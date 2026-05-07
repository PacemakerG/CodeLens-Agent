# Claude Code Request Interceptor

Intercepts and logs all raw HTTP requests and responses between Claude Code and the Anthropic API, using a local reverse proxy.

## How It Works

Claude Code's Anthropic SDK respects the `ANTHROPIC_BASE_URL` environment variable. This tool starts a local HTTP proxy at that URL, records every request/response (including streaming SSE), then forwards the traffic to `https://api.anthropic.com` transparently.

## Quick Start

### 1. Install

```bash
npm install
```

### 2. Start the Proxy

```bash
node src/proxy.js
# or: npm run proxy
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--port <n>` | `9999` | Local port to listen on |
| `--log-dir <path>` | `./logs` | Directory to write JSONL log files |
| `--redact-keys` | off | Replace `x-api-key` / `authorization` values with `***REDACTED***` |
| `--cleanup --days <n>` | — | Delete log files older than N days, then exit |

### 3. Configure Claude Code

In a new terminal (before running Claude Code):

```bash
export ANTHROPIC_BASE_URL=http://localhost:9999
claude  # or however you launch Claude Code
```

To stop intercepting:

```bash
unset ANTHROPIC_BASE_URL
```

### 4. View Logs (Web UI)

Open a browser to view requests visually:

```bash
# Start proxy + Web UI together (recommended)
node src/proxy.js --web
# Then open: http://localhost:9998

# Or start Web UI standalone (reads existing logs)
node src/web-server.js
# or: npm run web
```

Web UI options:

| Flag | Default | Description |
|------|---------|-------------|
| `--web` | off | Enable Web UI when starting the proxy |
| `--web-port <n>` | `9998` | Port for the Web UI |
| `--log-dir <path>` | `./logs` | Log directory to read (standalone mode) |

The Web UI provides:
- Date selector to browse logs by day
- Searchable request list with method badges, status codes, and duration
- Detail panel with Request Headers / Request Body / Response Headers / Response tabs
- JSON syntax highlighting
- Streaming response display (assembled text + expandable raw SSE chunks)
- One-click copy for any content section

### 5. View Logs (CLI)

```bash
# List today's requests
node src/viewer.js list

# List requests for a specific date
node src/viewer.js list --date 2024-01-15

# Show full details of a request (full UUID or first 4+ chars)
node src/viewer.js show <id-or-prefix>

# Print just the AI response text
node src/viewer.js response <id-or-prefix>

# Search across the last 7 days
node src/viewer.js search "keyword"
node src/viewer.js search "keyword" --in request
node src/viewer.js search "keyword" --in response
```

## Log Format

Each line in a `logs/YYYY-MM-DD.jsonl` file is a JSON object:

```json
{
  "id": "uuid-v4",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "method": "POST",
  "path": "/v1/messages",
  "request_headers": { "x-api-key": "sk-..." },
  "request_body": { "model": "...", "messages": [...] },
  "status_code": 200,
  "response_headers": { "content-type": "text/event-stream" },
  "response_type": "stream",
  "stream_chunks": ["data: {...}\n\n", "..."],
  "response_assembled": "Full assistant reply text here",
  "duration_ms": 3421,
  "truncated": false
}
```

## Security Notes

- Log files are created with `600` permissions (owner read/write only).
- Use `--redact-keys` if you share log files with others.
- Log files contain full conversation content and API keys — handle with care.
- Run `node src/proxy.js --cleanup --days 7` regularly to limit disk usage.
