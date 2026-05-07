'use strict';

const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

class Logger {
  constructor(logDir, redactKeys) {
    this.logDir = logDir;
    this.redactKeys = redactKeys;
    fs.mkdirSync(logDir, { recursive: true });
  }

  /** Build the initial log entry from an incoming request. */
  generateLogEntry(req, bodyBuffer) {
    let requestBody = null;
    if (bodyBuffer && bodyBuffer.length > 0) {
      try {
        requestBody = JSON.parse(bodyBuffer.toString('utf8'));
      } catch {
        requestBody = bodyBuffer.toString('utf8');
      }
    }

    const headers = this._processHeaders(req.headers);
    const entry = {
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      method: req.method,
      path: req.url,
      request_headers: headers,
      request_body: requestBody,
      truncated: bodyBuffer ? bodyBuffer.length > 1024 * 1024 : false,
    };
    return entry;
  }

  /** Append non-streaming response fields to a log entry, then persist. */
  finalizeNonStream(entry, statusCode, responseHeaders, responseBodyBuffer, startTime) {
    let responseBody = null;
    if (responseBodyBuffer && responseBodyBuffer.length > 0) {
      try {
        responseBody = JSON.parse(responseBodyBuffer.toString('utf8'));
      } catch {
        responseBody = responseBodyBuffer.toString('utf8');
      }
    }
    entry.status_code = statusCode;
    entry.response_headers = Object.fromEntries(
      Object.entries(responseHeaders).map(([k, v]) => [k, v])
    );
    entry.response_body = responseBody;
    entry.duration_ms = Date.now() - startTime;
    this._write(entry);
  }

  /** Append streaming response fields to a log entry, then persist. */
  finalizeStream(entry, statusCode, responseHeaders, chunks, startTime) {
    const rawChunks = chunks.map(c => c.toString('utf8'));
    const assembled = this._assembleSSE(rawChunks);

    entry.status_code = statusCode;
    entry.response_headers = Object.fromEntries(
      Object.entries(responseHeaders).map(([k, v]) => [k, v])
    );
    entry.response_type = 'stream';
    entry.stream_chunks = rawChunks;
    entry.response_assembled = assembled;
    entry.duration_ms = Date.now() - startTime;
    this._write(entry);
  }

  /** Persist a log entry to today's JSONL file. */
  _write(entry) {
    const date = new Date().toISOString().slice(0, 10);
    const filePath = path.join(this.logDir, `${date}.jsonl`);
    const line = JSON.stringify(entry) + '\n';
    fs.appendFileSync(filePath, line, 'utf8');
    // Restrict file permissions to owner-only (600)
    try { fs.chmodSync(filePath, 0o600); } catch {}
  }

  /** Strip API keys from headers if redaction is enabled. */
  _processHeaders(headers) {
    const result = {};
    for (const [k, v] of Object.entries(headers)) {
      if (this.redactKeys && (k.toLowerCase() === 'x-api-key' || k.toLowerCase() === 'authorization')) {
        result[k] = '***REDACTED***';
      } else {
        result[k] = v;
      }
    }
    return result;
  }

  /**
   * Reconstruct the full assistant text from SSE chunks.
   * Handles Anthropic's streaming format:
   *   data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"..."}}
   */
  _assembleSSE(rawChunks) {
    const parts = [];
    for (const chunk of rawChunks) {
      for (const line of chunk.split('\n')) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6).trim();
        if (payload === '[DONE]') continue;
        try {
          const obj = JSON.parse(payload);
          // Anthropic messages API streaming
          if (obj.type === 'content_block_delta' && obj.delta?.type === 'text_delta') {
            parts.push(obj.delta.text);
          } else if (obj.type === 'content_block_delta' && obj.delta?.type === 'input_json_delta') {
            parts.push(obj.delta.partial_json ?? '');
          }
        } catch {}
      }
    }
    return parts.join('');
  }

  /** Delete log files older than `days` days. */
  cleanup(days) {
    const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
    const files = fs.readdirSync(this.logDir).filter(f => f.endsWith('.jsonl'));
    const deleted = [];
    for (const file of files) {
      const match = file.match(/^(\d{4}-\d{2}-\d{2})\.jsonl$/);
      if (!match) continue;
      const fileDate = new Date(match[1]).getTime();
      if (fileDate < cutoff) {
        fs.unlinkSync(path.join(this.logDir, file));
        deleted.push(file);
      }
    }
    return deleted;
  }
}

module.exports = Logger;
