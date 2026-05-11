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

## Quick Start

Intercept `mc` traffic in two steps:

```bash
# Terminal 1 — start the proxy
deep-ai-analysis proxy

# Terminal 2 — launch mc through the proxy
deep-ai-analysis start-mc
```

## Commands

### `proxy`

Starts an HTTP/HTTPS intercepting proxy. Matching traffic is recorded to daily JSONL log files.

```
Usage: deep-ai-analysis proxy [OPTIONS]

Options:
  --port INTEGER      Port for the proxy to listen on.  [default: 7788]
  --output DIRECTORY  Directory where JSONL log files are written.  [default: ~/.deep-ai-analysis/raw-req-resp]
  --help              Show this message and exit.
```

**Examples:**

```bash
deep-ai-analysis proxy
deep-ai-analysis proxy --port 9000 --output ~/ai-logs
```

On startup, the proxy prints the listening address, active filter domains, log directory, and CA certificate path.

---

### `start-mc`

Launches `mc --code` with proxy environment variables automatically injected.

```
Usage: deep-ai-analysis start-mc [OPTIONS]

Options:
  --port INTEGER  Proxy port to point HTTPS_PROXY at.  [default: 7788]
  --help          Show this message and exit.
```

Sets the following environment variables for the `mc` process:

| Variable | Value |
|---|---|
| `HTTPS_PROXY` | `http://127.0.0.1:<port>` |
| `NODE_EXTRA_CA_CERTS` | `~/.mitmproxy/mitmproxy-ca-cert.pem` |

```bash
deep-ai-analysis start-mc
deep-ai-analysis start-mc --port 9000
```

---

### `clear-req-resp`

Cleans raw proxy JSONL logs into structured records. Parses `request.body` as JSON, reconstructs `response_json` from SSE events, and extracts `claude_session_id` from request headers. Non-SSE records are skipped.

```
Usage: deep-ai-analysis clear-req-resp [OPTIONS] INPUT

Arguments:
  INPUT  Path to a .jsonl file or a directory containing .jsonl files.

Options:
  -o, --output PATH  Output path (single-file mode only).
  --help             Show this message and exit.
```

**Output format** (JSONL, one record per line):

```json
{
  "timestamp": "2026-05-08T05:06:43.598393+00:00",
  "domain": "mcli.sankuai.com",
  "method": "POST",
  "url": "https://mcli.sankuai.com/v1/messages",
  "claude_session_id": "e75940a3-3a79-41bd-be4d-6d0fb1a5a307",
  "request_json": { "model": "...", "messages": [...] },
  "response_json": {
    "message": {
      "id": "msg_...", "model": "...", "stop_reason": "end_turn",
      "content": { "text": "..." },
      "usage": { "input_tokens": 206, "output_tokens": 79 }
    }
  }
}
```

**Examples:**

```bash
# Single file → logs/2026-05-08_parsed.jsonl
deep-ai-analysis clear-req-resp logs/2026-05-08.jsonl

# Custom output path
deep-ai-analysis clear-req-resp logs/2026-05-08.jsonl -o parsed.jsonl

# Directory — processes all .jsonl files
deep-ai-analysis clear-req-resp logs/
```

---

### `web-server`

Starts a local HTTP server that serves a browser-based viewer for Claude Code session logs. No file upload — the server reads directly from `~/.claude/projects`.

```
Usage: deep-ai-analysis web-server [OPTIONS]

Options:
  --port INTEGER          Port for the viewer API server.  [default: 7789]
  --projects-dir PATH     Path to the Claude Code projects directory.
                          [default: ~/.claude/projects]
  --req-resp-dir PATH     Directory containing raw HTTP request/response JSONL files.
                          [default: ~/.deep-ai-analysis/raw-req-resp]
  --help                  Show this message and exit.
```

**Usage:**

```bash
# Start the API server
deep-ai-analysis web-server

# Then open viewer/index.html in your browser
open viewer/index.html
```

The viewer lets you:
- Browse all Claude Code sessions by project
- View main session conversation (user messages, assistant responses, tool calls)
- Inspect each subagent in a dedicated tab
- See token usage statistics per session

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
export http_proxy=http://127.0.0.1:7788
export https_proxy=http://127.0.0.1:7788
```

## Log Format

### Raw proxy log (`proxy` command)

Written to `logs/YYYY-MM-DD.jsonl` — one JSON object per line.

**SSE (streaming) request:**

```json
{
  "timestamp": "2026-05-08T10:31:00.000000+00:00",
  "domain": "mcli.sankuai.com",
  "method": "POST",
  "url": "https://mcli.sankuai.com/v1/messages",
  "request": {
    "headers": { "Content-Type": "application/json" },
    "body": "{\"model\": \"...\", \"messages\": [...]}"
  },
  "response": {
    "status": 200,
    "headers": { "content-type": "text/event-stream" },
    "body": "event: message_start\ndata: {...}\n\n..."
  },
  "is_sse": true,
  "sse_events": ["event: message_start\ndata: {...}", "..."]
}
```

> Note: `Authorization` headers are excluded from `request.headers` to prevent token leakage.

### Parsed log (`clear-req-resp` command)

See the [`clear-req-resp`](#clear-req-resp) section above for the parsed output format.

**Query parsed logs with `jq`:**

```bash
# Show all session IDs
jq -r '.claude_session_id' logs/2026-05-08_parsed.jsonl | sort -u

# Show model usage
jq -r '.response_json.message.model' logs/2026-05-08_parsed.jsonl | sort | uniq -c

# Show token usage per request
jq '{url, usage: .response_json.message.usage}' logs/2026-05-08_parsed.jsonl
```
