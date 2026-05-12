# deep-ai-analysis

拦截并分析 AI 服务 HTTP/HTTPS 流量的 CLI 工具包。

## 环境要求

- Python 3.10+
- [mitmproxy](https://mitmproxy.org/)（通过 `brew install mitmproxy` 安装）

## 安装

### 一键安装脚本（推荐⭐️⭐️⭐️⭐️⭐️）

```bash
bash <(curl -s https://msstest.sankuai.com/ad-dqe-public/ai-coding-analysis/install.sh)
```

或者手动下载后执行：

```bash
curl -O https://msstest.sankuai.com/ad-dqe-public/ai-coding-analysis/install.sh
bash install.sh
```

### 从源码安装（开发模式）

```bash
git clone ssh://git@git.sankuai.com/~zhoukang04/deep-ai-analysis.git
cd deep-ai-analysis
pip install -e .
```

## 快速开始 ⭐️⭐️⭐️⭐️⭐️

三步快速开始

```bash
# 终端 1 — 启动代理
deep-ai-analysis proxy

# 终端 2 — 通过代理启动 mc，开始AI Coding
deep-ai-analysis start-mc

# 终端 3 - 浏览器查看AI工作内容
deep-ai-analysis web-server
```
