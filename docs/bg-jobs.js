/* bg-jobs.js — shared background-job client + status banner.
 *
 * The local catalogue editor server runs the slow production steps (combined
 * STL render, adjusted bake, "move to production", and the agent flesh-out) as
 * background jobs. This module fires those jobs, shows a status banner pinned
 * to the top of the page for any ongoing processing, and runs a completion
 * callback when each finishes — so the author can keep working on other signs
 * (or even switch pages) while a job runs.
 *
 * Public API (window.BGJobs):
 *   BGJobs.start(kind, payload, {label, onStart, onDone, onError})
 *       -> Promise<jobId>. onDone(result, job) / onError(message, job).
 *   BGJobs.refresh()  -> force an immediate poll (e.g. on page load).
 *   BGJobs.activeCount() -> number of queued/running jobs known to this page.
 */
(function () {
  'use strict';
  if (window.BGJobs) return;

  var POLL_MS = 1500;          // poll cadence while jobs are active
  var DONE_VISIBLE_MS = 9000;  // keep finished chips on screen this long
  var tracked = {};            // jobId -> {onDone, onError, fired}
  var dismissed = {};          // jobId -> true (user closed the chip)
  var lastJobs = [];           // last server snapshot
  var pollTimer = null;
  var barEl = null;
  var listEl = null;
  var styleInjected = false;

  function injectStyle() {
    if (styleInjected) return;
    styleInjected = true;
    var css = [
      '#bgjobs-bar{position:fixed;top:0;left:0;right:0;z-index:99999;',
      'display:none;flex-wrap:wrap;gap:8px;align-items:center;',
      'padding:8px 14px;background:rgba(18,20,24,.97);',
      'border-bottom:1px solid #41502a;box-shadow:0 2px 10px rgba(0,0,0,.45);',
      'font:13px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;',
      'color:#e7ead0;backdrop-filter:blur(4px)}',
      '#bgjobs-bar.show{display:flex}',
      '#bgjobs-bar .bgj-title{font-weight:700;color:#b7d36a;margin-right:4px;',
      'white-space:nowrap}',
      '#bgjobs-bar .bgj-chip{display:inline-flex;align-items:center;gap:7px;',
      'padding:4px 10px;border-radius:999px;background:#222a16;',
      'border:1px solid #41502a;max-width:46ch}',
      '#bgjobs-bar .bgj-chip.done{border-color:#3a6b34;background:#1c2a18}',
      '#bgjobs-bar .bgj-chip.error{border-color:#7a3030;background:#2a1818}',
      '#bgjobs-bar .bgj-lbl{white-space:nowrap;overflow:hidden;',
      'text-overflow:ellipsis;font-weight:600}',
      '#bgjobs-bar .bgj-st{color:#9aa789;white-space:nowrap}',
      '#bgjobs-bar .bgj-chip.error .bgj-st{color:#e88}',
      '#bgjobs-bar .bgj-chip.done .bgj-st{color:#a7d39a}',
      '#bgjobs-bar .bgj-x{cursor:pointer;color:#8a937c;font-weight:700;',
      'margin-left:2px;padding:0 2px}',
      '#bgjobs-bar .bgj-x:hover{color:#fff}',
      '@keyframes bgj-spin{to{transform:rotate(360deg)}}',
      '#bgjobs-bar .bgj-spin{width:13px;height:13px;border-radius:50%;',
      'border:2px solid #4a5a2e;border-top-color:#b7d36a;display:inline-block;',
      'animation:bgj-spin .8s linear infinite;flex:none}',
      '#bgjobs-bar .bgj-ic{flex:none;font-size:14px}'
    ].join('');
    var s = document.createElement('style');
    s.id = 'bgjobs-style';
    s.textContent = css;
    document.head.appendChild(s);
  }

  function ensureBar() {
    if (barEl) return;
    injectStyle();
    barEl = document.createElement('div');
    barEl.id = 'bgjobs-bar';
    var title = document.createElement('span');
    title.className = 'bgj-title';
    title.textContent = '⚙ Background';
    listEl = document.createElement('span');
    listEl.style.display = 'contents';
    barEl.appendChild(title);
    barEl.appendChild(listEl);
    document.body.appendChild(barEl);
  }

  function esc(t) {
    return String(t == null ? '' : t)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function statusText(job) {
    if (job.status === 'queued') return 'queued…';
    if (job.status === 'running') return 'processing…';
    if (job.status === 'done') return 'done ✓';
    if (job.status === 'error') return 'failed: ' + (job.error || 'error');
    return job.status;
  }

  function visibleJobs() {
    var now = Date.now();
    return lastJobs.filter(function (j) {
      if (dismissed[j.id]) return false;
      if (j.status === 'queued' || j.status === 'running') return true;
      // keep finished chips briefly so the author sees the outcome
      var fin = j.finishedAt ? j.finishedAt * 1000 : now;
      return (now - fin) < DONE_VISIBLE_MS;
    });
  }

  function render() {
    ensureBar();
    var jobs = visibleJobs();
    if (!jobs.length) {
      barEl.classList.remove('show');
      listEl.innerHTML = '';
      return;
    }
    barEl.classList.add('show');
    listEl.innerHTML = jobs.map(function (j) {
      var cls = 'bgj-chip' + (j.status === 'done' ? ' done'
        : j.status === 'error' ? ' error' : '');
      var icon = (j.status === 'queued' || j.status === 'running')
        ? '<span class="bgj-spin"></span>'
        : '<span class="bgj-ic">' + (j.status === 'done' ? '✓' : '⚠') + '</span>';
      var x = (j.status === 'done' || j.status === 'error')
        ? '<span class="bgj-x" data-bgj-x="' + esc(j.id) + '" title="dismiss">×</span>'
        : '';
      return '<span class="' + cls + '" title="' + esc(j.label) + '">' + icon +
        '<span class="bgj-lbl">' + esc(j.label) + '</span>' +
        '<span class="bgj-st">' + esc(statusText(j)) + '</span>' + x + '</span>';
    }).join('');
    Array.prototype.forEach.call(listEl.querySelectorAll('[data-bgj-x]'), function (el) {
      el.addEventListener('click', function () {
        dismissed[el.getAttribute('data-bgj-x')] = true;
        render();
      });
    });
  }

  function fireIfComplete(job) {
    var t = tracked[job.id];
    if (!t || t.fired) return;
    if (job.status !== 'done' && job.status !== 'error') return;
    t.fired = true;
    // fetch the full record (with result) before invoking the callback
    fetch('/api/job/status?id=' + encodeURIComponent(job.id), { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var full = (j && j.job) ? j.job : job;
        if (full.status === 'done') {
          if (t.onDone) { try { t.onDone(full.result || {}, full); } catch (e) { console.error(e); } }
        } else if (t.onError) {
          try { t.onError(full.error || 'failed', full); } catch (e) { console.error(e); }
        }
      })
      .catch(function () {
        if (job.status === 'error' && t.onError) t.onError(job.error || 'failed', job);
      });
  }

  function hasActivity() {
    var now = Date.now();
    return lastJobs.some(function (j) {
      if (j.status === 'queued' || j.status === 'running') return true;
      // keep polling a touch longer so finished chips fade and callbacks fire
      if (tracked[j.id] && !tracked[j.id].fired) return true;
      var fin = j.finishedAt ? j.finishedAt * 1000 : now;
      return (now - fin) < DONE_VISIBLE_MS;
    });
  }

  function poll() {
    return fetch('/api/job/list', { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        lastJobs = (j && j.jobs) ? j.jobs : [];
        lastJobs.forEach(fireIfComplete);
        render();
      })
      .catch(function () { /* server probably not running; stay quiet */ })
      .then(scheduleNext);
  }

  function scheduleNext() {
    if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
    if (hasActivity()) {
      pollTimer = setTimeout(poll, POLL_MS);
    } else {
      render();
    }
  }

  function startPolling() {
    if (pollTimer) return;
    pollTimer = setTimeout(poll, 0);
  }

  window.BGJobs = {
    start: function (kind, payload, opts) {
      opts = opts || {};
      var body = { kind: kind, label: opts.label || kind, payload: payload || {} };
      return fetch('/api/job/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (!j || !j.ok) throw new Error((j && j.error) || 'could not start job');
          tracked[j.jobId] = { onDone: opts.onDone, onError: opts.onError, fired: false };
          if (opts.onStart) { try { opts.onStart(j.jobId); } catch (e) { /* noop */ } }
          ensureBar();
          startPolling();
          return j.jobId;
        });
    },
    refresh: function () { startPolling(); },
    activeCount: function () {
      return lastJobs.filter(function (j) {
        return j.status === 'queued' || j.status === 'running';
      }).length;
    }
  };

  // On load, pick up any jobs already running (e.g. started from the other
  // page) so the banner reflects all ongoing processing.
  function boot() { ensureBar(); startPolling(); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
