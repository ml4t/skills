# Security Policy

## What this repository ships

Markdown. Every skill is a `SKILL.md` file with no executable scripts, no
hooks, no MCP servers, and no network calls. The only code that runs on your
machine is `scripts/install.sh`, which you invoke deliberately, and the
maintenance scripts under `scripts/` and `.github/scripts/`.

That is the point: an [empirical study of 31,132 public
skills](https://arxiv.org/abs/2601.10338) found 26.1% contained at least one
vulnerability, and skills shipping executable scripts were 2.12 times more
likely to be among them. Reading a skill before installing it is a reasonable
habit, and here reading it is the whole audit.

## What counts as a vulnerability here

- A skill whose guidance would lead an agent that follows it to do something
  unsafe: exfiltrate credentials, execute untrusted input, disable a control,
  or take an irreversible action without confirmation.
- Prompt-injection content embedded in a skill, whether deliberate or carried
  in from a source.
- A flaw in `scripts/install.sh` that writes outside the target directory or
  overwrites something it did not create.
- A flaw in the GitHub Actions workflows that would let repository contents or
  a token be influenced by an untrusted input.

Trading losses are not a vulnerability. These skills teach method; they make no
promise about the profitability of any strategy, and a correct method can still
lose money.

## Reporting

Report privately through GitHub's **Report a vulnerability** button under the
repository's Security tab, or by email to <pm@ml4trading.io>.

Please include the file, what an agent following it would do, and how you
established that. A working demonstration is welcome; a step-by-step recipe for
attacking a third party is not.

You can expect an acknowledgement within a week. Fixes land on `main` and are
noted in the release that follows. There is no bounty.

## Supported versions

The tip of `main` is the supported version. Tagged releases are snapshots and
do not receive backported fixes.
