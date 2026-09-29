# MindIE Agent

Domain context, remote execution tools, and a knowledge/experience/usefulness feedback loop for Ascend development.

Use the [Codex](https://github.com/mindie-agent/mindie-agent-codex), [Kimi Code](https://github.com/mindie-agent/mindie-agent-kimi), or [Claude Code](https://github.com/mindie-agent/mindie-agent-cc) adapter in your own business repository.
Knowledge and authorized contribution processing run locally; remote-dev provides remote execution. Codex selects and redacts public transcript messages without a body model. A separate non-thinking model may generate only the title and retrieval summary. Collection is off until explicitly enabled.

This repository contains [architecture](docs/architecture.md), [design principles](docs/design-principles.md)
and [next steps](docs/next-steps.md). Component ownership and current evidence are listed in the [Chinese README](README.md).

The former workspace bootstrap, updater, source management, client wiring and automatically exposed Skills
have been removed. No legacy aliases or installation path are provided. Git history retains prior work.
The current rewrite is merged into the independent Codex, Kimi and Claude Code repositories' main branches. Read the
[unified implementation status](docs/implementation-status.md) for development and native acceptance separately.
The [2026-09-29 Codex acceptance](docs/codex-public-transcript-acceptance-2026-09-29.md) records
Windows PowerShell and WSL NPU runs, native Stop, redacted publication and retrieval against exact
candidate revisions. It identifies manual interventions and unverified boundaries separately.
Kimi model acceptance is deferred; Grok is not an adapter under test. Merge is distinct from release
acceptance. Old business Skills and profiling remain deferred.
