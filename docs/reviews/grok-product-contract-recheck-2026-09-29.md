# MindIE Agent 产品契约复查

复查对象是当前目录固定快照。`manifest.json` 记录的提交为：

| 仓库 | 提交 |
| --- | --- |
| core `knowledge` | `28568061ea9a94e9a1b4b057322b6bc8f66ff27b` |
| codex `mindie-agent-codex` | `657efc18aaaaee51624446394d91eb97bc2d32f8` |
| kimi `mindie-agent-kimi` | `02ff312e319f642bf1ea53db698d1b5c92cfdc59` |
| cc `mindie-agent-cc` | `ff861132460fb0db19ac3dbca4351f58678175ba` |
| product `mindie-agent` | `def143d2695a0808173cbd924e64c63259275135` |
| remote-dev `audit-remote-dev` | `28213bf3065e173216794c43ad021ef169e6a8c9`（与上轮相同） |
| diagnostics `audit-diagnostics` | `7c56f6b510b48fa60f256b46f71805e3be61eed8`（与上轮相同） |

本轮只对照上轮报告点名的差异阅读源码和 diff，没有改产品源码，没有跑测试，没有在 `/tmp` 完成确定性复现，没有启动服务或访问网络。上轮对旧提交的复现结果不能当作本快照的实测。下面凡写“静态”的结论都来自当前源码结构；写“未验证”的部分本轮没有执行。

结论：上轮 9 项里，扫描器重试、坏 JSONL 后续正文、Kimi 锁内合并项目根、`state.json` 读取失败不纳入父历史、摘要按同一 `body_digest` 恢复、隔离配置去掉 thinking / max effort、验收文档口径，以及“授权故障不换代”，在源码上已经落地。仍有 1 个具体问题：同意文件里已经明确保存 `read-only` / `later` / `disabled` 时，策略不变的再次启用仍会每次新开 generation。慢速未闭合 Hook JSON 在正常原生完整对象下不构成当前缺陷。浅克隆安装、服务锁等待和 Codex `fetch --no-auto-maintenance` 只做了静态核对，行为没有重跑。

## 仍有的具体问题

### 1. 明确的非 contribute 选择仍会使同策略启用每次换代

- 状态：仍有具体问题
- 证据：静态。本轮没有调用 `transition()`。
- 位置：`core/mindie_knowledge/loop/settings.py` 的 `transition()`。策略比较之后，只要新文档 `enabled` 且旧文档带有 `consent_config`，`capture_block_kind() == 'revoked'` 就把 `changed` 置真，随后新造 generation 并改写 `enabled_at`。`capture_block_kind()` 把有效同意文件中的 `read-only`、`later`、`disabled` 都定为 `revoked`。
- 触发：设置已经 `enabled`，同意文件可读且 choice 仍是这三项之一，repository、branch、visibility、account、fork、project_roots 都不变，再次执行 `transition()`、`write()`，或适配器的启用写入。Codex `set_enabled` 只有“开关和 choice 都已经是目标值”才直接返回；choice 仍是 `disabled` 时会先写设置，再在锁外 `record_choice`。Kimi 与 CC 的 `write_enabled` 每次都会进入 `ctx.write`。写设置成功、choice 尚未改成 `contribute` 时崩溃或重试，会再走一次换代。
- 影响：本快照的 `transition()` 会给出新的 generation 和新的 `enabled_at`。采集边界因此前移。上轮核对过的 outbox 会取消其他 generation 的未发送批次；本轮没有重读 `store.py`，这一下游效果沿用上轮，不算本轮实测。
- 已经分开的路径：同意文件缺失、不可读、损坏、没有 choice，或 `consent_config` 本身非法时，`capture_block_kind()` 返回 `fault`，这一条件不换代。choice 已是 `contribute` 且策略不变时，这一条件也不换代。
- 应修：choice 保持 `read-only` / `later` / `disabled` 的重复写入保持原 generation 和 `enabled_at`。从明确 opt-out 进入一次新的 contribute 边界时可以换代一次，换代不能发生在 choice 尚未变成 `contribute` 的每一次重试上。

## 上轮 9 项

| 项 | 状态 | 依据 |
| --- | --- | --- |
| 1. 相同启用在尚不能贡献时每次换代 | 仍有具体问题 | 故障、损坏、无 choice 已不换代。明确的 `read-only` / `later` / `disabled` 仍每次换代，见上节 |
| 2. 未闭合 Hook JSON 丢掉已出现的 transcript 路径 | 不构成当前缺陷 | 三端 reader 的“等完整对象”逻辑不在本轮 diff 中。见下文 |
| 3. 扫描器非零退出或非法报告后不重试 | 已解决 | 静态。两类结果都改为 `ScannerUnavailable`（`OSError` 子类），引擎对 public-transcript 的 `OSError` 延迟同一 capture |
| 4. 一条完整坏 JSONL 停住后文 | 已解决 | 静态。三端解析器隔离该行并继续。半写行分支未改 |
| 5. Kimi 在锁外合并项目根 | 已解决 | 静态。`extend_scope` 的重读和合并位于 `write_enabled` 的写上下文内。本轮没有做交错执行 |
| 6. Kimi 读不到 `state.json` 时纳入父历史 | 已解决 | 静态。读失败抛 `OSError`，函数在打开 wire 之前返回，父正文不会进入结果。引擎按 public-transcript 的 `OSError` 延迟同一 capture |
| 7. 同一版正文的摘要失败后不重试 | 已解决 | 静态。扫描器故障和服务停止把同一 `body_digest` 退回 `pending`；明确撤销写成 `cancelled`；错误模型结构保持 `failed` |
| 8. Kimi 隔离配置保留 always_thinking 和 max effort | 已解决 | 静态。模型表去掉 `thinking`、`always_thinking`、`support_efforts`、`default_effort`，并写 `[thinking] enabled=false`。没有用真实 Kimi 配置执行 |
| 9. 验收文档仍要求旧模型口径 | 已解决 | 静态，只核对上轮点名的两处。`harness-boundary-and-lifecycle.md` 与 `architecture.md` 已改为正文不调用模型，摘要为适配器内部 gpt-6-luna / low。没有全库再搜其他文档 |

## 本轮其余点名修复

这些结论都是静态的，本轮没有跑旧反例，也没有跑修复后的成功路径。

- 核心 `transition()` 接收完整请求文档。`configure()` 先把请求合并进当前文档再调用 `transition()`，未出现的扩展键保留。`write()` 对显式 `None` 扩展先弹出键，再把完整文档交给 `transition()`，因此显式 `None` 会删除 fork，缺省的 fork 不会被旧文档补回。
- 核心 `consent_store.record_choice` 在 choice 相同时直接返回，文档无变化则不写。CC、Kimi bootstrap、Codex 三份副本是同一改法。重复同一 choice 时 `migrated_from` 也不会被清除；本轮没有看到该字段参与授权判断，不单列问题。
- Kimi / CC 在省略 account 时取当前 account；省略 fork 时，仅在 repository、branch、account 都与当前目标一致时保留原 fork。目标变化时 fork 保持调用方的 `None`，`write()` 会删除旧 fork。CC 没有 `extend_scope`，项目根仍按调用方列表替换。Kimi 只在已启用且 repository、branch、account、fork 都一致时合并项目根。省略 account 时，即使 repository 变了也会留下原 account；这与“换目标不沿用旧 fork”的要求不冲突，本轮没有看到因此串用项目根的路径。
- CC workflow 对 knowledge checkout 写了 `fetch-depth: 0`，并把 core 引用改到本快照提交。`knowledge_checkout` 在浅克隆时抛出 `IdentityPrecondition`，发生在 pip 之前。真实安装改为 `bounded.run`，参数含 `--no-index`、`--no-deps`、`--no-build-isolation`；`run()` 默认 `check=True`，非零退出抛错，并在 `finally` 里按进程组清理。diff 中没有伪造 `direct_url` 的写入，测试仍读取安装后的来源元数据。安装本身本轮未执行。
- 核心 `serve` 对 `consumer.lock` 调用 `acquire(wait=STARTUP_TIMEOUT)`，期限仍是 5 秒。锁冲突为 `EAGAIN` 或 `EACCES` 时在该期限内重试。观察者释放后，这次启动可以拿到锁；锁被持有满 5 秒则 `StartInProgress`，`_serve` 返回 0，不另起服务。Stop 的 `request_wake` 使用的是 `wake.request.lock` 且等待时间为 0，不走这 5 秒等待。Windows 上 `msvcrt` 的 errno 本轮未验证。
- Codex 更新取源的 `git fetch` 在 `--depth=1` 前加入 `--no-auto-maintenance`。参数位置是选项。本机 git 是否接受该选项、后台维护是否因此不再启动，本轮未执行。

## 回归检查

全部为静态，本轮没有喂入样本。

- 正常尾页：页预算判断在计入该记录之前。放不下的下一条不消费，`end` 停在它前面，`more` 为真。页内第一条即使超过 `max_text_bytes` 仍整段保留。这个分支没有被坏行的 `continue` 改掉。
- 缺时间戳后文：仅当授权边界存在且该条没有时间戳时，解析器记录起止位置和原因、不把原文放入正文，然后继续。边界不存在时，缺时间戳的公开记录仍可进入正文。后文带有不早于边界的时间戳时可以进入正文。Kimi 在 `fork_time` 已确定时，无时间戳记录会先被排除出正文并前移游标，计入 `skipped_records`，不写入 `discarded_records`。正文不包含该条，后文仍继续。
- 半写行：没有换行的尾部仍把 `partial` 置真并 `break`，不推进 `end`。引擎对 `partial` 且 `end == start` 的路径仍是推迟。
- 重复 enable：choice 已是 `contribute` 且策略不变时，`transition()` 的换代条件不成立。这是主路径。残留问题只覆盖 choice 仍为明确 opt-out 的重复写入。
- 摘要撤销：`summarize_due` 只挑选 `summary_status='pending'`。`MaintenanceCancelled` 且 `engine.stop` 未置位时写成 `cancelled`，detail 为 `authority revoked`，不会被再次挑选。`stop` 已置位时退回 `pending`。服务启动把残留的 `running` 改回 `pending` 并保留原行的 `body_digest`。撤销与停止同时发生时，停止优先，重启后若授权仍是 revoked，下一次会在模型调用前取消；这是一次额外尝试，不单列。
- 错误模型结构：标题或摘要的形状错误落入通用 `Exception`，状态保持 `failed`，选择器不取 `failed`。
- 正文不等摘要：本轮 diff 只在已经整理的 capture detail 中加入 `discarded_records`，摘要函数仍在正文提交之后。摘要失败的更新带 `body_digest` 条件。
- 过度防御和静默截断：本轮读到的产品改动是去掉核心 CLI 的 128 KiB stdin 上限、handoff 对 `transcript_path` / `cwd` 的 4096 上限、Codex 项目根 1024 上限、适配器配置 64 KiB 上限和同意文件 64 KiB 上限。这些路径改为拒绝 NUL、要求类型正确，或等待完整 JSON。没有看到新的正文长度截断。宿主进程期限和 1.5 / 1.3 / 2 / 5 秒 Hook 或启动期限仍在。缺时间戳记录在有授权边界时被排除，是该条不授权，后文继续。

任务身份方面，三端仍在读记录循环之前用路径会话做 `wrong-task` / `unknown-format` 判断。CC 对单条记录里不一致的 session id 仍只丢弃该条。坏行 `continue` 发生在这些判断之后。

## 未闭合 Hook JSON

不构成当前缺陷。

Codex `bridge.py` 的 `_read_hook_stdin` 仍等到 EOF、期限，或缓冲区能够 `json.loads` 成一个完整值。成功解析后，`hook_event` 仍要求 `Stop`、合法 `session_id` 和 `turn_id`、`stop_hook_active` 为假，以及绝对 `cwd` 和 `transcript_path`。本轮 diff 没有把“看到 `transcript_path` 就转发”写进去。CC / Kimi 的 launcher 读循环不在本轮变更文件里，仍是上轮看到的完整 JSON 读法。

正常原生 Stop 发送的是一个完整对象，写完后管道会结束，或者最后一个数据块已经使整个对象可解析。这种输入由完整对象进入身份校验，不需要从半个对象里猜任务、递归 Stop 或子代理标识。上轮那种把预算降到 0.35 秒、或在对象尚未闭合时持续滴入的做法，只说明未闭合输入会在进程期限到达时被放弃。它不证明正常产品链路丢掉已经写完的正文。不完整身份不应放行。

核心 CLI 的 `hook` 已改为读到 EOF 再 `json.loads`。旧的 128 KiB 静默返回 `{}` 已删除。三条原生 Stop 桥不走这条 CLI stdin。未闭合且没有外部进程期限的 CLI 管道会一直读到 EOF；这是进程期限问题，不是正文业务上限。

本轮没有重测 129 KiB、1 MiB、10 MiB 的 Stop 子进程，也不把他人给出的通过次数当作本报告的证据。

## 快照之后的说明

以下三项发生在本快照之后。本轮没有读到对应修复，没有执行，不把它们记为独立通过，也不把它们写成仍开放的缺陷。它们应按单独的回归证据记录。

- `project_roots` 的目录别名去重和顺序。本轮只看到 `transition()` 用解析后的路径集合比较策略，没有读 `normalized_roots` 的实现。
- 纯坏页的位置诊断被 `finish_region` 的默认空 detail 清掉。本轮看到“无公开正文”路径把 `discarded_records` 传入 `reserve`，随后调用 `finish_region(region_id, "succeeded")` 时没有再传 detail。没有读 `finish_region`，不能自行判定诊断是否被覆盖。含有公开正文的页把同一诊断放在 `mark_capture` 的 detail 里，这条路径不经过该次 `finish_region`。
- Codex 一次性 Git 源夹具在第一次 commit 时启动自动维护。本轮只看到更新流程的 `git fetch --no-auto-maintenance`，没有读该夹具。

## 未覆盖

- 本轮零次执行。授权换代、解析器分页、扫描器重试、摘要状态、锁内合并、浅克隆 pip、锁观察者竞争、`git fetch` 参数，都没有实测。
- 没有重读 `store.py` 的 outbox 取消和 `enabled_at` 采集下界，相关影响沿用上轮。
- 没有逐行核对正文脱敏的调用点是否一定在游标提交之前。能确定的是 `redact()` 对非零退出、非法 span、子进程 `OSError` 和超时抛出 `ScannerUnavailable`，而 public-transcript 引擎对 `OSError` 延迟同一 capture。相对路径或空扫描器路径仍在子进程之前抛 `ValueError`，该异常不是 `OSError`。
- Kimi `state.json` 已是合法对象、存在 `forkedFrom` 但没有 `createdAt` 时，解析器仍返回 `unknown-format`。引擎对该状态会把 capture 标为失败，不是 `OSError` 重试。这与上轮“没有 `createdAt` 则整页不读”一致。下一次 Stop 会不会新建 capture，本轮未验证。
- 生产解析器夹具与三端正式解析器是否字节相同，本轮未做哈希。
- `admission_ops.py`、`mcp_gate.py`、各仓库 `runtime-requirements.txt`、核心与 Kimi/Codex workflow 的 diff、大部分测试 diff，本轮没有读。
- remote-dev 与 diagnostics 提交未变，本轮未审。
- 没有执行 Windows、真实 Gitleaks、真实模型、NPU、私人 transcript 或凭据。Kimi / Claude 原生模型验收仍未执行。组件上的静态核对不能写成 native 验收。