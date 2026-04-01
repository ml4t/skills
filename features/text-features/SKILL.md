---
name: ml4t-text-features
description: "Extract features from financial text (filings, earnings calls, news) with timestamp-safe pipelines. Use when adding NLP signals to a trading model."
when_to_use: "Use when incorporating unstructured text into a quantitative pipeline"
dependencies: [lookahead-bias, point-in-time]
paths: ["**/*feature*.py", "**/*label*.py", "**/*barrier*.py", "**/*store*.py", "**/*horizon*.py", "**/*meta_label*.py", "**/*microstructure*.py", "**/*regime*.py", "**/*selection*.py"]
metadata:
  book_chapters: "10"
  library: ""
---
# Text Feature Engineering

Using a 2024-trained language model to score 2022 earnings calls leaks future information. Every text feature needs the same point-in-time discipline as fundamental data — plus model-vintage controls.

## The Problem

Text features introduce three leakage channels beyond standard PIT concerns:

1. **Model vintage leakage** — a FinBERT checkpoint trained on 2024 financial text encodes patterns from events after your backtest start.
2. **Availability vs publication** — an earnings call transcript published Jan 15 may not appear in your vendor feed until Jan 17. Using publication date instead of availability date inflates signal.
3. **Corpus-level leakage** — fitting TF-IDF or topic models on the full document corpus (including future documents) leaks vocabulary statistics into past predictions.

## The Pattern

### WRONG
```python
from transformers import pipeline

# Global model trained on ALL financial text through 2024
classifier = pipeline("sentiment-analysis", model="ProsusAI/finbert")

# Score a 2021 earnings call with 2024 knowledge
score = classifier(transcript_2021_q3)[0]
features["sentiment"] = score["score"]  # Look-ahead via model vintage
```

### CORRECT
```python
from sklearn.feature_extraction.text import TfidfVectorizer
import polars as pl

# Walk-forward TF-IDF: fit only on documents available before each date
def walk_forward_tfidf(docs_df: pl.DataFrame, max_features: int = 500):
    """Fit TF-IDF only on past documents at each prediction date."""
    results = []
    for date in docs_df["prediction_date"].unique().sort():
        past = docs_df.filter(pl.col("availability_date") < date)
        current = docs_df.filter(pl.col("prediction_date") == date)
        if len(past) < 50:
            continue
        tfidf = TfidfVectorizer(max_features=max_features)
        tfidf.fit(past["text"].to_list())  # fit on PAST only
        vecs = tfidf.transform(current["text"].to_list())
        results.append((date, vecs))
    return results
```

## Representation Ladder

| Method | Pros | Cons | PIT Risk |
|--------|------|------|----------|
| Loughran-McDonald dict | Deterministic, no training | Fixed vocabulary, ignores context | Low |
| TF-IDF / BM25 | Fast, interpretable | Bag-of-words, no semantics | Medium (corpus fit) |
| Static embeddings (Word2Vec) | Captures similarity | One vector per word (polysemy) | Medium (training corpus) |
| FinBERT / Transformer | Context-aware, high quality | Model vintage leaks, expensive | **High** |

Start with dictionary-based sentiment for baseline; add learned representations only if IC justifies the complexity.

## Guardrails

- **Model vintage**: checkpoint training cutoff must predate backtest start
- **Availability date**: join text features on vendor processing date, not publication date
- **Corpus-level transforms**: TF-IDF, LDA, and PCA on text must be fit walk-forward
- **Polysemy trap**: "margin" (operating vs margin call), "guidance" (earnings vs regulatory) — dictionary methods miss this
- **Coverage bias**: heavily-covered stocks get more text signal — control for attention asymmetry

## Production Implementation

No ml4t-* library covers text features. Use standard tools with PIT discipline:

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import AutoTokenizer, AutoModel

# For pre-trained embeddings, pin a specific checkpoint with known cutoff
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert", revision="v1.0")
model = AutoModel.from_pretrained("ProsusAI/finbert", revision="v1.0")
# Document: this checkpoint was trained on data through 2020-Q4
```

## Checklist

- [ ] Text joined on availability date, not publication date
- [ ] Pre-trained model checkpoint predates backtest start
- [ ] Corpus-level transforms (TF-IDF, topic models) fit walk-forward
- [ ] Dictionary baseline established before adding learned features
- [ ] Coverage bias controlled for (text density varies by market cap)
