#!/usr/bin/env node
'use strict';

const http = require('http');
const https = require('https');
const path = require('path');
const { Command } = require('commander');
const Logger = require('./logger');
const { startWebServer } = require('./web-server');

const program = new Command();
program
  .name('proxy')
  .description('Claude Code request interceptor proxy')
  .option('-p, --port <port>', 'Local port to listen on', '9999')
  .option('--log-dir <dir>', 'Directory to write log files', path.join(process.cwd(), 'logs'))
  .option('--redact-keys', 'Redact API keys from logs', false)
  .option('--cleanup', 'Delete old log files and exit')
  .option('--days <n>', 'Number of days to keep when using --cleanup', '7')
  .option('--web', 'Also start the web UI server', false)
  .option('--web-port <port>', 'Port for the web UI (requires --web)', '9998')
  .parse(process.argv);

const opts = program.opts();

// --cleanup mode: delete old logs and exit
if (opts.cleanup) {
  const logger = new Logger(opts.logDir, false);
  const deleted = logger.cleanup(parseInt(opts.days, 10));
  if (deleted.length === 0) {
    console.log(`No log files older than ${opts.days} days found.`);
  } else {
    console.log(`Deleted ${deleted.length} file(s):`);
    deleted.forEach(f => console.log(`  ${f}`));
  }
  process.exit(0);
}

const PORT = parseInt(opts.port, 10);
const logger = new Logger(opts.logDir, opts.redactKeys);

const UPSTREAM_HOST = 'api.anthropic.com';

const server = http.createServer((req, res) => {
  const startTime = Date.now();

  // Collect the incoming request body
  const bodyChunks = [];
  req.on('data', chunk => bodyChunks.push(chunk));
  req.on('end', () => {
    const bodyBuffer = Buffer.concat(bodyChunks);
    const entry = logger.generateLogEntry(req, bodyBuffer);

    // Build upstream request options
    const upstreamOptions = {
      hostname: UPSTREAM_HOST,
      port: 443,
      path: req.url,
      method: req.method,
      headers: {
        ...req.headers,
        host: UPSTREAM_HOST,  // override the host header
      },
    };

    const upstreamReq = https.request(upstreamOptions, (upstreamRes) => {
      const isStream = (upstreamRes.headers['content-type'] || '').includes('text/event-stream');

      // Forward status code and headers to client immediately
      res.writeHead(upstreamRes.statusCode, upstreamRes.headers);

      if (isStream) {
        const responseChunks = [];
        upstreamRes.on('data', chunk => {
          res.write(chunk);           // forward to client immediately
          responseChunks.push(chunk); // accumulate for logging
        });
        upstreamRes.on('end', () => {
          res.end();
          logger.finalizeStream(entry, upstreamRes.statusCode, upstreamRes.headers, responseChunks, startTime);
        });
      } else {
        const responseChunks = [];
        upstreamRes.on('data', chunk => {
          res.write(chunk);
          responseChunks.push(chunk);
        });
        upstreamRes.on('end', () => {
          res.end();
          const responseBodyBuffer = Buffer.concat(responseChunks);
          logger.finalizeNonStream(entry, upstreamRes.statusCode, upstreamRes.headers, responseBodyBuffer, startTime);
        });
      }
    });

    upstreamReq.on('error', (err) => {
      console.error(`[proxy] Upstream error for ${req.method} ${req.url}: ${err.message}`);
      if (!res.headersSent) {
        res.writeHead(502, { 'content-type': 'application/json' });
      }
      res.end(JSON.stringify({ error: 'Bad Gateway', message: err.message }));
    });

    // Write request body to upstream
    if (bodyBuffer.length > 0) {
      upstreamReq.write(bodyBuffer);
    }
    upstreamReq.end();
  });
});

// Port conflict detection
server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`Error: Port ${PORT} is already in use. Choose a different port with --port.`);
  } else {
    console.error(`Server error: ${err.message}`);
  }
  process.exit(1);
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[proxy] Listening on http://localhost:${PORT}`);
  console.log(`[proxy] Forwarding to https://${UPSTREAM_HOST}`);
  console.log(`[proxy] Logging to ${opts.logDir}`);
  if (opts.redactKeys) {
    console.log('[proxy] API key redaction: ENABLED');
  }
  console.log(`\nTo intercept Claude Code traffic, run:`);
  console.log(`  export ANTHROPIC_BASE_URL=http://localhost:${PORT}`);

  if (opts.web) {
    startWebServer(opts.logDir, parseInt(opts.webPort, 10));
  }
});
