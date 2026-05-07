#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { Command } = require('commander');

const DEFAULT_LOG_DIR = path.join(process.cwd(), 'logs');

// ── Helpers ──────────────────────────────────────────────────────────────────

function todayDate() {
  return new Date().toISOString().slice(0, 10);
}

/** Read all log entries from a given YYYY-MM-DD.jsonl file. Returns [] if not found. */
function readLogFile(logDir, date) {
  const filePath = path.join(logDir, `${date}.jsonl`);
  if (!fs.existsSync(filePath)) return [];
  const lines = fs.readFileSync(filePath, 'utf8').split('\n').filter(Boolean);
  return lines.map(l => {
    try { return JSON.parse(l); } catch { return null; }
  }).filter(Boolean);
}

/** Get all .jsonl dates in logDir, sorted descending. */
function allDates(logDir) {
  if (!fs.existsSync(logDir)) return [];
  return fs.readdirSync(logDir)
    .filter(f => /^\d{4}-\d{2}-\d{2}\.jsonl$/.test(f))
    .map(f => f.replace('.jsonl', ''))
    .sort()
    .reverse();
}

/** Get last N calendar dates (YYYY-MM-DD strings). */
function lastNDates(n) {
  const dates = [];
  for (let i = 0; i < n; i++) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    dates.push(d.toISOString().slice(0, 10));
  }
  return dates;
}

/** Find a log entry by full or prefix ID, searching all available dates. */
function findEntries(logDir, idPrefix) {
  const dates = allDates(logDir);
  const matches = [];
  for (const date of dates) {
    const entries = readLogFile(logDir, date);
    for (const e of entries) {
      if (e.id && e.id.startsWith(idPrefix)) {
        matches.push(e);
      }
    }
    if (matches.length > 1) break; // early exit for multi-match detection
  }
  // If still looking for more matches after first file, keep searching
  if (matches.length === 1) return matches; // exact or single prefix match
  // Re-search all for completeness when prefix is ambiguous
  const all = [];
  for (const date of dates) {
    for (const e of readLogFile(logDir, date)) {
      if (e.id && e.id.startsWith(idPrefix)) all.push(e);
    }
  }
  return all;
}

function formatTime(isoStr) {
  return isoStr ? isoStr.replace('T', ' ').replace(/\.\d+Z$/, 'Z') : '-';
}

function printSummaryRow(e) {
  const id = (e.id || '').slice(0, 8);
  const time = formatTime(e.timestamp);
  const method = (e.method || '-').padEnd(6);
  const pathStr = (e.path || '-').padEnd(30);
  const status = String(e.status_code || '-').padEnd(6);
  const duration = e.duration_ms != null ? `${e.duration_ms}ms` : '-';
  console.log(`${id}  ${time}  ${method}  ${pathStr}  ${status}  ${duration}`);
}

// ── Program ───────────────────────────────────────────────────────────────────

const program = new Command();
program
  .name('viewer')
  .description('Claude Code request log viewer')
  .option('--log-dir <dir>', 'Log directory', DEFAULT_LOG_DIR);

// ── list ─────────────────────────────────────────────────────────────────────
program
  .command('list')
  .description('List recorded requests')
  .option('--date <date>', 'Date to list (YYYY-MM-DD, default: today)')
  .action((cmdOpts) => {
    const logDir = program.opts().logDir;
    const date = cmdOpts.date || todayDate();
    const entries = readLogFile(logDir, date);
    if (entries.length === 0) {
      console.log(`No requests found for ${date}`);
      process.exit(0);
    }
    console.log(`${'ID'.padEnd(10)}  ${'TIME'.padEnd(23)}  ${'METHOD'.padEnd(6)}  ${'PATH'.padEnd(30)}  ${'STATUS'.padEnd(6)}  DURATION`);
    console.log('-'.repeat(100));
    for (const e of entries) printSummaryRow(e);
  });

// ── show ──────────────────────────────────────────────────────────────────────
program
  .command('show <id>')
  .description('Show full log entry by ID or prefix')
  .action((id, _cmdOpts) => {
    const logDir = program.opts().logDir;
    const matches = findEntries(logDir, id);
    if (matches.length === 0) {
      console.error(`Request ${id} not found`);
      process.exit(1);
    }
    if (matches.length === 1) {
      console.log(JSON.stringify(matches[0], null, 2));
      return;
    }
    // Multiple matches — list them
    console.error(`Multiple requests match prefix "${id}". Please specify a longer prefix:`);
    for (const e of matches) {
      console.error(`  ${e.id}  ${formatTime(e.timestamp)}  ${e.method}  ${e.path}`);
    }
    process.exit(1);
  });

// ── response ──────────────────────────────────────────────────────────────────
program
  .command('response <id>')
  .description('Print the assembled response text for a request')
  .action((id, _cmdOpts) => {
    const logDir = program.opts().logDir;
    const matches = findEntries(logDir, id);
    if (matches.length === 0) {
      console.error(`Request ${id} not found`);
      process.exit(1);
    }
    if (matches.length > 1) {
      console.error(`Multiple requests match prefix "${id}". Please be more specific.`);
      process.exit(1);
    }
    const e = matches[0];
    if (e.response_assembled != null) {
      process.stdout.write(e.response_assembled + '\n');
      return;
    }
    // Non-streaming: extract text from response_body.content
    const content = e.response_body?.content;
    if (Array.isArray(content)) {
      const text = content.filter(b => b.type === 'text').map(b => b.text).join('');
      process.stdout.write(text + '\n');
    } else if (typeof content === 'string') {
      process.stdout.write(content + '\n');
    } else {
      console.error('No response text found in this entry.');
      process.exit(1);
    }
  });

// ── search ────────────────────────────────────────────────────────────────────
program
  .command('search <keyword>')
  .description('Search log content across the last 7 days')
  .option('--in <scope>', 'Scope: request | response | all (default: all)', 'all')
  .option('--days <n>', 'Number of days to search', '7')
  .action((keyword, cmdOpts) => {
    const logDir = program.opts().logDir;
    const days = parseInt(cmdOpts.days, 10);
    const scope = cmdOpts.in;
    const dates = lastNDates(days);
    const kw = keyword.toLowerCase();
    let found = 0;

    for (const date of dates) {
      const entries = readLogFile(logDir, date);
      for (const e of entries) {
        let hit = false;
        const reqStr = JSON.stringify(e.request_body || '').toLowerCase();
        const resStr = JSON.stringify(
          e.response_assembled ?? e.response_body ?? ''
        ).toLowerCase();

        if (scope === 'request') hit = reqStr.includes(kw);
        else if (scope === 'response') hit = resStr.includes(kw);
        else hit = reqStr.includes(kw) || resStr.includes(kw);

        if (hit) {
          printSummaryRow(e);
          found++;
        }
      }
    }
    if (found === 0) {
      console.log(`No matches found for "${keyword}" in the last ${days} days.`);
    } else {
      console.log(`\n${found} match(es) found.`);
    }
  });

program.parse(process.argv);
