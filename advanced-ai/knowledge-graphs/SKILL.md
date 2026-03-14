---
name: ml4t-knowledge-graphs
description: Knowledge graphs for financial entity relationships and alternative data signals. Use when modeling supply chains, ownership structures, or event propagation across interconnected entities.
dependencies: []
metadata:
  book_chapters: "24"
  library: ""
---

# Knowledge Graphs for Finance

Flat tabular data treats each company as independent. In reality, a supplier's earnings miss propagates to its customers within hours. Knowledge graphs make these relationships queryable and tradeable.

## The Problem

When Foxconn reports production delays, Apple's stock drops before any Apple-specific news. A tabular model with Apple features alone cannot anticipate this. Supply chain links, ownership structures, and sector relationships form a graph that transmits information faster than fundamental analysis.

## The Pattern

Build a typed directed graph. Nodes: entities (companies, sectors, executives). Edges: typed relationships with economic weights. Generate features from graph topology and neighbor events.

### WRONG

```python
import polars as pl

df = pl.DataFrame({
    "symbol": ["AAPL", "FOXC", "TSM", "MSFT"],
    "sector": ["Tech", "Tech", "Tech", "Tech"],
    "earnings_surprise": [0.02, -0.05, 0.01, 0.03],
})
# Apple sees only its own features — no way to know Foxconn's miss matters
features = df.filter(pl.col("symbol") == "AAPL")
```

### CORRECT

```python
import networkx as nx

G = nx.DiGraph()
G.add_node("AAPL", type="company", sector="Tech")
G.add_node("FOXC", type="company", sector="Tech")
G.add_node("TSM", type="company", sector="Semicon")

G.add_edge("FOXC", "AAPL", relation="supplies", revenue_pct=0.35)
G.add_edge("TSM", "AAPL", relation="supplies", revenue_pct=0.25)

def supply_chain_exposure(G, symbol: str, events: dict[str, float]) -> float:
    """Weighted sentiment from direct suppliers."""
    exposure = 0.0
    for supplier in G.predecessors(symbol):
        edge = G.edges[supplier, symbol]
        if edge.get("relation") == "supplies" and supplier in events:
            exposure += events[supplier] * edge.get("revenue_pct", 0.1)
    return exposure

events = {"FOXC": -0.05, "TSM": 0.01}
apple_exposure = supply_chain_exposure(G, "AAPL", events)
# -0.05 * 0.35 + 0.01 * 0.25 = -0.015 (negative supply chain signal)
```

## Graph-Derived Features

```python
def graph_features(G, symbol: str, events: dict[str, float]) -> dict:
    suppliers = [n for n in G.predecessors(symbol)
                 if G.edges[n, symbol].get("relation") == "supplies"]
    return {
        "n_suppliers": len(suppliers),
        "supply_chain_sentiment": supply_chain_exposure(G, symbol, events),
        "pagerank": nx.pagerank(G).get(symbol, 0),
        "in_degree": G.in_degree(symbol),
    }
```

## Temporal Consistency

Financial graphs evolve: M&A changes ownership, earnings calls reveal suppliers, board members rotate. Every edge needs a `valid_from` timestamp. Features must be recomputed per timestamp from point-in-time graph snapshots. A supplier relationship discovered in a Q2 filing cannot exist in Q1 features.

## Guardrails

- **Timestamp every edge** — stale supply chain links from 2020 create false signals in 2024
- **Weight by economic significance** — unweighted edges treat a 1% supplier the same as 35%
- **Beware lookahead in graph construction** — edges cannot predate their disclosure
- **Graph features must be point-in-time** — recompute centrality at each timestamp, not once globally
- **Validate entity resolution** — match names across SEC EDGAR CIK, Bloomberg, and news sources

## Production Implementation

No ml4t library for knowledge graphs. Recommended stack:

- **Prototyping**: `networkx` for local graph operations
- **Production**: Neo4j or Amazon Neptune for scale
- **Edge sources**: SEC supply chain disclosures (Item 1), FactSet Revere, Bloomberg SPLC
- **GNN models**: PyTorch Geometric for graph neural network approaches

## Checklist

- [ ] Edges are typed (supplies, owns, board_member) not generic
- [ ] Edges carry weights reflecting economic significance
- [ ] Graph is timestamped — no future edges in historical features
- [ ] Features recomputed per timestamp (point-in-time snapshots)
- [ ] Supplier/customer exposure weighted by revenue percentage
- [ ] Entity resolution validated across data sources
