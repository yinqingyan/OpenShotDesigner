#!/usr/bin/env python3
"""Build a self-contained, offline confirmation UI for Chinese review."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOCALIZATION = ROOT / "localization" / "zh-CN"
DRAFTS = LOCALIZATION / "zh-cn-drafts.json"
TERMS = LOCALIZATION / "zh-cn-terminology.json"
OUTPUT = LOCALIZATION / "zh-CN-review.html"


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Open Shot Designer — 简体中文逐条确认</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0e1117;
      --panel: #161b23;
      --panel-2: #1c232d;
      --line: #303947;
      --ink: #f3f5f7;
      --muted: #9ca8b6;
      --blue: #58a6ff;
      --green: #3fb950;
      --amber: #d29922;
      --red: #f85149;
      --violet: #bc8cff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: radial-gradient(circle at 70% -20%, #1a2c42 0, transparent 36%), var(--bg);
      color: var(--ink);
      font: 14px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
    }
    button, input, select, textarea { font: inherit; }
    button {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 12px;
      color: var(--ink);
      background: var(--panel-2);
      cursor: pointer;
    }
    button:hover:not(:disabled) { border-color: #65758b; background: #242d39; }
    button:disabled { opacity: .45; cursor: not-allowed; }
    button.primary { background: #1f6feb; border-color: #388bfd; }
    button.confirm { background: #238636; border-color: #2ea043; }
    button.warning { color: #ffd28a; border-color: #80611a; background: #34270d; }
    button.violet { color: #e5d1ff; border-color: #805ad5; background: #291d3d; }
    .shell { max-width: 1240px; margin: 0 auto; padding: 28px 22px 48px; }
    .topbar { display: flex; gap: 18px; align-items: flex-start; justify-content: space-between; }
    h1 { margin: 0; font-size: 24px; letter-spacing: .01em; }
    .subtitle { margin-top: 5px; color: var(--muted); }
    .phase {
      display: inline-flex; gap: 7px; align-items: center; margin-top: 12px;
      padding: 5px 10px; border-radius: 999px; background: #27200e; color: #f2cc60; font-size: 12px;
    }
    .phase.ready { background: #13351c; color: #7ee787; }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
    .progress { margin-top: 20px; }
    .progress-track { height: 8px; border-radius: 5px; overflow: hidden; background: #252d38; }
    .progress-fill { width: 0; height: 100%; background: linear-gradient(90deg, #1f6feb, #3fb950); transition: width .2s; }
    .metrics { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 10px; margin-top: 12px; }
    .metric { border: 1px solid var(--line); background: rgba(22, 27, 35, .88); border-radius: 10px; padding: 10px 12px; }
    .metric strong { display: block; font-size: 20px; }
    .metric span { color: var(--muted); font-size: 12px; }
    .filters {
      display: grid; grid-template-columns: 1.5fr 1fr .8fr .9fr; gap: 10px;
      margin: 18px 0 12px;
    }
    input, select, textarea {
      width: 100%; border: 1px solid var(--line); border-radius: 8px;
      background: #11161d; color: var(--ink); padding: 10px 11px; outline: none;
    }
    input:focus, select:focus, textarea:focus { border-color: var(--blue); box-shadow: 0 0 0 2px #1f6feb33; }
    .workspace { display: grid; grid-template-columns: minmax(0, 1fr) 290px; gap: 14px; }
    .card { border: 1px solid var(--line); border-radius: 12px; background: rgba(22, 27, 35, .94); }
    .card-head { display: flex; justify-content: space-between; gap: 12px; padding: 13px 16px; border-bottom: 1px solid var(--line); }
    .badge { display: inline-block; border-radius: 999px; padding: 2px 8px; background: #252d38; color: var(--muted); font-size: 12px; }
    .card-body { padding: 16px; }
    .label { color: var(--muted); font-size: 12px; margin-bottom: 5px; }
    .source { margin-bottom: 18px; }
    pre {
      margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; font: 15px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace;
    }
    textarea { min-height: 140px; resize: vertical; font-size: 17px; line-height: 1.65; }
    .translation-wrap { position: relative; }
    .char-count { position: absolute; right: 10px; bottom: 8px; color: var(--muted); font-size: 11px; }
    .context {
      margin-top: 14px; border-left: 3px solid var(--violet); padding: 10px 12px;
      background: #21192e; color: #d8c6ed; border-radius: 0 8px 8px 0;
    }
    .row-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 10px; }
    .note { min-height: 76px; margin-top: 12px; }
    .card-foot { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; padding: 13px 16px; border-top: 1px solid var(--line); }
    .nav { display: flex; gap: 8px; }
    .side .card-body { padding: 10px; }
    .queue-title { color: var(--muted); font-size: 12px; margin: 5px 5px 9px; }
    .queue-item {
      width: 100%; text-align: left; border: 0; background: transparent; border-radius: 8px; padding: 9px;
      display: grid; grid-template-columns: 9px 1fr; gap: 8px;
    }
    .queue-item.current { background: #233047; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #6e7b8d; margin-top: 6px; }
    .dot.confirmed { background: var(--green); }
    .dot.edit { background: var(--amber); }
    .dot.preserve { background: var(--violet); }
    .queue-source { color: var(--ink); font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .queue-state { color: var(--muted); font-size: 11px; }
    .keyboard { color: var(--muted); font-size: 12px; }
    .toast {
      position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%) translateY(20px);
      opacity: 0; pointer-events: none; transition: .2s; background: #e6edf3; color: #111827;
      border-radius: 9px; padding: 9px 14px; box-shadow: 0 8px 26px #0008;
    }
    .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
    @media (max-width: 900px) {
      .metrics { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .workspace { grid-template-columns: 1fr; }
      .side { order: 2; }
      .filters { grid-template-columns: 1fr 1fr; }
      .topbar { flex-direction: column; }
      .actions { justify-content: flex-start; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <div>
        <h1>简体中文逐条确认</h1>
        <div class="subtitle">先核对专业初译，再确认。全部完成后才进入代码合成。</div>
        <div id="phase" class="phase">审校阶段 · 尚不可合成</div>
      </div>
      <div class="actions">
        <button id="reset">清空本地进度</button>
        <button id="export" disabled>导出已确认清单</button>
        <button id="synthesize" class="primary" disabled>进入合成</button>
      </div>
    </div>

    <section class="progress">
      <div class="progress-track"><div id="progressFill" class="progress-fill"></div></div>
      <div class="metrics">
        <div class="metric"><strong id="metricTotal">0</strong><span>全部条目</span></div>
        <div class="metric"><strong id="metricPending">0</strong><span>待确认</span></div>
        <div class="metric"><strong id="metricConfirmed">0</strong><span>已确认</span></div>
        <div class="metric"><strong id="metricEdit">0</strong><span>需修改</span></div>
        <div class="metric"><strong id="metricPreserve">0</strong><span>保留英文</span></div>
      </div>
    </section>

    <section class="filters">
      <input id="search" type="search" placeholder="搜索英文、中文、编号">
      <select id="moduleFilter"><option value="">全部模块</option></select>
      <select id="statusFilter">
        <option value="">全部状态</option>
        <option value="待确认" selected>待确认</option>
        <option value="需修改">需修改</option>
        <option value="已确认">已确认</option>
      </select>
      <select id="confidenceFilter">
        <option value="">全部置信度</option>
        <option value="高">高</option>
        <option value="中">中</option>
        <option value="低">低</option>
        <option value="不适用">不适用</option>
      </select>
    </section>

    <section class="workspace">
      <article class="card">
        <div class="card-head">
          <div id="itemPosition" class="badge">0 / 0</div>
          <div id="itemState" class="badge">待确认</div>
        </div>
        <div class="card-body">
          <div class="source">
            <div class="label">English source</div>
            <pre id="source"></pre>
          </div>
          <div class="translation-wrap">
            <div class="label">专业初译 / 可编辑</div>
            <textarea id="translation" spellcheck="false"></textarea>
            <span id="charCount" class="char-count"></span>
          </div>
          <div id="context" class="context"></div>
          <div class="row-meta" id="meta"></div>
          <textarea id="reviewNote" class="note" placeholder="修改意见（可选；标记需修改时建议填写）"></textarea>
        </div>
        <div class="card-foot">
          <div class="nav">
            <button id="prev">← 上一项</button>
            <button id="next">下一项 →</button>
          </div>
          <span class="keyboard">⌘/Ctrl + Enter 确认并下一项</span>
          <div class="nav">
            <button id="needsEdit" class="warning">需修改</button>
            <button id="confirm" class="confirm">确认并下一项</button>
          </div>
        </div>
      </article>

      <aside class="card side">
        <div class="card-head"><strong>当前筛选</strong><span id="queueCount" class="badge">0</span></div>
        <div class="card-body">
          <div class="queue-title">逐条处理队列</div>
          <div id="queue"></div>
        </div>
      </aside>
    </section>
  </main>
  <div id="toast" class="toast"></div>
  <script id="review-data" type="application/json">__DATA__</script>
  <script>
    const seed = JSON.parse(document.getElementById('review-data').textContent);
    const storageKey = `osd-zh-cn-review-${seed.metadata.sourceCommit}`;
    const state = loadState();
    let filtered = [];
    let currentId = null;

    const $ = (id) => document.getElementById(id);
    const esc = (value) => String(value ?? '')
      .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;').replaceAll("'", '&#39;');

    function loadState() {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          const map = new Map(parsed.map((item) => [item.id, item]));
          seed.entries = seed.entries.map((entry) => ({ ...entry, ...(map.get(entry.id) || {}) }));
          return parsed;
        } catch (_) {}
      }
      const initial = seed.entries.map((entry) => ({
        id: entry.id,
        translation: entry.translation,
        status: entry.status || '待确认',
        note: '',
      }));
      localStorage.setItem(storageKey, JSON.stringify(initial));
      return initial;
    }

    function saveState() {
      localStorage.setItem(storageKey, JSON.stringify(seed.entries.map((entry) => ({
        id: entry.id,
        translation: entry.translation,
        status: entry.status,
        note: entry.note || '',
      }))));
    }

    function showToast(text) {
      $('toast').textContent = text;
      $('toast').classList.add('show');
      clearTimeout(showToast.timer);
      showToast.timer = setTimeout(() => $('toast').classList.remove('show'), 1800);
    }

    function topModule(value) {
      return String(value || '其他').split(',')[0].trim() || '其他';
    }

    function counts() {
      const result = { total: seed.entries.length, '待确认': 0, '已确认': 0, '需修改': 0, preserve: 0 };
      for (const entry of seed.entries) {
        if (entry.status === '已确认') result['已确认']++;
        else if (entry.status === '需修改') result['需修改']++;
        else result['待确认']++;
        if (entry.disposition === '保留英文') result.preserve++;
      }
      return result;
    }

    function updateProgress() {
      const c = counts();
      const complete = c['已确认'];
      $('metricTotal').textContent = c.total;
      $('metricPending').textContent = c['待确认'];
      $('metricConfirmed').textContent = c['已确认'];
      $('metricEdit').textContent = c['需修改'];
      $('metricPreserve').textContent = c.preserve;
      $('progressFill').style.width = `${c.total ? (complete / c.total) * 100 : 0}%`;
      const ready = c['待确认'] === 0 && c['需修改'] === 0;
      $('synthesize').disabled = !ready;
      $('export').disabled = !ready;
      $('phase').classList.toggle('ready', ready);
      $('phase').textContent = ready ? '确认完成 · 已允许进入合成' : '审校阶段 · 尚不可合成';
    }

    function applyFilter() {
      const query = $('search').value.trim().toLowerCase();
      const module = $('moduleFilter').value;
      const status = $('statusFilter').value;
      const confidence = $('confidenceFilter').value;
      filtered = seed.entries.filter((entry) => {
        if (module && topModule(entry.module) !== module) return false;
        if (status && entry.status !== status) return false;
        if (confidence && entry.confidence !== confidence) return false;
        if (query) {
          const haystack = `${entry.id} ${entry.source} ${entry.translation} ${entry.module}`.toLowerCase();
          if (!haystack.includes(query)) return false;
        }
        return true;
      });
      if (!filtered.some((entry) => entry.id === currentId)) currentId = filtered[0]?.id || null;
      render();
    }

    function render() {
      updateProgress();
      $('queueCount').textContent = filtered.length;
      const index = filtered.findIndex((entry) => entry.id === currentId);
      const entry = seed.entries.find((item) => item.id === currentId);
      $('prev').disabled = index <= 0;
      $('next').disabled = index < 0 || index >= filtered.length - 1;
      $('confirm').disabled = !entry;
      $('needsEdit').disabled = !entry;
      if (!entry) {
        $('itemPosition').textContent = '无匹配项';
        $('itemState').textContent = '—';
        $('source').textContent = '';
        $('translation').value = '';
        $('translation').disabled = true;
        $('context').textContent = '';
        $('meta').innerHTML = '';
        $('reviewNote').value = '';
        $('queue').innerHTML = '<div class="queue-state" style="padding:12px">没有符合筛选条件的条目。</div>';
        return;
      }

      $('translation').disabled = false;
      $('itemPosition').textContent = `${index + 1} / ${filtered.length}`;
      $('itemState').textContent = entry.disposition === '保留英文' ? `${entry.status} · 保留英文` : entry.status;
      $('source').textContent = entry.source;
      $('translation').value = entry.translation;
      $('confirm').textContent = entry.disposition === '保留英文' ? '确认保留并下一项' : '确认并下一项';
      $('charCount').textContent = `${entry.translation.length} 字`;
      $('context').textContent = entry.context_note || '';
      $('reviewNote').value = entry.note || '';
      $('meta').innerHTML = [
        `编号 ${entry.id}`,
        `模块 ${entry.module}`,
        `置信度 ${entry.confidence}`,
        `处置 ${entry.disposition}`,
        entry.entry_type || (entry.pdf ? 'PDF/打印' : '界面文案'),
      ].map((text) => `<span class="badge">${esc(text)}</span>`).join('');

      $('queue').innerHTML = filtered.slice(Math.max(0, index - 5), Math.max(0, index - 5) + 12).map((item) => {
        const dotClass = item.status === '已确认' ? 'confirmed' : item.status === '需修改' ? 'edit' : item.disposition === '保留英文' ? 'preserve' : '';
        return `<button class="queue-item ${item.id === currentId ? 'current' : ''}" data-id="${esc(item.id)}">
          <span class="dot ${dotClass}"></span>
          <span><span class="queue-source">${esc(item.source)}</span><span class="queue-state">${esc(item.status)} · ${esc(item.disposition)}</span></span>
        </button>`;
      }).join('');
      $('queue').querySelectorAll('[data-id]').forEach((button) => {
        button.addEventListener('click', () => selectItem(button.dataset.id));
      });
    }

    function selectItem(id) {
      currentId = id;
      render();
    }

    function updateCurrent(patch) {
      const entry = seed.entries.find((item) => item.id === currentId);
      if (!entry) return;
      Object.assign(entry, patch);
      saveState();
      render();
    }

    function step(delta) {
      const index = filtered.findIndex((entry) => entry.id === currentId);
      const next = filtered[index + delta];
      if (next) selectItem(next.id);
    }

    function confirmCurrent() {
      const entry = seed.entries.find((item) => item.id === currentId);
      if (!entry) return;
      if (!entry.translation.trim()) {
        showToast('译文为空，请补译或确认保留英文');
        $('translation').focus();
        return;
      }
      updateCurrent({ status: '已确认', note: $('reviewNote').value.trim() });
      showToast(entry.disposition === '保留英文' ? '已确认保留英文' : '已确认');
      // Keep the active filter useful: after confirmation, move to the next row
      // before the row disappears from a "pending" filter.
      const oldIndex = filtered.findIndex((item) => item.id === entry.id);
      applyFilter();
      const next = filtered[Math.min(oldIndex, filtered.length - 1)];
      if (next) selectItem(next.id);
    }

    function markNeedsEdit() {
      updateCurrent({ status: '需修改', note: $('reviewNote').value.trim() });
      showToast('已标记需修改');
      step(1);
    }

    function exportReview() {
      const c = counts();
      if (c['待确认'] !== 0 || c['需修改'] !== 0) {
        showToast('仍有待确认或需修改条目，暂不能导出确认清单');
        return false;
      }
      const output = {
        ...seed,
        metadata: {
          ...seed.metadata,
          exportedAt: new Date().toISOString(),
          reviewState: 'confirmed',
        },
        entries: seed.entries,
      };
      const blob = new Blob([JSON.stringify(output, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'zh-cn-confirmed.json';
      link.click();
      URL.revokeObjectURL(url);
      showToast('已导出已确认清单');
      return true;
    }

    function initFilters() {
      const modules = [...new Set(seed.entries.map((entry) => topModule(entry.module)))].sort();
      $('moduleFilter').insertAdjacentHTML('beforeend', modules.map((module) =>
        `<option value="${esc(module)}">${esc(module)}</option>`).join(''));
    }

    $('search').addEventListener('input', applyFilter);
    $('moduleFilter').addEventListener('change', applyFilter);
    $('statusFilter').addEventListener('change', applyFilter);
    $('confidenceFilter').addEventListener('change', applyFilter);
    $('translation').addEventListener('input', (event) => {
      const entry = seed.entries.find((item) => item.id === currentId);
      if (entry) {
        entry.translation = event.target.value;
        if (entry.status === '已确认') {
          entry.status = '需修改';
          entry.note = '已确认后再次修改，需要重新确认。';
          $('itemState').textContent = `${entry.status} · 重新确认`;
          saveState();
          updateProgress();
        }
      }
      $('charCount').textContent = `${event.target.value.length} 字`;
    });
    $('translation').addEventListener('blur', () => updateCurrent({ translation: $('translation').value }));
    $('reviewNote').addEventListener('blur', () => updateCurrent({ note: $('reviewNote').value.trim() }));
    $('prev').addEventListener('click', () => step(-1));
    $('next').addEventListener('click', () => step(1));
    $('confirm').addEventListener('click', confirmCurrent);
    $('needsEdit').addEventListener('click', markNeedsEdit);
    $('export').addEventListener('click', exportReview);
    $('synthesize').addEventListener('click', () => {
      if (exportReview()) showToast('确认完成，已导出合成输入');
    });
    $('reset').addEventListener('click', () => {
      if (!confirm('确定清空此浏览器中的全部审校进度吗？')) return;
      localStorage.removeItem(storageKey);
      location.reload();
    });
    document.addEventListener('keydown', (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
        event.preventDefault();
        confirmCurrent();
      } else if (event.key === 'ArrowLeft' && !event.target.matches('textarea,input,select')) {
        step(-1);
      } else if (event.key === 'ArrowRight' && !event.target.matches('textarea,input,select')) {
        step(1);
      }
    });

    initFilters();
    updateProgress();
    applyFilter();
  </script>
</body>
</html>
"""


def build() -> Path:
    data = json.loads(DRAFTS.read_text(encoding="utf-8"))
    term_data = json.loads(TERMS.read_text(encoding="utf-8"))
    entry_type_order = {"术语": 0, "界面": 1}
    disposition_order = {"术语初译": 0, "初译": 1, "保留英文": 2}
    confidence_order = {"高": 0, "中": 1, "低": 2, "不适用": 3}
    module_order = {
        "components/dashboard": 0,
        "components/inspector": 1,
        "components/equipment": 2,
        "components/schedule": 3,
        "components/shotlist": 4,
        "components/continuity": 5,
        "components/script": 6,
        "components/power": 7,
        "components/rigging": 8,
        "components/budget": 9,
        "components/locations": 10,
        "components/logistics": 11,
    }

    def priority(entry: dict) -> tuple[int, int, int, int, str]:
        primary_module = str(entry.get("module", "")).split(",")[0].strip()
        return (
            entry_type_order.get(str(entry.get("entry_type", "界面")), 2),
            confidence_order.get(str(entry.get("confidence")), 4),
            disposition_order.get(str(entry.get("disposition")), 2),
            module_order.get(primary_module, 20),
            str(entry.get("source", "")).casefold(),
        )

    data["entries"] = sorted(
        [*term_data["entries"], *data["entries"]],
        key=priority,
    )
    data["metadata"]["reviewStages"] = ["术语", "界面与打印"]
    data["metadata"]["counts"]["reviewEntries"] = len(data["entries"])
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</script", "<\\/script")
    OUTPUT.write_text(HTML.replace("__DATA__", payload), encoding="utf-8")
    return OUTPUT


if __name__ == "__main__":
    print(build())
