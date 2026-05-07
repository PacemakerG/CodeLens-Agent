#!/usr/bin/env node
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const { Command } = require('commander');

const program = new Command();
program
  .name('web-server')
  .description('Claude Code request log web viewer')
  .option('--web-port <port>', 'Port for the web UI', '9998')
  .option('--log-dir <dir>', 'Log directory to read from', path.join(process.cwd(), 'logs'))
  .parse(process.argv);

const opts = program.opts();

/**
 * Start the web server. Returns the http.Server instance.
 * logDir and webPort can be passed directly (for proxy.js integration).
 */
function startWebServer(logDir, webPort) {
  logDir = logDir || opts.logDir;
  webPort = webPort || parseInt(opts.webPort, 10);

  const PUBLIC_DIR = path.join(__dirname, '..', 'public');

  const MIME = {
    '.html': 'text/html; charset=utf-8',
    '.js':   'application/javascript; charset=utf-8',
    '.css':  'text/css; charset=utf-8',
  };

  // ── Helpers ────────────────────────────────────────────────────────────────

  function readLogFile(date) {
    const filePath = path.join(logDir, `${date}.jsonl`);
    if (!fs.existsSync(filePath)) return [];
    return fs.readFileSync(filePath, 'utf8')
      .split('\n')
      .filter(Boolean)
      .map(l => { try { return JSON.parse(l); } catch { return null; } })
      .filter(Boolean);
  }

  function jsonResponse(res, statusCode, data) {
    const body = JSON.stringify(data);
    res.writeHead(statusCode, {
      'Content-Type': 'application/json; charset=utf-8',
      'Content-Length': Buffer.byteLength(body),
    });
    res.end(body);
  }

  function parseUrl(urlStr) {
    const base = `http://localhost`;
    return new URL(urlStr, base);
  }

  // ── Route handlers ─────────────────────────────────────────────────────────

  function handleDates(res) {
    if (!fs.existsSync(logDir)) return jsonResponse(res, 200, []);
    const dates = fs.readdirSync(logDir)
      .filter(f => /^\d{4}-\d{2}-\d{2}\.jsonl$/.test(f))
      .map(f => f.replace('.jsonl', ''))
      .sort()
      .reverse();
    jsonResponse(res, 200, dates);
  }

  function handleListRequests(url, res) {
    const date = url.searchParams.get('date');
    const q = (url.searchParams.get('q') || '').toLowerCase().trim();
    if (!date) return jsonResponse(res, 400, { error: 'date parameter required' });

    const entries = readLogFile(date);
    let filtered = entries;
    if (q) {
      filtered = entries.filter(e => {
        const reqStr = JSON.stringify(e.request_body || '').toLowerCase();
        const resStr = JSON.stringify(e.response_assembled ?? e.response_body ?? '').toLowerCase();
        return reqStr.includes(q) || resStr.includes(q);
      });
    }

    const summaries = filtered.map(e => ({
      id:            e.id,
      timestamp:     e.timestamp,
      method:        e.method,
      path:          e.path,
      status_code:   e.status_code,
      duration_ms:   e.duration_ms,
      response_type: e.response_type || 'json',
    }));
    jsonResponse(res, 200, summaries);
  }

  function handleGetRequest(pathname, url, res) {
    // pathname: /api/requests/<id>
    const id = pathname.replace('/api/requests/', '');
    const date = url.searchParams.get('date');
    if (!date) return jsonResponse(res, 400, { error: 'date parameter required' });

    const entries = readLogFile(date);
    const entry = entries.find(e => e.id === id);
    if (!entry) return jsonResponse(res, 404, { error: 'Not found' });
    jsonResponse(res, 200, entry);
  }

  function handleStatic(pathname, res) {
    // Map / → index.html
    const filePath = pathname === '/'
      ? path.join(PUBLIC_DIR, 'index.html')
      : path.join(PUBLIC_DIR, pathname.slice(1));

    // Security: ensure resolved path is within PUBLIC_DIR
    const resolved = path.resolve(filePath);
    if (!resolved.startsWith(path.resolve(PUBLIC_DIR))) {
      res.writeHead(403); res.end('Forbidden'); return;
    }

    if (!fs.existsSync(resolved)) {
      res.writeHead(404); res.end('Not found'); return;
    }

    const ext = path.extname(resolved);
    const contentType = MIME[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    fs.createReadStream(resolved).pipe(res);
  }

  // ── Server ────────────────────────────────────────────────────────────────

  const server = http.createServer((req, res) => {
    // CORS for local dev convenience
    res.setHeader('Access-Control-Allow-Origin', '*');

    const url = parseUrl(req.url);
    const pathname = url.pathname;

    if (pathname === '/api/dates') {
      return handleDates(res);
    }
    if (pathname === '/api/requests' && req.method === 'GET') {
      return handleListRequests(url, res);
    }
    if (pathname.startsWith('/api/requests/') && req.method === 'GET') {
      return handleGetRequest(pathname, url, res);
    }
    // Static files
    return handleStatic(pathname, res);
  });

  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.error(`[web] Error: Port ${webPort} is already in use. Choose a different port with --web-port.`);
    } else {
      console.error(`[web] Server error: ${err.message}`);
    }
    process.exit(1);
  });

  server.listen(webPort, '127.0.0.1', () => {
    console.log(`[web] UI available at http://localhost:${webPort}`);
    console.log(`[web] Reading logs from ${logDir}`);
  });

  return server;
}

// Run standalone when executed directly
if (require.main === module) {
  startWebServer();
}

module.exports = { startWebServer };
