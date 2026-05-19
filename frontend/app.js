const state = {
  documents: [],
  selectedDocumentId: null,
  citations: [],
  steps: [],
};

const $ = (id) => document.getElementById(id);

const els = {
  fileInput: $('fileInput'),
  fileName: $('fileName'),
  uploadButton: $('uploadButton'),
  sourceSelect: $('sourceSelect'),
  sourceQuery: $('sourceQuery'),
  sourceSearchButton: $('sourceSearchButton'),
  sourceResults: $('sourceResults'),
  refreshDocumentsButton: $('refreshDocumentsButton'),
  documentsList: $('documentsList'),
  currentTitle: $('currentTitle'),
  currentMeta: $('currentMeta'),
  documentInfo: $('documentInfo'),
  queryInput: $('queryInput'),
  topKInput: $('topKInput'),
  ragButton: $('ragButton'),
  agentButton: $('agentButton'),
  answerContent: $('answerContent'),
  answerMode: $('answerMode'),
  citationsList: $('citationsList'),
  citationCount: $('citationCount'),
  stepsList: $('stepsList'),
  stepCount: $('stepCount'),
  toast: $('toast'),
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function markdownToHtml(text) {
  const escaped = escapeHtml(text || '');
  const lines = escaped.split('\n');
  const html = [];
  let inList = false;
  for (const line of lines) {
    if (line.startsWith('### ')) {
      if (inList) { html.push('</ul>'); inList = false; }
      html.push(`<h3>${line.slice(4)}</h3>`);
    } else if (line.startsWith('## ')) {
      if (inList) { html.push('</ul>'); inList = false; }
      html.push(`<h2>${line.slice(3)}</h2>`);
    } else if (line.startsWith('- ')) {
      if (!inList) { html.push('<ul>'); inList = true; }
      html.push(`<li>${line.slice(2)}</li>`);
    } else if (line.trim() === '') {
      if (inList) { html.push('</ul>'); inList = false; }
    } else {
      if (inList) { html.push('</ul>'); inList = false; }
      html.push(`<p>${line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}</p>`);
    }
  }
  if (inList) html.push('</ul>');
  return html.join('');
}

function showToast(message, type = '') {
  els.toast.textContent = message;
  els.toast.className = `toast show ${type}`.trim();
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    els.toast.className = 'toast';
  }, 3200);
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  let payload = null;
  if (text) {
    try { payload = JSON.parse(text); } catch { payload = text; }
  }
  if (!response.ok) {
    const detail = payload && typeof payload === 'object' ? payload.detail : payload;
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return payload;
}

function selectedDocument() {
  return state.documents.find((doc) => doc.id === state.selectedDocumentId) || null;
}

function setBusy(button, busy, label) {
  if (!button) return;
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = label || '处理中...';
    button.disabled = true;
  } else {
    button.textContent = button.dataset.label || button.textContent;
    button.disabled = false;
  }
}

async function loadDocuments(selectId = null) {
  els.documentsList.textContent = '正在读取文档...';
  els.documentsList.className = 'documents-list empty';
  try {
    const payload = await apiFetch('/documents');
    state.documents = payload.documents || [];
    if (selectId) state.selectedDocumentId = selectId;
    if (!state.selectedDocumentId && state.documents.length) {
      state.selectedDocumentId = state.documents[0].id;
    }
    if (state.selectedDocumentId && !state.documents.some((doc) => doc.id === state.selectedDocumentId)) {
      state.selectedDocumentId = state.documents[0]?.id || null;
    }
    renderDocuments();
    renderCurrentDocument();
  } catch (error) {
    els.documentsList.textContent = error.message;
    showToast(`文档列表加载失败：${error.message}`, 'error');
  }
}

function renderDocuments() {
  if (!state.documents.length) {
    els.documentsList.className = 'documents-list empty';
    els.documentsList.textContent = '暂无文档。';
    return;
  }
  els.documentsList.className = 'documents-list';
  els.documentsList.innerHTML = state.documents.map((doc) => {
    const title = doc.title || doc.filename;
    const active = doc.id === state.selectedDocumentId ? ' active' : '';
    const status = doc.status === 'completed' ? '已入库' : doc.status;
    return `
      <article class="doc-card${active}" data-id="${escapeHtml(doc.id)}">
        <p class="card-title">${escapeHtml(title)}</p>
        <p class="card-meta">${escapeHtml(doc.document_type)} · ${escapeHtml(doc.chunk_strategy)} · ${doc.chunk_count} chunks</p>
        <p class="card-meta">${escapeHtml(status)}</p>
      </article>`;
  }).join('');
  els.documentsList.querySelectorAll('.doc-card').forEach((card) => {
    card.addEventListener('click', () => {
      state.selectedDocumentId = card.dataset.id;
      state.citations = [];
      state.steps = [];
      renderDocuments();
      renderCurrentDocument();
      renderCitations();
      renderSteps();
      els.answerMode.textContent = '等待提问';
      els.answerContent.className = 'answer empty';
      els.answerContent.textContent = '已切换文档，请输入问题。';
    });
  });
}

function renderCurrentDocument() {
  const doc = selectedDocument();
  if (!doc) {
    els.currentTitle.textContent = '请选择或上传文本';
    els.currentMeta.textContent = '等待文档';
    els.documentInfo.className = 'info-grid empty';
    els.documentInfo.textContent = '暂无选中文档。';
    return;
  }
  els.currentTitle.textContent = doc.title || doc.filename;
  els.currentMeta.textContent = `${doc.document_type} · ${doc.chunk_count} chunks · ${doc.status}`;
  const items = [
    ['文件', doc.filename],
    ['体裁', doc.document_type],
    ['策略', doc.chunk_strategy],
    ['状态', doc.status],
    ['来源', doc.source_name || '本地上传'],
    ['作者', doc.author || '未知'],
  ];
  els.documentInfo.className = 'info-grid';
  els.documentInfo.innerHTML = items.map(([key, value]) => `
    <div class="info-item"><span>${escapeHtml(key)}</span><span>${escapeHtml(value)}</span></div>
  `).join('');
}

function renderCitations(citations = state.citations) {
  state.citations = citations || [];
  els.citationCount.textContent = String(state.citations.length);
  if (!state.citations.length) {
    els.citationsList.className = 'citation-list empty';
    els.citationsList.textContent = '运行 RAG 或 Agent 后显示引用。';
    return;
  }
  els.citationsList.className = 'citation-list';
  els.citationsList.innerHTML = state.citations.map((citation, index) => `
    <article class="citation-card">
      <p class="card-title">引用 ${index + 1} · ${escapeHtml(citation.section_title || citation.chunk_type)}</p>
      <p class="card-meta">${escapeHtml(citation.filename)} · ${escapeHtml(citation.source_location)} · score ${citation.score == null ? '-' : Number(citation.score).toFixed(3)}</p>
      <blockquote>${escapeHtml(citation.content)}</blockquote>
    </article>
  `).join('');
}

function renderSteps(steps = state.steps) {
  state.steps = steps || [];
  els.stepCount.textContent = String(state.steps.length);
  if (!state.steps.length) {
    els.stepsList.className = 'steps-list empty';
    els.stepsList.textContent = '运行 Agent 后显示执行轨迹。';
    return;
  }
  els.stepsList.className = 'steps-list';
  els.stepsList.innerHTML = state.steps.map((step) => {
    const output = step.error_message || step.output_text || step.input_text || '无输出';
    return `
      <article class="step-card">
        <div class="step-head">
          <span class="step-type">${escapeHtml(step.step_type)}</span>
          <span class="card-meta">${escapeHtml(step.role)}</span>
        </div>
        <div class="step-output">${escapeHtml(output)}</div>
      </article>
    `;
  }).join('');
}

function getTopK() {
  const value = Number.parseInt(els.topKInput.value, 10);
  if (Number.isNaN(value)) return 5;
  return Math.min(20, Math.max(1, value));
}

function requireDocumentAndQuestion() {
  const doc = selectedDocument();
  const query = els.queryInput.value.trim();
  if (!doc) throw new Error('请先选择或上传一个文本。');
  if (!query) throw new Error('请先输入问题。');
  return { doc, query };
}

async function uploadDocument() {
  const file = els.fileInput.files?.[0];
  if (!file) {
    showToast('请先选择文件。', 'error');
    return;
  }
  setBusy(els.uploadButton, true, '上传中...');
  try {
    const body = new FormData();
    body.append('file', file);
    const doc = await apiFetch('/documents/upload', { method: 'POST', body });
    showToast('上传完成，已写入知识库。', 'success');
    await loadDocuments(doc.id);
  } catch (error) {
    showToast(`上传失败：${error.message}`, 'error');
  } finally {
    setBusy(els.uploadButton, false);
  }
}

async function searchSources() {
  const source = els.sourceSelect.value;
  const q = els.sourceQuery.value.trim();
  if (!q) {
    showToast('请输入书名关键词。', 'error');
    return;
  }
  setBusy(els.sourceSearchButton, true, '搜索中...');
  els.sourceResults.className = 'source-results empty';
  els.sourceResults.textContent = '正在搜索公开书源...';
  try {
    const payload = await apiFetch(`/book-sources/search?source=${encodeURIComponent(source)}&q=${encodeURIComponent(q)}&limit=8`);
    renderSourceResults(payload.results || []);
  } catch (error) {
    els.sourceResults.textContent = error.message;
    showToast(`书源搜索失败：${error.message}`, 'error');
  } finally {
    setBusy(els.sourceSearchButton, false);
  }
}

function renderSourceResults(results) {
  if (!results.length) {
    els.sourceResults.className = 'source-results empty';
    els.sourceResults.textContent = '没有搜索到候选作品。';
    return;
  }
  els.sourceResults.className = 'source-results';
  els.sourceResults.innerHTML = results.map((item) => `
    <article class="source-card">
      <p class="card-title">${escapeHtml(item.title)}</p>
      <p class="card-meta">${escapeHtml(item.author || '未知作者')} · ${escapeHtml(item.language || '-')} · ${escapeHtml(item.source)}</p>
      <button class="secondary full import-button" data-source="${escapeHtml(item.source)}" data-id="${escapeHtml(item.source_id)}" type="button">导入</button>
    </article>
  `).join('');
  els.sourceResults.querySelectorAll('.import-button').forEach((button) => {
    button.addEventListener('click', () => importBook(button.dataset.source, button.dataset.id, button));
  });
}

async function importBook(source, sourceId, button) {
  setBusy(button, true, '导入中...');
  try {
    const payload = await apiFetch('/book-sources/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source, source_id: sourceId }),
    });
    showToast('导入完成，已写入知识库。', 'success');
    await loadDocuments(payload.document.id);
  } catch (error) {
    showToast(`导入失败：${error.message}`, 'error');
  } finally {
    setBusy(button, false);
  }
}

async function runRag() {
  let doc;
  let query;
  try {
    ({ doc, query } = requireDocumentAndQuestion());
  } catch (error) {
    showToast(error.message, 'error');
    return;
  }
  setBusy(els.ragButton, true, '检索中...');
  els.answerMode.textContent = 'RAG 问答';
  els.answerContent.className = 'answer empty';
  els.answerContent.textContent = '正在检索原文并生成回答...';
  renderSteps([]);
  try {
    const payload = await apiFetch('/rag/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: doc.id, query, top_k: getTopK(), task_type: 'qa' }),
    });
    els.answerContent.className = 'answer';
    els.answerContent.innerHTML = markdownToHtml(payload.answer);
    renderCitations(payload.citations || []);
  } catch (error) {
    els.answerContent.className = 'answer empty';
    els.answerContent.textContent = error.message;
    showToast(`RAG 问答失败：${error.message}`, 'error');
  } finally {
    setBusy(els.ragButton, false);
  }
}

async function runAgent() {
  let doc;
  let query;
  try {
    ({ doc, query } = requireDocumentAndQuestion());
  } catch (error) {
    showToast(error.message, 'error');
    return;
  }
  setBusy(els.agentButton, true, '分析中...');
  els.answerMode.textContent = 'Agent 深度分析';
  els.answerContent.className = 'answer empty';
  els.answerContent.textContent = 'LangGraph 工作流运行中，可能需要一些时间...';
  renderCitations([]);
  renderSteps([]);
  try {
    const payload = await apiFetch('/agent/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: doc.id, task: query, task_type: 'literature', top_k: getTopK() }),
    });
    els.answerMode.textContent = `Agent ${payload.status}`;
    els.answerContent.className = 'answer';
    els.answerContent.innerHTML = markdownToHtml(payload.answer || '无回答内容。');
    renderSteps(payload.steps || []);
    const retrieveStep = (payload.steps || []).find((step) => step.step_type === 'retrieve' && step.output_text);
    if (retrieveStep) {
      try {
        const observation = JSON.parse(retrieveStep.output_text);
        renderCitations(observation.citations || []);
      } catch {
        renderCitations([]);
      }
    }
  } catch (error) {
    els.answerContent.className = 'answer empty';
    els.answerContent.textContent = error.message;
    showToast(`Agent 分析失败：${error.message}`, 'error');
  } finally {
    setBusy(els.agentButton, false);
  }
}

function bindEvents() {
  els.fileInput.addEventListener('change', () => {
    els.fileName.textContent = els.fileInput.files?.[0]?.name || '选择文学作品或片段';
  });
  els.uploadButton.addEventListener('click', uploadDocument);
  els.sourceSearchButton.addEventListener('click', searchSources);
  els.sourceQuery.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') searchSources();
  });
  els.refreshDocumentsButton.addEventListener('click', () => loadDocuments());
  els.ragButton.addEventListener('click', runRag);
  els.agentButton.addEventListener('click', runAgent);
}

bindEvents();
loadDocuments();
