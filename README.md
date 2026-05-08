# deep-ai-analysis

CLI toolkit for intercepting and analyzing AI service HTTP/HTTPS traffic.

## Requirements

- Python 3.10+
- [mitmproxy](https://mitmproxy.org/) (installed automatically as a dependency)

## Installation

```bash
pip install -e .
```

This registers the `deep-ai-analysis` command in your current Python environment.

## Commands

### `proxy`

Starts an HTTP/HTTPS intercepting proxy. Matching traffic is recorded to daily JSONL log files.

```
Usage: deep-ai-analysis proxy [OPTIONS]

Options:
  --port INTEGER      Port for the proxy to listen on.  [default: 7788]
  --output DIRECTORY  Directory where JSONL log files are written.  [default: ./logs]
  --help              Show this message and exit.
```

**Examples:**

```bash
# Start on default port 7788
deep-ai-analysis proxy

# Custom port and log directory
deep-ai-analysis proxy --port 9000 --output ~/ai-logs
```

On startup, the proxy prints the listening address, active filter domains, log directory, and CA certificate path.

## Domain Filtering

The domains to record are configured in `deep_ai_analysis/config.py`:

```python
RECORD_DOMAINS: list[str] = [
    "mcli.sankuai.com",
]
```

Only traffic to domains in this list is written to disk. All other traffic is proxied transparently without logging.

## HTTPS Setup

mitmproxy decrypts HTTPS traffic using a local CA certificate. You need to trust it once:

```bash
# The CA cert is generated on first run at:
~/.mitmproxy/mitmproxy-ca-cert.pem

# macOS — trust the cert system-wide:
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
```

Then configure your HTTP client to use the proxy:

```bash
# curl
curl -x http://127.0.0.1:7788 https://mcli.sankuai.com/...

# Environment variables (affects most CLI tools)
export http_proxy=http://127.0.0.1:7788
export https_proxy=http://127.0.0.1:7788
```

## Log Format

Logs are written to `logs/YYYY-MM-DD.jsonl` — one JSON object per line.

**Standard request:**

```json
{
  "timestamp": "2026-05-08T10:30:00.123456+00:00",
  "domain": "mcli.sankuai.com",
  "method": "POST",
  "url": "https://mcli.sankuai.com/v1/chat/completions",
  "request": {
    "headers": { "content-type": "application/json", "authorization": "Bearer ..." },
    "body": "{\"model\": \"...\", \"messages\": [...]}"
  },
  "response": {
    "status": 200,
    "headers": { "content-type": "application/json" },
    "body": "{\"id\": \"...\", \"choices\": [...]}"
  },
  "is_sse": false
}
```

**SSE (streaming) request:**

```json
{
  "timestamp": "2026-05-08T10:31:00.000000+00:00",
  "domain": "mcli.sankuai.com",
  "method": "POST",
  "url": "https://mcli.sankuai.com/v1/chat/completions",
  "request": { "headers": {}, "body": "..." },
  "response": {
    "status": 200,
    "headers": { "content-type": "text/event-stream" },
    "body": "data: {...}\n\ndata: {...}\n\ndata: [DONE]\n\n"
  },
  "is_sse": true,
  "sse_events": [
    "data: {\"id\":\"...\",\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}",
    "data: {\"id\":\"...\",\"choices\":[{\"delta\":{\"content\":\" world\"}}]}",
    "data: [DONE]"
  ]
}
```

**Query logs with `jq`:**

```bash
# Show all recorded URLs
jq -r '.url' logs/2026-05-08.jsonl

# Show only SSE requests
jq 'select(.is_sse == true)' logs/2026-05-08.jsonl

# Count requests by method
jq -r '.method' logs/2026-05-08.jsonl | sort | uniq -c
```
