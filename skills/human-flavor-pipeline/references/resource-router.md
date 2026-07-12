# 资源加载路由

按任务读取最少必要资源。不要为了「全面」一次加载整个目录。

| 条件 | 必读 | 条件读取 |
|------|------|----------|
| 所有任务 | `patterns/banned-words.md`、`references/scoring.md` | 无 |
| 载体 / 文体边界不清 | `patterns/channel-presets.md` | 目标载体与受众 |
| 需要校准笔调 | `patterns/voice-profiles.md` | 当前激活 Profile 或用户真文 |
| 规则命中拿不准 | `patterns/catalog/README.md` | 只进入对应深查文件 / 编号 |
| 营销代理任务 | `packs/marketing-agency/router.md` | 按路由读取 corpus 局部 |
| 完整改写 | `references/editing-protocol.md` | 对应文体的深查规则 |
| 输出报告 | `references/report-format.md` | 按 detect / review / full 选模板 |

Profile 默认 `profiles/default.md`;不得自动启用 `profiles/lens.md`。外部本地 Profile 的明确指令优先于仓库 Profile。
