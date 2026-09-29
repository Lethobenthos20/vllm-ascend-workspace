## 复核意见：已解决

针对「明确 opt-out 下，同一次启用被中断后重试反复换代」这一项，提交 `ec05a65c6841ca77ec55c7ea32232efa6699f342` 的 `transition()` 静态上已满足本次产品要求。本结论只覆盖这一项，不是全产品结论。

静态依据是该 diff，加上此前读过的 `capture_block_kind()`、`write()` / `configure()`、`record_choice()`，以及 Codex `set_enabled`、Kimi/CC `write_enabled`。三个适配器的调用方式不在这份 diff 里；按此前代码，重试仍会把同一策略送入核心 `transition()`，边界现在由核心收口。

- 首次写入：没有旧 generation 时 `changed` 为真。同意文件有效且 choice 为 `read-only` / `later` / `disabled` 时，generation 改为由 schema、同意路径、choice、`choice_at`、策略字段和解析后的根集合派生的 32 位值，并写一次 `enabled_at`。
- 重复重试：同一 `choice_at` 和同一策略得到同一个派生 generation，`changed` 不再被置真，沿用原来的 generation 和 `enabled_at`。`write()` / `configure()` 只在文档有差异时落盘，因此完成后的重复启用不写文件。此期间 `allows_capture()` 仍要求 choice 为 `contribute`，采集保持关闭。
- 完成后再关闭：`record_choice` 只有在 choice 实际变化时才更新 `choice_at`。再次启用会因新的 `choice_at` 得到新 generation，并前移一次 `enabled_at`。随后对这一新选择的重试再次稳定。
- 路径顺序和别名：解析后的根集合不变时，先恢复旧的 `project_roots`；派生 generation 使用排序后的解析路径。顺序或目录别名不会单独变成新的未完成启用边界。
- 合法边界恢复：choice 变为 `contribute` 后不再进入派生分支。策略不变时不换代、不改 `enabled_at`；同意文件被重新读取后采集才打开。
- 缺失或损坏的同意文件不会进入 `state == 'ok'` 且 choice 属于那三项的分支，不会因此换代，仍由原有 fault 门禁挡住采集。

主代理提供的 Windows 四模块 72 项通过，以及连续四次 `configure(enabled=True)` 由 4 个边界变为 1 个，是主代理记录，不是本次静态复核的实测。

未覆盖：没有运行测试，没有重读 outbox 如何标记旧 generation，没有查看三个适配器的依赖更新 diff，也没有做原生模型验收。