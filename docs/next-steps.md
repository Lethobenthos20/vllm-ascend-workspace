# Next steps

Updated 2026-09-29. Follow the [nine design principles](design-principles.md),
[architecture](architecture.md) and [lifecycle contract](harness-boundary-and-lifecycle.md).
[Implementation status](implementation-status.md) separates completed evidence
from work in progress. Earlier release reports retain their historical results.

The [Codex public-transcript acceptance](codex-public-transcript-acceptance-2026-09-29.md)
records the implemented Windows/WSL work, exact candidate commits and remaining
limits. Preserve the following existing mechanisms:

1. Keep submitted knowledge authoritative on the remote. Retain only unsent
   additions locally, apply them to the current own PR or merged main, and never
   resurrect a Bot-redacted passage or withdrawn entry from an old full draft.
   Distinguish locally staged material from confirmed remote delivery.
2. Recover transient publication, feed and plugin-update failures through existing
   background workers and schedules. Persist backoff and reconcile unknown writes
   before retrying. Do not require a CLI, another business turn, or another model
   call. Content rejection remains separate from a recoverable network failure.
   Stable adapter management commands must select the installed generation.
3. Let long tasks and growing knowledge continue. Remove cumulative-body and
   whole-corpus rejection thresholds while bounding individual operations and
   using incremental processing. Do not introduce user-managed batches,
   compulsory draft administration or a new scheduling service.

Codex body processing now uses deterministic public-message selection and local
redaction. Do not reintroduce a model into body capture or increase its timeout
to handle larger transcripts. Optional title/summary generation selects its model
and effort separately; GPT-6-Luna/low has completed real metadata calls in both
PowerShell and WSL. Unsupported or failed calls retain labeled source excerpts.
Real native business tasks use gpt-6-luna/max.

Review and merge the recorded core and Codex candidates before checking ordinary
main-branch update delivery. The isolated candidate profile deliberately uses a
manual update schedule, so it does not establish current Windows/WSL OS scheduler
delivery. Keep native Hook trust, automatic contribution and feed synchronization
as separately observed boundaries. A historical trusted Hook does not prove a
changed Hook is trusted.

Kimi native model acceptance is deferred; Grok has no adapter in this scope.
Other harnesses need their own transcript projection and native evidence.
Earlier macOS and Claude results retain their original scope. Old business Skills,
profiling analysis, automatic Skill extraction and additional domains remain deferred.
