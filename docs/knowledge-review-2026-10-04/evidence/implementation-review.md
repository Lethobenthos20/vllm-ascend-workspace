# 实施阶段证据与九原则审查

日期：2026-10-04。这是初始研究之后、原生安装与 GitHub/Grok 完整验收之前的实施快照。它补充研究结论，不把后来取得的结果倒填到最初只读调查，也不把本地结果写成生产部署完成。阶段、原始快照和当前文件 SHA256 见[证据清单](manifest.json)。

## 版本与实际边界

| 对象 | 本阶段版本或依据 | 能证明的范围 |
| --- | --- | --- |
| knowledge | `0fa011701f4d73f40709df56c969cc3492eb8fab` | 已实现任务材料包、真实 ReMe 检索、LangMem 增量索引与可见失败；完整远端 CI 结论仍待核对 |
| Codex | `78d9cffcf207a9ac7ab862f6b158906210693d52` | 本地提交及精确依赖定向测试；不是已安装插件的原生 Hook 验收 |
| 内容仓库 | `b11527d52c6f656ff98e94adad86513e2ab7d90a` | 20 条已公开内容的一次离线转换及固定 validator 检查；此快照未取得远端新 workflow 验收 |
| 原则依据 | 当前主工作区 `docs/design-principles.md`；Git blob `9b21e6ae87ac96ff8bdacc3f4f546384e111a184`，SHA256 `15b4b58385846051464c27d06922ad0353bdd6a4031b619ff248c3a65c179741` | 包含第 9 条和开发 PR review 的当前实际文本，不只引用旧 HEAD |

ReMe 固定为 `4c54c2b650038eff2a5d0d77aaa61b3e836f1b18`，实际使用其 Markdown chunker、LocalFileStore、FileGraph、BM25 和派生缓存，不启动默认 Application、jobs、watcher、模型、embedding 或 tags。读取和持久化错误通过窄覆盖到达调用者。技术标识符分词保留 API basename、版本及中文词项。规范包、Git 哈希、候选文件与已提交元数据的事务衔接仍由 MindIE 承担，不能归称为 ReMe 原生事务。

最后复查在此前 core `ec5f33e9d6a329c0fb48cea67cba66113e70a5b9` 复现一项原始字节完整性缺口：本地 Markdown 通过 `Path.read_text` 读取时会隐式归一换行，实际文件字节变更可能未使 export/ReMe 前置校验失败。该问题已在 `0fa011701f4d73f40709df56c969cc3492eb8fab` 修复：6 处 Markdown 读取/比较及 ReMe 前置读取改为原始字节读取后显式 UTF-8 decode，JSON 行为保持不变。block/manifest 的 CRLF 字节损坏现在令 get、export、search、reinstall 明确失败，current 指针与缓存不推进。受影响测试 **52 项通过**，另 **1 项 Windows 长路径 fixture 定向通过**；这些局部结果不替代该新提交的远端 CI。

LangMem `0.0.30` 的函数处理完整新增块及已有短导航；单块至多 16 KiB，每批至多 8 块，序列化用户 prompt 至多 64 KiB。该限制不截断整个任务，也不是包含宿主上下文的总 token 或货币费用硬上限。正文保持普通 Markdown，SQLite 只保留小元数据和操作回执。旧 FTS、全文重写 organizer 和历史兼容恢复路径已删除。

Worker、调用回执、原生适配及其精确测试版本见[专门审查](organizer/implementation-review.md)。其中 303 项本地全套测试使用 core `9dba4d46dda5b798dd27fdf207262c3ad98f7339`，12 项平台相关跳过；后来在 core `f72445403fe9069f0abaa224306943e7de608500` 上完成 26 项启动、feed、失败可见性和安装 pin 定向测试。没有把前一版本的全套结果改记为最后版本全套通过。 最终 Codex `78d9cffcf207a9ac7ab862f6b158906210693d52` 只跟随更新安装 pin；精确 core 安装与 preflight 通过，installed-runtime 定向单测 1 项通过（2.979 s），没有再运行前述 303/26 项。

已取得的远端 CI 局部结果绑定 PR head `f72445403fe9069f0abaa224306943e7de608500`，三个 job 的实际 checkout 均为 PR merge commit `9de371bf3369d434e7176fba3fac088b2881bf13`，合入 base `2637ffa848c0a44bde38ee488112150ee9bc0743`。日志确认如下；Windows 在该版本暴露 CRLF 包契约失败。后续 `ec5f33e9d6a329c0fb48cea67cba66113e70a5b9` 已修复受管 Git checkout 的换行恢复和 checkout/diff 失败可见性；后续 head 的结果不能沿用此表。

| 远端 job | 实际结果 | 耗时 |
| --- | --- | --- |
| Ubuntu contracts | 622 passed、9 skipped、1 warning | 311.54 s |
| macOS contracts | 622 passed、9 skipped、1 warning | 446.09 s |
| Package checks | 622 passed、9 skipped、1 warning | 391.74 s |

随后 `ec5f33e9d6a329c0fb48cea67cba66113e70a5b9` 的 Windows 运行在 110 passed、23 skipped 后暴露原始 Git fixture 的长路径问题；对应 fixture 已随 `0fa011701f4d73f40709df56c969cc3492eb8fab` 修正。此计数是失败前已观察范围，当前 `0fa011701f4d73f40709df56c969cc3492eb8fab` 的远端 CI 全部仍待结果。

## 真实材料测量

依据是 core 固定提交中的[匿名 K3 验收 JSON](https://github.com/mindie-agent/knowledge/blob/0fa011701f4d73f40709df56c969cc3492eb8fab/tests/fixtures/k3-system-acceptance-2026-10-04.json)，文件 SHA256 为 `97de7962f717c7db83ff884488c1537c6c38ae7ebb6efcf08b9205cb54da93c4`。只复核公开计数和结果，不把真实 transcript 复制到本证据目录。此提交绑定的是匿名测量记录，不表示后来的平台修复又重放了全部真实模型调用。

| 检查 | 实际结果 | 解释边界 |
| --- | --- | --- |
| 选定历史材料 | 4 个真实 K3 任务，81 个块全部建立索引 | 仅这 4 个显式选择的快照，不代表任意私有材料均可公开 |
| 指定小模型 | `gpt-5.6-luna` / `low`，35 次原生 worker 调用 | 计数是 native invocations，不是独立观测到的提供商内部请求数 |
| 用量 | 658,424 input tokens、33,219 output tokens；unknown calls 为 0 | 原生回执的实际 token 计数，不推断货币价格 |
| 本地检索 | 12/12 个任务目标查询找到相关任务，均有正文片段 | 特定目标查询检查，不是通用召回率或语义质量认证 |
| 独立消费者 | 本地 Git 文件协议获取 4 个任务包，12/12 查询命中，0 次模型调用；重复同步 unchanged | 尚不等于 GitHub 传输、Grok 收件或合并验收 |

35 次调用包含失败 attempt 34：3 个源块返回了 4 个索引，其中 1 个重复；该次已知 22,077 input / 1,483 output tokens 保留在累计量中，没有被重置为未调用或自动重试。输出 schema 随后约束精确数组长度，仍保留身份和顺序校验；显式 attempt 35 后完成全部 81 块。这个失败及修复不能证明以后所有模型输出都正确。

## 公开内容的一次转换

内容源提交 `9aab5e1e2f1298f992b1b41e403c2b1e0232d12c` 的 20 条现有公开条目转换为 20 个任务包、22 个块。按清单逐项核对原文件、正文、新 manifest 及 revision 的哈希；拼接块正文精确重现 110,289 字节，包括原有最终换行。标题、摘要、conditions 和 entry ID 沿用，唯一反馈文件字节不变，投票仍属于原 revision。

转换没有模型调用；`status: complete` 仅表示索引打包完成。最终内容提交由 `0fa011701f4d73f40709df56c969cc3492eb8fab` 的固定源码验证，得到 20 entries、1 feedback、246,051 bytes。workflow 的两个内嵌 Python 脚本编译通过，安装和结果摘要引用同一个固定 validator SHA；任务包拓扑与所有 block hash 都参与检查。

新 CI 和文档通过 whitespace 检查。全迁移 diff 中的一处两空格 Markdown hard break 来自原公开正文，为满足精确保留要求保持原字节，不声称全 diff 没有任何 whitespace 提示。

## 公开证据检查

所有 tracked/new 文本文件都经过固定 core 版本的 public-data 扫描，另检查本机用户目录和原始 transcript 路径模式。已将研究清单、复现命令、探针和 selector 回执中的本机路径改成明确的工作副本角色或相对路径；源码 commit/hash 和原始测量值保留。路径归一后的探针仅作语法检查，没有把原始实验重新记为执行过。

规则仍会命中公开来源 URL、仓库相对证据路径、检索指标记号、包版本号、明确合成的 PEM 边界 canary 以及已经脱敏的占位符。逐项复核后将这些记录为 reviewed findings；它们没有被当作真实凭据，也没有通过全局放宽产品扫描规则来隐藏。具体计数和未解决项见清单的 `validation.public_data_scan`，不声称原始扫描零命中。机械规则扫描仍不构成所有语义隐私均已识别的保证。

## 九原则结论与本轮修正

1. **总成本。** 增量处理只使用新增完整块和短导航；消费者复用现有索引，不再调用模型。一次内容转换复用原始公开成果，文档修正不重跑真实模型实验。
2. **封闭问题。** schema、包完整性、哈希、边界、批次和调用回执有明确机械合同；模型摘要与知识是否适用仍是参考判断。文档已把“未入 manifest 的文件拒绝”明确限定为任务包内部。
3. **理解负担。** 对使用者呈现任务材料、检索卡和明确错误；初始研究、实现和验收分阶段呈现，避免要求读者自己辨别互相冲突的“当前”结论。公开源码定位使用工作副本角色及相对路径，不要求读者访问某台机器的目录。
4. **职责边界。** ReMe 拥有分块和派生检索，LangMem 负责索引生成，MindIE 保留授权、规范包与事务衔接，GitHub 是公开版本权威；不把自有 glue 声称为框架已接管。当前材料的一套权威文件是 Markdown，ReMe 派生缓存可能包含文本，可独立重建；这不承诺磁盘只有一份字节副本。SQLite 不镜像正文，本地不另建原始 transcript 副本或逐 revision 正文档案。
5. **Skill 信息性。** 此文档变更不创建 Skill、固定研究路线或业务收尾要求。开发 PR 的原则审查是已有交付规则；经验正文继续作为知识材料保存。
6. **参考性。** 原正文、失败、更正和不确定性保持，已有摘要明确为 fallible index。任务索引完成、规则扫描、检索命中和公开审核均不认证技术结论；保留原反馈 revision。
7. **按需介入。** 实测只覆盖用户明确选定的四份历史及已有公开内容转换。普通任务不因文档或安装自动导入旧历史，不新增模型裁判或强制经验贡献。
8. **成果复用。** 保留初始研究快照及当时哈希；复用固定原生回执和既有机制测试。公开证据仅将本机路径归一成工作副本角色与相对路径，原始测量没有重新运行或改写；初始清单 SHA 标明为归一前文件哈希。后续平台修复使用相关定向验证，明确前后版本，不通过重复全量运行掩盖证据差异。
9. **错误可见。** 模型失败和未知保留实际状态与已知用量；已返回输出的本地恢复不重复付费。缺少必要 worker、损坏索引、包校验失败和提交后的清理错误不能成为成功或空数据。文档修正了全任务“未调用模型”的过时描述，并保留远端权限拒绝与未完成验收，未把本地通过冒充外部完成。

当前尚未完成远端平台 CI、已安装插件与原生 Hook、GitHub 内容 PR dispatch、Grok 事件/审查/合并完整链的验收。主任务报告内容仓库 `ca16093b5c0383ab486cea13f8b1a22c61d964ed` 的 workflow 修改 push 因 OAuth token 缺少 workflow scope 被拒绝，尚未创建对应远端分支或 PR；后续 `b11527d52c6f656ff98e94adad86513e2ab7d90a` 仅更新本地 validator pin，没有再次尝试 push。主机锁定也阻止了剩余原生 UI 验收。这两项是验收环境阻碍，不能推断为产品缺陷。这里记录拒绝，不重复 push，也不改用旧 validator 的零条目绿灯作为验收。后续验收应追加独立阶段和真实回执，不能覆盖以上已知失败或倒改初始研究状态。
