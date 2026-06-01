# SKILLS.md

## Built-In Runtime Capabilities

- System inspection
- GPU / NIC / PCIe topology parsing
- NCCL benchmark execution
- NVBandwidth benchmark execution
- JSON report generation
- Markdown report generation
- Typer CLI
- FastAPI service interface

## Reserved Capabilities

当前只保留扩展位，不实现逻辑：

- optimizer
- evolution
- ranking
- recommendation

## Design Defaults

- 语言：Python 3.11+
- 配置格式：YAML
- 数据模型：Pydantic v2
- CLI：Typer
- API：FastAPI
- 日志：标准库 `logging`
