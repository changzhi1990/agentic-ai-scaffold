# AGENT.md

## Current Scope

当前版本仅处理两件事：

- 系统配置检查
- NCCL / NVBandwidth 基础能力测试

## Execution Principles

- 优先读取 Linux 原生命令与 `/proc`、`/sys` 信息
- 命令缺失时返回 warning，不中断整个流程
- benchmark 失败时保留 stdout/stderr 与结构化状态
- 所有输出统一汇总为结构化结果与标准化报告

## Future Extension Points

以下方向只预留接口，不在当前阶段实现：

- optimizer
- evolution
- ranking
- self-optimization
- self-evolution
- multi-agent orchestration
