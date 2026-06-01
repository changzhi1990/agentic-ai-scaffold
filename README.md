# Agentic-AI-Benchmark-Agent

一个可运行、可扩展、面向 Linux GPU Server 的 Python Benchmark Agent 工程。

当前阶段只实现两类能力：

- 系统配置检查
- 基础能力测试（NCCL / NVBandwidth）

不包含：

- 多轮 Agentic workload benchmark
- Tool calling workflow benchmark
- Ranking
- Tuning recommendation
- 自我优化、自我进化、自动调参、自动学习
- 多节点调度、Agent 协同

## Features

- 结构化采集 Linux 系统与 GPU/NIC/PCIe 拓扑信息
- 自动检测命令是否存在，缺失时降级而非崩溃
- 执行 NCCL allreduce / alltoall benchmark 和 NVBandwidth benchmark
- 支持 benchmark binary 路径、参数、超时、重复次数配置
- 生成 JSON 与 Markdown 标准化报告
- Markdown 报告使用对齐表格，并直接展开命令完整输出
- 提供 CLI 与 FastAPI 接口

## Project Layout

```text
agentic_ai_benchmark_agent/
  README.md
  AGENT.md
  SKILLS.md
  requirements.txt
  .env.example
  config/
    settings.yaml
    benchmark_profiles.yaml
  app/
    main.py
    agent.py
    orchestrator.py
    models.py
  inspection/
    system_inspector.py
    parsers.py
    topology.py
  benchmarks/
    nccl_runner.py
    nvbandwidth_runner.py
    metrics.py
    parsers.py
  tools/
    shell_tool.py
    file_tool.py
  reports/
    generator.py
    markdown_report.py
    json_report.py
  interfaces/
    cli.py
    api.py
  data/
    results/
    reports/
  tests/
    test_system_inspector.py
    test_nccl_runner.py
    test_nvbandwidth_runner.py
    test_report.py
```

## Requirements

- Python 3.10+
- Linux
- 可选命令：`lscpu`、`numactl`、`lspci`、`nvidia-smi`、`sysctl`、`lsmod`
- 可选 benchmark binary：
  - NCCL：`all_reduce_perf`
  - NVBandwidth：`nvbandwidth`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果目标机器没有 `python3-venv`，可以退化为用户级安装：

```bash
pip3 install --user --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## CLI

```bash
python3 -m app.main run
python3 -m app.main inspect
python3 -m app.main nccl --profile default
python3 -m app.main nvbandwidth --profile default
python3 -m app.main run --output-dir data/reports/manual
```

默认 `nccl` profile 会执行两类测试：

- `all_reduce_perf`
- `alltoall_perf`

默认命令参数为全 GPU 压测风格：

```bash
NCCL_NTHREADS=128 NCCL_MIN_NCHANNELS=8 NCCL_P2P_LEVEL=SYS all_reduce_perf -b 128 -e 8G -f 2 -g 8
NCCL_NTHREADS=128 NCCL_MIN_NCHANNELS=8 NCCL_P2P_LEVEL=SYS alltoall_perf  -b 128 -e 8G -f 2 -g 8
```

## API

启动：

```bash
uvicorn interfaces.api:api --host 0.0.0.0 --port 8000
```

示例：

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/inspect
curl -X POST http://127.0.0.1:8000/benchmark/nccl -H 'content-type: application/json' -d '{"profile_name":"default"}'
curl -X POST http://127.0.0.1:8000/benchmark/nvbandwidth -H 'content-type: application/json' -d '{"profile_name":"default"}'
curl -X POST http://127.0.0.1:8000/run -H 'content-type: application/json' -d '{"run_nccl":true,"run_nvbandwidth":true}'
```

## Output

完整流程返回结构示例：

```json
{
  "inspection": {},
  "benchmarks": {
    "nccl": {},
    "nvbandwidth": {}
  },
  "report_paths": {
    "json": "data/reports/benchmark_report_20260601_120000.json",
    "markdown": "data/reports/benchmark_report_20260601_120000.md"
  },
  "status": "success",
  "warnings": []
}
```

## Notes

- 硬件信息只读取系统可获取数据，不伪造 BIOS、驱动、CUDA、NCCL 版本。
- 当命令不存在、binary 缺失、解析失败、GPU 缺失时，流程保持可运行并返回 warning。
