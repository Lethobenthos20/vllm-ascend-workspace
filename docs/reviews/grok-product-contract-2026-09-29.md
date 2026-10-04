# MindIE Agent 产品契约审查

审查对象是当前目录的固定快照，`manifest.json` 记录的提交为：

| 仓库 | 提交 |
| --- | --- |
| core `knowledge` | `e099a80fd99a6d895579b5d016aecf2a96851559` |
| codex `mindie-agent-codex` | `6f43baf926c4ae9b4fcf8b5a6ce2022bf0437a81` |
| kimi `mindie-agent-kimi` | `bce2ac0481df1e11041310b272017ee15ef8edbb` |
| cc `mindie-agent-cc` | `5065d53f8578bd827433aaf3c3c5851759126540` |
| product `mindie-agent` | `b03bb43b46c76e328cbd997944fb087bf1e46d91` |
| remote-dev `audit-remote-dev` | `28213bf3065e173216794c43ad021ef169e6a8c9` |
| diagnostics `audit-diagnostics` | `7c56f6b510b48fa60f256b46f71805e3be61eed8` |

本轮在 Linux 上用临时脚本直接调用快照源码复现，没有修改产品源码，没有跑整套数百项，没有下载 Gitleaks，也没有安装到生产环境。用户提供的 Windows 通过数不作为正确性证据。证据分为三类：已复现、静态推断、缺少证据。

产品源码未改。下面只列会改变授权边界、丢掉正文或让失败无法自动恢复的问题。

## 可行动的问题

### 1. 同意文件尚未允许贡献时，每次相同写入都新开授权边界

- 严重程度：高
- 证据：换代行为已复现。三个适配器“先写设置、后记选择”的顺序是静态核对。换代之后取消旧批次、排除旧草稿、前移采集边界，由对应函数的 `generation` / `enabled_at` 条件静态推出，本轮没有再跑完整 outbox 集成。
- 位置：`core/mindie_knowledge/loop/settings.py:437-443`。读取侧已经把故障和明确关闭分开：`settings.py:267-282` 的 `capture_block_kind()`。写入侧没有使用这个区分。
- 触发：文档已经 `enabled`，并且已经带有 `consent_config`，但同意文件缺失、不可读、损坏、没有 choice，或 choice 还不是 `contribute`。此后任何一次策略相同的 `transition()` 都把 `changed` 置真，新造 16 字节 `generation`，并改写 `enabled_at`。调用方传入的 generation 会被丢掉。
- 适配器怎样踩中：Codex `sharing.py:546-560` 只有“开关和 choice 都已经是目标值”才直接返回；设置写在社区锁内，`record_choice` 在锁外。CC `entry.py:501-508` 先 `write_enabled`，再由 `_finish_contribution`（`entry.py:465`）记录 contribute。Kimi `entry.py:470-478` 同样先 `write_enabled` 再 `record_choice`。设置已开启、选择尚未落盘时崩溃或重试，下一次相同 enable 会换代。Codex `sharing.py:58-68`、CC/Kimi 的 `community_config` 都进入同一个 `transition()`。
- 影响：`store.py:2003-2013` 把其他 generation 的 pending outbox 标成 `disabled`（`settings generation changed before send`）。`store.py:1222-1256` 的 `drafts_changed(generation=...)` 只导出当前 generation 的授权草稿。`engine.py:219-223` 的采集边界是 `max(enabled_at, activated_at, capture_floor)`，新的 `enabled_at` 会跳过更早的公开 transcript。已经发出的材料保留。用户真正关闭后再开启，仍然应该换代。
- 最小复现：同意为 contribute 且策略不变时，两次写入的 generation 都是 `4274d860b8295c663b0786c5d1cd2dd2`，`enabled_at` 不变。同意缺失时，同一策略连续写三次得到 `4274d860…` → `ec5056de…` → `9514ef15…`，`enabled_at` 两次都变。损坏、choice=`disabled`、有文件但没有 choice，结果相同。调用方传入 32 个 `a`/`b` 组成的 generation，落盘值仍是存储侧自己的 generation。
- 应修的共同根因：`transition()` 把“当前不能贡献”当成“用户改变了边界”。只有用户明确关闭，或 repository、branch、visibility、account、fork、project_roots 真正变化，才允许新 generation 和新 `enabled_at`。同意缺失、损坏或尚未写入时只挡住采集，不换代。`record_choice` 与 enable 放进同一次 `CommunityWriteContext`。明确的 disabled 再变为 contribute 仍是一次新边界，不能在 choice 保持非 contribute 的每次重试上再造一次。

读取侧测试 `core/tests/test_consent_fault_recovery.py:192-233` 要求损坏同意文件期间 generation 不变、已收工作保留。它只破坏文件再读取，不经过 `transition()`，所以这条写入缺陷仍然是绿的。

### 2. Stop 要等完整 JSON，未写完的对象会丢掉已经出现的 transcript 路径

- 严重程度：高
- 证据：三个 reader 的超时和空返回已复现。`stop()` / `_hook` 随后打印 `{}`、不调用采集，是根据已复现的返回值对照源码作出的静态推断；完整 `stop()` 会碰共享配置，本轮没有跑。Windows 冷导入是否吃掉预算，缺少证据。
- 位置：
  - Codex `bridge.py:29` 在导入项目模块之前开始计时；`bridge.py:74-75` 预算 1.5 秒，Windows 1.3 秒；`bridge.py:86-131` 只有 `json.loads` 成功才结束读取，超时抛 `TimeoutError`；`bridge.py:504-507` 捕获后打印 `{}` 并返回。
  - CC `mindie_launch.py:89`、`318-363`：同样等完整 JSON，超时返回 `b""`。`bridge.py:191` 再把剩余时间收成 `budget_seconds=0.8`。Kimi `mindie_launch.py:89`、`321`、`343`、`354` 是同一读法。
  - 宿主超时是进程期限：Codex `hooks.json` 为 5 秒；CC 与打包后的 Kimi Stop 为 `mindie_launch.py hook stop`，超时 2 秒。Kimi 源码 `kimi.plugin.json` 仍写 `with_runtime.py bridge.py stop`，`updater.py:344-348` 在打包时改写成 launcher hook。这些期限本身成立，不能改成正文大小上限。
- 触发：stdin 里 `transcript_path` 已经写完，但后面的 `last_assistant_message` 还没让整个对象闭合，读预算先到。本机慢速滴入在 0.35 秒预算、已写入 10240/300160 字节时：Codex 抛 `TimeoutError: hook stdin deadline exceeded`；CC 与 Kimi launcher 返回空字节。把 `json.loads` 人为拖过等待时间时，一个已经完整的 162 字节对象也会被丢掉，因为 `finished` 要等 `loads` 返回。真实触发是对象未写完。
- 影响：Hook 结束时没有采集。游标不动，这条 Stop 的公开正文不会入库。快速本地管道不受影响：2 MiB 完整 JSON 在 0.005 秒内读完，所以 `timeout=5` 的 10 MiB Stop 测试可以保持绿色。本机导入 Codex bridge 耗时 0.107 秒；Windows 冷启动是否把 1.3 秒预算耗尽，缺少证据。reader 注释写明 Windows 路径只做了代码检查。
- 附带静态推断：Codex `admission_ops.py:180-185` 在已经很紧的 Hook 预算里再用 `max_seconds=1.0` 探测 transcript，只为拒绝 `session_match is False`。这不是正文截断，但会占用 Stop 时间。本轮没有执行这条探测。
- 应修的共同根因：reader 把“整个原生对象闭合”当成可以转发的条件，产品只需要身份和 `transcript_path`。读到路径后就转发，或只读有界前缀并抽出路径；不要为了 `last_assistant_message` 把预算用完。1.3/1.5/2/5 秒仍是进程期限，不要提高成正文业务上限。

同一类静默丢弃还存在于不在三端实链上的核心 CLI。`cli.py:471-479` 最多读 `128*1024+1` 字节，更大就打印 `{}`、退出码 0，且不调用 `capture_hook`。已复现：130 KiB 输入 `capture_called=false`；小输入 `capture_called=true`。严重程度低，因为当前三个 Stop 桥不走这条 stdin。

### 3. 扫描器暂时失败后，同一条通知不会自动恢复

- 严重程度：高
- 证据：已复现。扫描器是临时假脚本，没有下载或运行 Gitleaks。
- 位置：`transcript_redaction.py:90-142`。只有 `OSError` 和 `TimeoutExpired` 变成 `ScannerUnavailable`。非零退出码和无法解析的 span 变成 `ValueError`。`engine.py:1438-1450` 只对 public-transcript 的 `OSError` 做 `defer_capture`，原因写成 `public-io:N:...`。其他异常落到 `engine.py:1470` 的 `mark_capture(..., "failed")`。`engine.py:1257-1258` 不再处理 `failed`。
- 触发：扫描器退出码非 0，或 stdout 不是合法 span JSON。文件暂时不存在则走另一条路。
- 影响：非零退出和 `not-json` 都使该 capture 成为 `failed`，游标保持 null，草稿为 0。换上可以正常返回 `[]` 的扫描器后，再处理同一 id 仍然是 `failed`。缺少绝对路径的扫描器会停在 `pending`，detail 为 `public-io:1:ScannerUnavailable`，这是会退避重试的路径；第一次退避约 2 秒，所以刚失败时 `due_capture` 还看不到它。好的扫描器把同一输入收成 `organized`，`body_model_calls` 为 0。若扫描器稳定输出坏 span，后续新 Stop 也会失败。会话最后一条 Stop 会卡在这条失败上。
- 应修的共同根因：暂时的扫描器故障（非零退出、超时、报告不可读）应与 `ScannerUnavailable` 一样，对同一 capture id `defer_capture`，游标不动，扫描器恢复后自动重放。只有内容本身被确定性拒绝时才永久失败。

### 4. 一条完整的坏 JSONL 停住该 transcript 后面的公开消息

- 严重程度：高
- 证据：已复现。使用快照里的 CC 正式解析器，经 Engine、Store、Admission 和正常扫描器。
- 位置：解析器 `cc/scripts/transcript.py:318-320` 遇到完整但非法的记录就返回 `invalid-record`，`end` 停在上一条好记录，页文本里仍可能含有坏行之前的公开文字。`engine.py:728-732` 看到该状态后把整次 capture 标为 `failed`，detail 为 `public transcript invalid-record; cursor unchanged`，不提交这一页。`engine.py:1257-1258` 不再处理该 id。
- 触发：transcript 中出现一行已经换行、但不是对象的 JSONL；后面还有合法公开消息。半行（没有换行）不触发这个问题。
- 影响：第一次和第二次 Stop 都是 `failed`，游标 null，草稿 0。坏行前的 `BEFORE-BAD` 和坏行后的 `AFTER-BAD` 都没有入库。游标不前移，下一次通知仍从同一位置读到坏行。坏行留在文件里时，该任务后续公开消息不会保存。产品约定是单条材料失败不拖停无关任务（`product/docs/harness-boundary-and-lifecycle.md:81`）；这里同一 transcript 的后续正文被拖停。
- 半行对照：没有换行的尾部使解析器 `partial=true` 且 `end` 停在完整记录之后；`engine.py:624-626` 在 `end==start` 时推迟。这是正确行为。
- 应修的共同根因：坏的完整记录被当成整页失败，而且失败 id 不再重试、游标也不越过坏记录。应先提交坏行之前已经解析出的公开正文，把坏记录隔离成诊断，再从它之后继续。对同一坏行反复重试不能代替越过它。

### 5. Kimi 在锁外合并项目根，后写入覆盖先写入并换代

- 严重程度：中
- 证据：已复现。按 `_enable_contribution` 的实际顺序做了确定性交错，不是碰运气的线程赛跑。
- 位置：`kimi/scripts/entry.py:418-447`。`load()` 在锁外取已有根，再把拼出来的列表交给 `sharing.py:60-84` 的 `write_enabled`。`CommunityWriteContext.write`（`settings.py:517-557`）用调用方给出的 `project_roots` 替换文档里的列表；根集合变化在 `settings.py:434-436` 被当成策略变化。
- 触发：两个 Kimi 客户端都先读到旧范围，然后各自发布。一方加入的根只存在于它自己的快照里。
- 影响：本轮交错后磁盘上只剩 `/tmp/mindie-roots-hi75e5tb/a`，`b` 被丢掉，generation 为 `2ade60b46ea00c5b7397a92385cb706c`。顺序调用也一样：先写 `[proj, other]` 再写只有 `[proj]` 的快照，`other` 消失，generation 从 `e44257da…` 变为 `ec3a4961…`。丢掉的根不再属于授权范围，同时产生问题 1 所述的新边界。
- 应修的共同根因：范围合并要在社区写锁内重读当前文档再加根。用户明确点名的根增删仍是范围变化。CC 的 `sharing-enable` 要求命令带 `--project-root`，并用点名的列表替换存储列表，这是一次明确范围变更，不要改成静默合并。

### 6. Kimi 分叉会话暂时读不到 state.json 时，父任务历史进入正文

- 严重程度：中
- 证据：已复现。路径布局是对的：主 wire 在 `<session>/agents/main/wire.jsonl`，`parents[2]/state.json` 就是会话状态。
- 位置：`kimi/scripts/transcript.py:188-203`。`OSError`、JSON 损坏或层级不够时返回 `None`，等于没有分叉边界。`forkedFrom` 存在但没有 `createdAt` 时抛出 `ValueError`，解析器变成 `unknown-format`。
- 触发：子 wire 里复制了父会话文字，而 `state.json` 暂时不存在或不可读。
- 影响：`state.json` 缺失时，`PARENT-HISTORY` 和 `CHILD-ONLY` 都进入正文。没有 `createdAt` 时整页不读，这是正确的失败关闭。有 `createdAt` 且早于子消息时，父文字被排除、子文字保留。`identity.session_state` 在文件缺失时返回 `{}`，与解析器这条失败打开不是同一个函数。
- 应修的共同根因：父文字是否可读只取决于这份 `state.json`。读不到边界时不能把 wire 里已复制的父历史当成子任务正文；应与缺少 `createdAt` 一样失败关闭。普通非分叉会话的 wire 只有自己的消息，失败关闭不能误伤那种文件。

### 7. 同一版正文的摘要失败后不自动重试；新正文仍然独立入库

- 严重程度：中
- 证据：已复现。导出批次不看 `summary_status` 是静态核对（`export.py` 的 `build_batch` 只按 generation 取草稿）。
- 位置：`transcript_capture.py:100-137`。函数先把 `summary_status` 改成 `running`，再脱敏；任何异常，包括 `ScannerUnavailable`，都在 `finally` 写成 `failed`，detail 只有异常类型。第二次 `summarize_due` 不再挑选 `failed`。`engine.py:1498-1505` 在 `start()` 时把残留的 `running` 改成 `failed` / `interrupted; body retained`，不重新排队。
- 触发：正文已经保存，摘要线程开始后扫描器暂时不可用；或摘要仍是 `running` 时进程重启。
- 影响：这一版正文的标题停在摘录，直到出现新的正文版本。新版本会 `INSERT OR REPLACE` 成 `pending`，所以摘要失败不阻塞下一次正文，也不改正文。本轮在摘要命令存在时：正文先是 `pending`；扫描器换成缺失文件后摘要变成 `failed` / `ScannerUnavailable`；再次摘要仍是 `failed`；随后一条新公开记录仍 `organized`，正文同时含有 `BODY-KEEP` 和 `BODY-NEXT`，任务回到 `pending`。重启一条 `running` 摘要得到 `failed` / `interrupted; body retained`。晚到的摘要若 `body_digest` 已变，更新条件不会覆盖新正文；这是代码条件，没有单独再跑一遍。
- 应修的共同根因：摘要是附加的标题和摘要。扫描器或进程中断应把同一 `body_digest` 退回可重试，而不是永久 `failed`。正文提交路径保持现在这样，不要等摘要成功。模型政策继续由适配器内部固定，不要做成用户配置。

### 8. Kimi 隔离配置仍带着 always_thinking 和 max effort

- 严重程度：中
- 证据：隔离文件内容已复现，使用的是临时 `KIMI_CODE_HOME`，没有读用户家目录。原生 Kimi 是否因此打开 thinking，缺少证据；真实模型验收按约定暂缓，不能把组件测试说成 native 验收。
- 位置：`kimi/scripts/organizer.py:113-138` 整表复制 `models."kimi-code/k3"`，再追加 `[thinking] enabled=false`。
- 触发：来源配置含有 `capabilities = [..., "always_thinking", ...]` 和 `default_effort = "max"`。
- 影响：隔离后的 `config.toml` 仍有 `"capabilities" = ["thinking", "always_thinking", "image_in"]` 和 `"default_effort" = "max"`，同时有 `[thinking] "enabled" = false`。组件测试 `kimi/tests/test_admission_organizer.py:109-131` 只要求复制模型字符串并且出现 `"enabled" = false`，所以这个文件可以保持绿色。
- 应修的共同根因：隔离配置在复制模型表时去掉 thinking 能力和 max effort，只保留 `[thinking] enabled=false` 以及适配器内部的低强度摘要策略。不要增加用户可选的摘要模型。

### 9. 验收文档仍把旧模型口径写成当前要求

- 严重程度：低
- 证据：静态核对，不是运行时缺陷。
- 位置：`product/docs/harness-boundary-and-lifecycle.md:9-18` 已经写明正文不调用模型，Codex 摘要固定 GPT-6-Luna / low。同文件第 89 行仍写“Codex 模型验收继续使用 gpt-5.6-luna / max”，并允许 Kimi 用 K3 / max。`product/docs/architecture.md:131` 把可选摘要写成“另行配置的模型和强度”；代码里 Codex `agent_worker.py:17-18` 固定 `gpt-6-luna` / `low`，CC `organizer.py:156-157` 与 `183-184` 固定 low，并覆盖用户的 effort 环境变量。`implementation-status.md` 与 `release-acceptance-2026-09-23.md` 是历史记录。
- 影响：按第 89 行验收会把业务模型 max，或 Kimi K3/max，当成摘要或正文路径的通过条件。
- 应修的共同根因：第 89 行和 architecture 的“另行配置”改成与第 9–18 行相同的内部固定策略。历史验收保留原样，并标明不能代替当前正文路径。

## 现有测试固化或漏掉的行为

这些测试现在是绿的，因为前置条件绕开了正在验证的产品行为。

| 测试 | 实际固定住的行为 | 仍缺的正交检查 |
| --- | --- | --- |
| `core/tests/test_public_transcript.py:321-338` | 重复 `configure` 的文档没有 `consent_config`，不会进入 `settings.py:439` | 同意缺失、损坏、尚未写入 choice 时，相同 enable 必须保持 generation、`enabled_at` 和已收草稿 |
| `core/tests/test_consent_fault_recovery.py:192-233` | 只把同意文件改坏再读取，generation 确实不变 | 同一次故障期间再执行一次相同的社区写入，generation 也不得变化 |
| `codex/tests/test_sharing.py:170-209` | `timeout=5` 且管道很快写完，10 MiB 冗余正文可以入库 | 1.3/1.5 秒预算内，对象尚未闭合时也要转发已经写出的 `transcript_path` |
| `core/tests/test_public_transcript.py:223-233` | 只覆盖扫描器文件不存在时的 `public-io:` 重试 | 非零退出码和非法 span 必须重试同一个 capture id |
| `codex/tests/test_public_projection.py:60-72` | 坏记录不被当成噪声消费，`end` 停在坏行前 | 坏行前后都有合法公开消息时，前缀要入库，后文要能继续；引擎不得把任务永久停住 |
| `kimi/tests/test_admission_organizer.py:109-131` | 隔离文件含 `"enabled" = false` 即通过 | 隔离结果不得保留 `always_thinking` 和 `default_effort = "max"` |
| `core/tests/test_parser_io_accounting.py:137`、`171` | `io_bytes < 48*1024` 约束的是小尾部不要重读大前缀 | 不能把这个断言理解成公开正文上限。长消息覆盖在 `test_public_transcript.py:341-364`，本轮没有重跑，它会使用真实 Gitleaks |
| `core/tests/conftest.py:25-29` 与 `provenance.json` | CI 默认加载 `tests/fixtures/production-parsers` | 固定提交旧于本快照（kimi `299ad86…`、cc `71cfcca…`、codex `ebebe7d…`），但三份解析器字节与本快照一致，sha256 分别为 `4086914f…`、`c719bea6…`、`48d46635…`。不能据此说 CI 在测另一份解析器 |
| `core/tests/transcript_double.py` | 仍被 `test_public_transcript.py:200`、`test_shared_core.py`、`test_service_startup.py`、`test_mindie_loop.py`、`test_history.py`、`test_gap_recovery.py` 使用，双份实现可以截断 | 这些用例只代表旧 organize / 缺口制造。公开链路必须以三份正式解析器为准 |
| 多处 `Engine(..., agent_command=...)` | `validate_config` 仍接受格式正确的 `agent_command`；`cli.py:58` 与 `cli.py:390` 在缺少 `capture_mode` 时默认 `organize` | 只能当作旧安装兼容。成功的安装和更新应发布 scanner 与 `summary_command`，并同时去掉 `agent_command` |

没有覆盖、代码看起来正确但本轮没跑的检查：省略 `--fork` 时保留已有 fork；两条 Kimi Stop 对同一 wire 只追加一次（`reserve_region` 的冲突返回没有执行）。

## 已核对、当前不构成缺陷

- 贡献选择为 contribute 且策略相同时，generation 与 `enabled_at` 保持不变。调用方自造的 generation 不会成为权威。
- `fork=None` 不会删除已有 fork。`write()` 会弹出值为 None 的扩展键，随后 `transition()` 用旧文档把缺键补回。复现中 `alice/fork` 仍在，generation `bac46eaa530d4d57a42d13f5ba7ebfe6` 没有轮换。明确写成另一个 fork 才是策略变化。
- CC 的 48 KiB 是记录之间的分页目标（`cc/scripts/transcript.py:21`）。一条约 60019 字的公开消息整页保留，页文本 156028 字节，首尾标记都在，`more=true`，下一次从 `end` 读到 `SECOND-PAGE`。`MAX_WINDOW = 256*1024`（同文件第 20 行）没有被使用。Codex 解析器的页目标是 4 MiB，10 MiB 单条消息在其解析测试里整段返回。
- 正文路径不调用模型。正常扫描器下 `body_model_calls` 为 0。摘要失败不替换正文，也不挡住下一条正文。
- Codex 摘要命令固定 `gpt-6-luna` / `low`，并带 `--ignore-user-config`。CC 复用原生 provider 的模型，再把 effort 写成 low、`MAX_THINKING_TOKENS=0`。
- 当前安装/更新在 `prepare` 成功时同时去掉 `agent_command` 并写入 scanner 与 `summary_command`：Kimi `updater.py:244-251`，CC `updater.py:287` 之后的 prepare，Codex `auto_update.py:1079` 之后的 `capture_config`。`prepare` 抛错时新引擎文件不会发布，内存里的 pop 不会落盘。未被重写的旧配置仍默认 `organize`。本轮没有执行会下载 Gitleaks 的 `prepare`，这条是静态核对。
- GitHub 单文件上限 `MAX_FILE_BYTES = 100 * 1024 * 1024` 是平台限制。diagnostics `fallback.py:27` 的 1 MiB 和 maintenance 的默认修剪是日志上限。remote-dev `preview.MAX_TEXT_CHARS = 12000` 只截断远端工具输出。三者都不是知识正文的业务大小限制。没有看到 transcript 采集复用 remote-dev 的预览截断。
- 三份正式解析器与 core 固定夹具字节相同。半写行会推迟而不是吞掉。明确关闭再开启是一次真实新边界。

## 未深入的区域

- Windows / WSL 的 UTF-8、无空控制台、Job Object 子孙进程退出和版本绑定只读了实现，没有在 Windows 上执行。`windows_process.py` 使用挂起创建、Job 的 `KILL_ON_JOB_CLOSE`，失败时回退 `taskkill /F /T`。`loop/process.py:43-44` 使用 `CREATE_NO_WINDOW`，非 detached starter 时再加 `CREATE_BREAKAWAY_FROM_JOB`。不能据此报告 Windows 进程缺陷。
- remote-dev 的传输、SSH 和作业机只核对了预览长度上限，没有审完整作业生命周期。
- diagnostics 的 reporter、outbox 和 health 只核对了日志上限与 `reporting_commands.maintain` 的有界预算。
- 贡献发布、Git 传输、`reserve_region` 的跨进程并发没有执行。
- 版本绑定从“选定 generation 的解释器”到 `stage_retained_bootstrap` / launcher 当前版本，没有做端到端核对。
- 没有执行 NPU、真实 Gitleaks、真实 Kimi/CC/Codex 模型，也没有读取用户配置、认证文件或私人 transcript。
- Kimi 真实模型验收按产品约定暂缓。适配器的 setup、update、Stop、存储和贡献路径已按上面的组件行为审查；组件通过不能写成 native 验收。
