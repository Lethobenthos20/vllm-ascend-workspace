# Incremental index worker and direct-cutover review

Date: 2026-10-04. Scope: the LangMem worker/outcome ledger, deletion of the legacy organizer path, Engine/CLI lifecycle changes, Codex runtime acceptance probe, and affected mechanism tests. This review is tied to the source hashes below. The parent task still owns review and acceptance of the complete integrated product and its external deployment.

Principles re-read from the current primary workspace: `docs/design-principles.md`, HEAD `c666e597c8690f7f7c141e0c04ae29e9a0484de7` plus the current uncommitted principle 9 and development-review expansions. File SHA-256 `15b4b58385846051464c27d06922ad0353bdd6a4031b619ff248c3a65c179741`, Git blob `9b21e6ae87ac96ff8bdacc3f4f546384e111a184`. The previous `bbe8...` hash is not the reviewed current text.

Reviewed current commits: knowledge `0fa011701f4d73f40709df56c969cc3492eb8fab`; Codex `78d9cffcf207a9ac7ab862f6b158906210693d52`. Codex is a local commit only; this agent did not push it or create a PR. The exact knowledge commit is installed in the shared test venv, alongside remote-dev `3c1a3543322a6d3a954715642a679336b0c5f830`. Earlier full-suite and targeted evidence retains its original revision below; neither suite was rerun for this final pin refresh.

## Resulting boundaries

- LangMem 0.0.30 `summarize_messages` processes admitted complete blocks with the previous short navigation. Every new block participates; no head/tail omission, old-body resummarization or final whole-history merge is maintained.
- Complete source blocks are at most 16 KiB, a batch at most eight blocks, and the exact serialized user prompt at most 64 KiB. Native system/context tokens are additional and included in actual usage. The prompt cap is not a hard total-token or money cap.
- Python validates exact ordered block IDs and complete metadata. The native JSON schema constrains the array to the admitted block count; invalid output still retains known usage before explicit retry. Failure labels distinguish count/identity/schema, native rejection/deadline, and local scanner/application stages without exposing source-bearing exceptions.
- The native adapter uses explicit `gpt-5.6-luna` / `low` based on the parent's account probe. There is one permitted native invocation, no provider SDK, configured fallback or model retry. `--identity` binds actual prompt/schema/model/effort/limits and executing source hashes without a model call.
- Worker process success means delivery of a strict `returned`, `failed` or `outcome_unknown` envelope. It does not itself mean indexing succeeded. Missing token usage remains unknown; known unsupported-model rejection remains rejected. `model_calls` counts native invocations, not independently observed provider-internal requests.
- SummaryLedger shares the existing state-v4 transaction, stores no input body, and retains returned raw metadata only until deterministic local application. Interrupted `invoking` becomes `outcome_unknown`. Local recovery scans/applies already-returned output even when the current worker executable is missing; failed/uncertain native outcomes do not automatically invoke again.
- Engine/CLI support only public-transcript capture. The old body organizer, paid gap retry, saved organizer application, summary-only fallback and remote restoration branch are deleted. `agent_command` and `organize` fail explicitly. Current feed packages supply the append base through the delivery component.
- Setup/updater import the actual ReMe and LangMem dependencies and validate the summary ledger, worker bounds, admission, adapter, and service APIs. The obsolete SQLite FTS5 contentless-delete gate is removed because retrieval now uses ReMe. The unchanged updater handshake key `maintenance_budget=1` still denotes the present rolling-budget capability; the new probe does not require the deleted MaintenanceBudget class or create a compatibility branch. An old installed updater still carries its old probe, so first deployment must use the reviewed new updater/setup entry; preserving the handshake alone does not establish upgrade acceptance.

## All nine principles

1. **Total user cost.** Complete incremental batches remove repeatedly processed raw history and sampled middle omissions. Returned-response recovery avoids repeated paid work. Deleting about 1,200 lines of the former processing path removes duplicate scheduling/recovery semantics. Test/runtime probes no longer reject a valid ReMe install for an unused FTS feature. The final core removes the inherited unconditional ReMe refresh from service startup/outbox work and splits UTF-8 input with one initial encoding plus byte offsets, avoiding repeated encoding of the entire remaining body. Framework dependency cost and actual model semantic quality remain explicit acceptance questions.
2. **Closed mechanical problem.** Partitioning, admission, schema/ID validation, bounded native execution and durable outcomes have defined inputs and failure states. They do not certify truth, infer broad sharing rights or decide that a business task succeeded.
3. **Understanding burden.** Users work with task material, search and visible failures. Framework IDs, queue receipts and policy identities stay internal. Existing configuration errors name the required replacement; no extra approval or user-maintained model provider setup is added.
4. **Component boundary.** This worker generates block indexes and navigation only. Markdown bodies remain the material authority. Capture, ReMe retrieval, publication and native adaptation retain distinct responsibilities. The ledger owns call outcomes without creating a second body database or framework service.
5. **Informational Skills.** The final Codex Skill diff removes the obsolete promised paid recovery, describes saved-response local recovery and explicit retry, and corrects expired/withdrawn reference behavior. It adds no mandatory lookup, research route, vote or closing checklist. Product documentation and the generated knowledge-explain description now match that reference boundary.
6. **Reference knowledge.** Prompts preserve failed attempts, uncertainty, later correction, attribution and synthetic status. Metadata cannot replace source bodies or certify an outcome. Reconstructed tests and static validation are not represented as real model-quality evidence.
7. **On-demand behavior.** Only authorized new material enters paid indexing. Duplicate Stops cannot duplicate the body/call. Returning from a business task does not trigger a whole-history merge. Passive consumer retrieval and sync do not invoke this worker. An empty summary queue performs only its existing bounded wait.
8. **Reuse.** The change uses the selected LangMem function, existing native authentication/process ownership, SQLite transaction, admission, cursor CAS and deterministic IO continuation. It does not instantiate LangGraph, BaseStore, a provider client or another external service. Valid mechanism tests were migrated; pure retired-organizer fixtures were removed. Fixed dependency/source checks are retained for final installed acceptance rather than weakened for editable development.
9. **Visible errors and actual effects.** Required indexing failure remains failed, not a publishable excerpt. Known usage survives invalid output and later cleanup failure; missing usage is not zero. A returned response is durably saved before local scan/application; rollback and recovery retain it without another model call. Unknown external outcome is not retryable first use. Shutdown retains local returned work, while authority revocation cancels it. The final lifecycle fix always starts the required queue worker so missing configuration settles due material as failed; it no longer silently leaves pending work to block idle shutdown forever. Setup rejects failed processes even if stdout printed OK. The updater now recognizes a core partial-promotion result, preserves metadata_committed/failed_stage and all original rows, and reports degraded. A synced/unchanged result with cleanup failure retains its completed sync status but reports degraded with visible cleanup failure; a primary error and cleanup error are both retained. No extra sync, model invocation or external write is introduced by this pure result fold.

## Findings resolved and validation

The current principle-9 review covers the actual result and side effect of each changed exception boundary: unsupported model/start/deadline/output failures, malformed or incomplete block metadata, scanner and authority failures after model return, local apply rollback, shutdown, cleanup failure and restart uncertainty. Controlled tests preserve original body/receipt/counters and prevent automatic native replay. A suspected cross-process claim-loser issue was investigated by the delivery agent and was not reproduced as a defect; it is not an open finding. The actual interrupted-call and shutdown classifications were corrected and tested.

Mechanism evidence before final package installation:

| Check | Result |
|---|---|
| Worker result reasons + ledger/budget/returned recovery | 19 passed; `/tmp/organizer-error-reasons-knowledge.log` |
| Native worker outcome/category tests | 16 passed; `/tmp/organizer-error-reasons-codex.log` |
| Eight retained lifecycle/redaction/process suites after cutover | 64 passed in 19.33 s; `/tmp/organizer-shrink-tests-final.log` |
| Missing worker real queue + service startup boundaries | 14 passed in 14.44 s; `/tmp/organizer-missing-worker-lifecycle.log` |
| Updated full-package export and scoped status fixtures | 2 passed in 5.736 s; `/tmp/organizer-codex-fixtures-targeted.log` |

The initial full Codex run exposed obsolete test engine configs, a stale discovery catalog after the remote-dev pin change, an old summary-only test protocol, and required-field omissions. Those fixtures now use production public-transcript configuration, the complete-block outcome protocol and canonical package validation. Teardown errors no longer leave process-global test environment patches installed. The second full run exposed the missing-worker lifecycle defect above; it was fixed in product code rather than masked by longer teardown waits. The third complete run had only the expected editable-install exact-pin failure (303 tests, 1 failure, 12 platform skips). The exact core revision was then installed with `uv pip install --no-deps`; preflight confirmed the core/Kimi fixtures and core/remote-dev package commits, and `uv pip check` confirmed all 164 installed distributions. The exact installed CI-entry run then passed: **303 tests in 110.308 seconds, OK with 12 platform-specific skips**, using `PYTHONUTF8=0` and `LANGSMITH_TRACING=false`; full log `/tmp/organizer-codex-exact-ci.log`. This complete run was at core `9dba4d46dda5b798dd27fdf207262c3ad98f7339`, before the later pure feed-result fold fix and final core platform fixes. The final revision uses the targeted results below; a full 303-case rerun was deliberately not repeated. Remote platform CI remains a separate acceptance boundary owned by the parent.

Seven processes from the failed local fixture runs were terminated only after confirming the exact test venv command, known PID and deleted temporary config path. Subsequent inspection showed no remaining service from those test fixtures. No actual user service or native history was touched.

New K3-derived tests use only the anonymous dimensions supplied by the parent (initial adaptation, middle correction, repeated progress/pending outcome, continuation). Source text is reconstructed. The volume test checks all 283,102 synthetic public bytes reach complete batches. All actual K3 history reading and native quality assessment remain with the parent. No private transcript was read or copied by this agent.

Remaining limits: native CLI total provider input/output tokens are not hard-capped beyond prompt/schema/output-byte/deadline limits, and rolling budget reservation is an estimate. A completed local suite is not native Hook acceptance, GitHub publication, full K3 semantic quality or Windows acceptance. Upstream trustcall deprecation and portable-fixture tar extraction warnings remain visible.

## Final affected-change verification

At the preceding core `f72445403fe9069f0abaa224306943e7de608500` and Codex `c865f2fd1aa3e84333704977cdb46a69c38d76f8`, the core was reinstalled with `uv pip install --no-deps`. Preflight confirmed both fixture revisions and the exact installed core/remote-dev commits; `uv pip check` confirmed 164 compatible distributions; `git diff --check` passed. That targeted command ran service handoff, real cold-entry lifetime, feed result folding/persistence, caller-visible failures, and the installed-runtime exact-commit test: **26 tests passed in 14.777 seconds**, `/tmp/organizer-codex-final-targeted.log`. This is retained evidence at the preceding pair, not a new run at `ec5f33e` / `ee8c80a`.

The independent feed fold/failure-visibility check passed **22 tests in 0.035 seconds**, `/tmp/organizer-feed-outcome-fold.log`. It covers partial metadata commit, synced and unchanged cleanup failures, simultaneous primary/cleanup failure, preservation through the updater plugin check and state file, and nonzero caller status for degraded knowledge. The fold is a bounded pure parse/aggregate operation: it does not rerun the sync or mutate the original row. Principles 1–4 and 7–9 therefore retain the same component and cost boundaries while fixing the missing error semantics; principles 5–6 remain satisfied by the already-reviewed informational Skill and fallible-reference treatment.

Reviewed preceding core delta: removing the old outbox index tick does not make retrieval optional—`MaterialStore.search` still constructs/refreshes ReMe on an explicit query and propagates errors. Byte-offset splitting advances only by the bytes of valid decoded text and preserves the earlier complete-block boundaries. These changes reduce startup/repeated-encoding cost without changing original-body authority or masking a missing required stage.

## Canonical checkout pin refresh

Codex `ee8c80a0855b6c0ba6ccbce8a62d5ee4cb84b976` changes only the four core commit references in runtime requirements, CI checkout, preflight and the cross-adapter installed-runtime assertion to knowledge `ec5f33e9d6a329c0fb48cea67cba66113e70a5b9`. The reviewed core delta scopes LF checkout/staging settings to the private publication clone, reconstructs that clone from the proven remote revision, propagates checkout failures, and distinguishes `git diff --cached` exit 1 (a change) from timeout or other errors. It does not change the user's Git settings or reset a business checkout.

Affected-principles review: **1** avoids false maintainer-conflict and repeated publication debugging caused by host line endings; **2** handles the closed Git-byte and exit-status contract; **3** adds no user configuration or recovery state; **4** remains inside private publication Git operations; **5** does not change Skill behavior; **6** retains source material as fallible reference without strengthening evidence claims; **7** adds no model call, background refresh or activation; **8** reuses prior full and lifecycle evidence and checks only the exact new installed dependency contract; **9** surfaces failed checkout/diff stages before commit or publication instead of treating them as an absent branch or a normal change. All nine retain their previously reviewed boundaries; no new violation was found in this scoped pin diff and its reviewed affected core behavior.

Actual refresh validation: `uv pip install --no-deps` installed the exact new Git commit. Preflight confirmed the core and Kimi checkouts plus installed core and remote-dev commits. `tests.test_parallel_codex_contract.CrossAdapterTests.test_running_runtime_matches_the_declared_core` passed **1 test in 2.821 seconds**, log `/tmp/organizer-codex-ec5f-exact-runtime.log`; `git diff --check` passed. The earlier **303** and **26** test suites were not rerun, and their timestamps/revisions above remain the evidence boundary. Native acceptance, deployment, Windows CI and publication remain separate parent-owned checks.

## Final material-byte integrity pin

Codex `78d9cffcf207a9ac7ab862f6b158906210693d52` changes the same four core references to knowledge `0fa011701f4d73f40709df56c969cc3492eb8fab`. The final core correction reads authoritative manifests and blocks as original bytes with strict UTF-8 decoding before validation, export or immutable-content comparison. ReMe validates those authoritative bytes before its own derived-text normalization. CRLF corruption therefore reaches the canonical validation failure instead of being hidden by Python universal-newline conversion. This adds no model call, second authority store or compatibility path.

The affected principles were rechecked against this core delta and the four-reference Codex diff. **1–4:** exact-byte validation removes false integrity acceptance using the existing parsing boundary, with no added user workflow or component responsibility. **5–7:** Skill guidance, fallible-reference semantics and activation/model behavior are unchanged. **8:** existing lifecycle/full-suite evidence is retained at its original commits; only the exact installed dependency boundary is rerun here. **9:** malformed authoritative content fails before derived indexing or export, rather than being normalized into a successful result. No additional issue was found in this bounded review.

Actual final validation: exact `uv pip install --no-deps` succeeded; preflight confirmed core/Kimi fixtures and installed core/remote-dev commits. The installed-runtime exact-commit test passed **1 test in 2.979 seconds**, `/tmp/organizer-codex-0fa0-exact-runtime.log`. The final Codex diff contains only four pin replacements and passes `git diff --check`. The prior 303-test, 26-test and ec5f one-test records above retain their original revisions; none is relabeled as a rerun at this final pair. This agent did not perform native inventory, a model call, plugin installation, default configuration/consent writes, deployment or publication during this pin refresh. The prepared synthetic native plan is still unexecuted.

## Reviewed final source hashes

```text
knowledge/mindie_knowledge/materials/reme_index.py 1179f74c5b47f99ff525f2dd56aa8b334cba94d483200bd30bc4646b4bca2136
knowledge/mindie_knowledge/materials/store.py db70cbb0901dffc2bfb2efc385843fa7eee35e305a2595757bfd6bc86ccea4d1
knowledge/mindie_knowledge/materials/summarizer.py 152c5d84910ce368735b4331a499347b27112e1a5ce97bba27dcc7cbeb580c08
knowledge/mindie_knowledge/materials/ingest.py f29916bc011eeaedc52ef6370d5051323732c1966adec05dbea4c25f4c0e3414
knowledge/mindie_knowledge/loop/engine.py 724a3a056928992104ff16136454369faddb5891bc827d9e9b0acc0d13a5d032
knowledge/mindie_knowledge/loop/cli.py a44cc45329b36aa3f89b0db9d3de74f2b03cacab02260ce9f305b54c1e3553bb
knowledge/mindie_knowledge/loop/budget.py 637028d60a15dd8eb31e83db1f63ad74fdd57e71378769de28317b158f6cc9e0
knowledge/mindie_knowledge/community/gitops.py 1e48e5a00dde779a8b211427b799028d50e8839bb6623caf9cb90b0d386c27b1
knowledge/tests/test_material_summarizer.py 26c69eae7288c44094401651ab4efbec56c78bb069938eb4fd31a03819a961f9
knowledge/tests/test_summary_budget.py 624bfda31cca3181d48875c688b3e750b1f605d4d966ad1dc2cffd00bb918337
knowledge/tests/test_summary_recovery.py fa6468b07b124a0bec968a3c98f68e012af71ca0318259360ea9e56bd159f79c
codex/.github/workflows/tests.yml e4d261788ada50ec7433f1d773ada4e9bb3aceff10b16d3afcfd32e94848a66c
codex/README.md 58abca31c637c991703ebc1d019921349b1b2920f1ec5bece4f52332d36d9ab7
codex/docs/history-import.md 601b73b5ca64fe9f99543b903693432c1de602da0ba3c797149009efa1bf26f5
codex/docs/native-business-acceptance.md b3e4c3f79aa599134244e21603c154ca9f65f26132e36aa514e3cb149e70e660
codex/docs/public-transcript.md 5dca3f164a48acb8118cb6c49ae0b09f39d6db3be32eb9b2388860cf8f967ffa
codex/plugins/mindie-agent/scripts/agent_worker.py 230f67237190adea7c8785034c250d7e94eeafc6dc2c002db0c8e17a90683bfa
codex/plugins/mindie-agent/scripts/auto_update.py ae0598f577d522ac9eedc3cb6585dba0c93fe9a33e44e3a089aeb1efbe50566c
codex/plugins/mindie-agent/scripts/export_catalog.py 56298a8234a1006da7fca0a0aa0420328d5968ff7fc9595b8e3b6a7ba496a9d7
codex/plugins/mindie-agent/scripts/history_import.py 635cbcb79758d9f18e9230172a7420ac8e9dffe5b69788d134cee4e234e9d89e
codex/plugins/mindie-agent/scripts/mcp_catalog.json f4e11c1c81d98e6965692496c37d7cc9aa550e4fe7b140b91f23f3e8de24ac6f
codex/plugins/mindie-agent/scripts/process_guard.py 4c9641243311698c04b12813d2124d2d436ad3833210e4bae338e6f1b635a346
codex/plugins/mindie-agent/scripts/runtime_probe.py 5c449763f315241aaf8a17dc008509b0e6d8e7c670db9fe11ca5912f29c61fc5
codex/plugins/mindie-agent/scripts/setup.py f5a2ff8ce3f04307296102e88010166baffc537f166d6bb44fce073c18901bd2
codex/plugins/mindie-agent/skills/mindie-agent/SKILL.md 72f2f967e010f950e6988ede9bbbb8a120c16db40585a872da03b0f8beeca58c
codex/runtime-requirements.txt da7abbedf0710b2613dd5cf5815837b8d24319eddb4df0510bc399175dd228b5
codex/tests/k3_material_fixture.py d0ca80d94de19aeecbba446c5f3d3a9ed32a9551d3a82bfaecb4d375d2f40f4e
codex/tests/preflight.py c5236e0feefa0c0c0393e21b9939167b308a8f52d6e4d29b562171452ca6ab27
codex/tests/process_fixtures.py 7218a9d30b5b084ce6ce6c7bbea41aa3556f17c962820fab9c824f24d64b7fdc
codex/tests/test_auto_update.py c786578a3bebcb816ce14abc42343f72fe4225b7fac6eda1badcff3e131ced34
codex/tests/test_entry_bounds.py a384991be5d3d7d906ade2d98722456d6063e30e2f764a09b455fce4572380c7
codex/tests/test_feed_sync.py 0b638b14f6fc3dafdd1088f7bc2357bb4c5f45f76ccc7797f62980716d63d9e1
codex/tests/test_history_import.py cdd0f4dbfaf3700ad6aa66a1b669be03e59df48bbcd8fd469f0e1d6408f7593b
codex/tests/test_organizer_categories.py 5a2502b5604423fbd838b3aea7a800880b53ba51cc1032e208c37207f90382e7
codex/tests/test_organizer_model.py a4d2af39b69bfc66b2b59ef07e450460e30ae226fe0a3189d53c76c8a6538f9f
codex/tests/test_parallel_codex_contract.py 882c4cf177c94ad729e11335735131759dad2e36e7372a89aea2959a12e35b5d
codex/tests/test_runtime_compatibility.py 30ede69a644c75855333e668175bfdce0fe33c9043255fae7fbf36324435f5ac
codex/tests/test_runtime_probe.py 6844fe99041c73494bb8f9080041d41096a985f0a580944707c43c933c8867b9
codex/tests/test_service_entry_lifetime.py 01830b66d8f5a78dc7c933617d769122cda213e20c278c3d388e1e8285941393
codex/tests/test_service_handoff.py b3814044db8c854a8a39ced535855b7bcc158248f2494b80da63c2b9f75a05cf
codex/tests/test_session_gate.py 7b0678235a15f18e607073a24fb2be271968434362f9d3542eb6b36e97d76d03
codex/tests/test_setup.py eb6d732a6208a2a545bb57f3676dd4e57340c0e813ef9ce24cc68fc9644a17b9
codex/tests/test_sharing.py 54f4d50bf67b2872120e3f5ee822900c4ee13b9c59867ffc062629bcff65419d
codex/tests/test_status_errors.py 83f485b0104b64802b82cac0fbb7bdb3e25296a211a5000ab95ae74ccd9b615c
```

Deleted obsolete fixture: `tests/test_fts_probe.py`; its process-failure honesty check remains in `tests/test_runtime_probe.py`.
