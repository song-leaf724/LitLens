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
  agentModeSelect: $('agentModeSelect'),
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

const DOCUMENT_TYPE_LABELS = {
  english_fiction: '英文小说',
  modern_chinese: '现代中文文本',
  classical_poetry: '古典诗歌',
  classical_prose: '文言散文',
  poetry_or_lyrics: '诗歌文本',
  unknown: '暂未识别',
};

const STRATEGY_LABELS = {
  modern: '按段落阅读',
  poetry: '按诗句阅读',
  classical_prose: '按文言句群阅读',
};

const STATUS_LABELS = {
  pending: '等待处理',
  processing: '正在入库',
  completed: '已完成',
  failed: '处理失败',
};

const SOURCE_LABELS = {
  gutenberg: 'Gutenberg',
  wikisource: 'Wikisource',
};

const LANGUAGE_LABELS = {
  en: '英文',
  zh: '中文',
  'zh-cn': '中文',
  'zh-hans': '中文',
};

const CHUNK_TYPE_LABELS = {
  whole_poem: '整首诗',
  poem_couplet: '诗句片段',
  poem_line: '诗句',
  paragraph: '段落',
  paragraph_window: '段落片段',
  classical_sentence_group: '文言句群',
  sentence_group: '句群',
  text: '文本片段',
};

const STEP_TYPE_LABELS = {
  plan: '分析计划',
  retrieve: '查找原文',
  reader_analysis: '原文细读',
  critic_analysis: '文学分析',
  verification: '依据核查',
  final: '整理回答',
  fast_answer: '快速回答',
  error: '运行异常',
};

const ROLE_LABELS = {
  PlannerAgent: '规划',
  Retriever: '原文检索',
  ReaderAgent: '细读',
  CriticAgent: '文学分析',
  VerifierAgent: '依据核查',
  FinalWriterAgent: '汇总',
  FastLiteraryAgent: '快速分析',
  LiteratureAgent: '系统',
};

const AGENT_STATUS_LABELS = {
  completed: { fast: '快速分析完成', deep: '深度细读完成' },
  failed: { fast: '快速分析未完成', deep: '深度细读未完成' },
  running: { fast: '正在快速分析', deep: '正在深度细读' },
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
  const escaped = escapeHtml(text || '').trim();
  if (!escaped) return '<p>暂无内容。</p>';

  const lines = escaped.split('\n');
  const html = [];
  let listType = null;

  function closeList() {
    if (listType) {
      html.push(`</${listType}>`);
      listType = null;
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (line.startsWith('### ')) {
      closeList();
      html.push(`<h3>${line.slice(4)}</h3>`);
    } else if (line.startsWith('## ')) {
      closeList();
      html.push(`<h2>${line.slice(3)}</h2>`);
    } else if (/^\d+\.\s+/.test(line)) {
      if (listType !== 'ol') { closeList(); html.push('<ol>'); listType = 'ol'; }
      html.push(`<li>${line.replace(/^\d+\.\s+/, '').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}</li>`);
    } else if (line.startsWith('- ')) {
      if (listType !== 'ul') { closeList(); html.push('<ul>'); listType = 'ul'; }
      html.push(`<li>${line.slice(2).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}</li>`);
    } else if (line.trim() === '') {
      closeList();
    } else {
      closeList();
      html.push(`<p>${line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}</p>`);
    }
  }
  closeList();
  return html.join('');
}

function labelOf(map, value, fallback = '未知') {
  if (value === null || value === undefined || value === '') return fallback;
  return map[value] || String(value);
}

function stripExtension(filename) {
  return String(filename || '').replace(/\.[^.]+$/, '');
}

function displayTitle(doc) {
  return doc?.title || stripExtension(doc?.filename) || '未命名文本';
}

function segmentLabel(docOrCount) {
  const count = typeof docOrCount === 'number' ? docOrCount : Number(docOrCount?.chunk_count || 0);
  return `${count} 段原文`;
}

function documentTypeLabel(doc) {
  return labelOf(DOCUMENT_TYPE_LABELS, doc?.document_type, '暂未识别');
}

function strategyLabel(doc) {
  return labelOf(STRATEGY_LABELS, doc?.chunk_strategy, '通用阅读方式');
}

function statusLabel(docOrStatus) {
  const status = typeof docOrStatus === 'string' ? docOrStatus : docOrStatus?.status;
  return labelOf(STATUS_LABELS, status, '未知状态');
}

function sourceLabel(source) {
  return labelOf(SOURCE_LABELS, source, '本地上传');
}

function languageLabel(language) {
  return labelOf(LANGUAGE_LABELS, String(language || '').toLowerCase(), language || '语言未知');
}

function chunkTypeLabel(citation) {
  return citation?.section_title || labelOf(CHUNK_TYPE_LABELS, citation?.chunk_type, '原文片段');
}

function stepTypeLabel(step) {
  return labelOf(STEP_TYPE_LABELS, step?.step_type, '分析步骤');
}

function roleLabel(role) {
  return labelOf(ROLE_LABELS, role, role || '分析器');
}

function sourceLocationLabel(location) {
  const match = String(location || '').match(/^chars:(\d+)-(\d+)$/);
  if (match) return `原文位置 ${match[1]}-${match[2]}`;
  return location || '';
}

function truncateText(text, limit = 150) {
  const value = String(text || '').replace(/\s+/g, ' ').trim();
  return value.length > limit ? `${value.slice(0, limit)}...` : value;
}

function readableError(detail) {
  if (Array.isArray(detail)) return detail.map((item) => item.msg || JSON.stringify(item)).join('；');
  if (detail && typeof detail === 'object') return detail.message || JSON.stringify(detail);
  return detail || '请求失败';
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
    throw new Error(readableError(detail) || `请求失败：${response.status}`);
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
    button.textContent = label || '请稍候...';
    button.disabled = true;
  } else {
    button.textContent = button.dataset.label || button.textContent;
    button.disabled = false;
  }
}

async function loadDocuments(selectId = null) {
  els.documentsList.textContent = '正在读取文本...';
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
    showToast(`文本列表加载失败：${error.message}`, 'error');
  }
}

function renderDocuments() {
  if (!state.documents.length) {
    els.documentsList.className = 'documents-list empty';
    els.documentsList.textContent = '还没有文本。你可以上传本地 txt/md，或从公开书源导入。';
    return;
  }
  els.documentsList.className = 'documents-list';
  els.documentsList.innerHTML = state.documents.map((doc) => {
    const active = doc.id === state.selectedDocumentId ? ' active' : '';
    return `
      <article class="doc-card${active}" data-id="${escapeHtml(doc.id)}">
        <p class="card-title">${escapeHtml(displayTitle(doc))}</p>
        <p class="card-meta">${escapeHtml(documentTypeLabel(doc))} · ${escapeHtml(segmentLabel(doc))}</p>
        <div class="doc-card-footer">
          <p class="card-meta">${escapeHtml(sourceLabel(doc.source_name))} · ${escapeHtml(statusLabel(doc))}</p>
          <button class="delete-document-button" data-id="${escapeHtml(doc.id)}" type="button" aria-label="删除 ${escapeHtml(displayTitle(doc))}">删除</button>
        </div>
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
      els.answerContent.textContent = '已切换文本，请输入你想细读的问题。';
    });
  });
  els.documentsList.querySelectorAll('.delete-document-button').forEach((button) => {
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      deleteDocument(button.dataset.id);
    });
  });
}

async function deleteDocument(documentId) {
  const doc = state.documents.find((item) => item.id === documentId);
  if (!doc) return;
  const confirmed = window.confirm(`确定删除《${displayTitle(doc)}》吗？这会同时删除本地文本、原文片段和向量索引。`);
  if (!confirmed) return;

  try {
    await apiFetch(`/documents/${encodeURIComponent(documentId)}`, { method: 'DELETE' });
    showToast('文本已删除。', 'success');
    if (state.selectedDocumentId === documentId) {
      state.selectedDocumentId = null;
      state.citations = [];
      state.steps = [];
      els.answerMode.textContent = '等待提问';
      els.answerContent.className = 'answer empty';
      els.answerContent.textContent = '回答会显示在这里。';
      renderCitations();
      renderSteps();
    }
    await loadDocuments();
  } catch (error) {
    showToast(`删除失败：${error.message}`, 'error');
  }
}

function renderCurrentDocument() {
  const doc = selectedDocument();
  if (!doc) {
    els.currentTitle.textContent = '请选择或上传文本';
    els.currentMeta.textContent = '等待文本';
    els.documentInfo.className = 'info-grid empty';
    els.documentInfo.textContent = '暂无选中文本。';
    return;
  }
  els.currentTitle.textContent = displayTitle(doc);
  els.currentMeta.textContent = `${documentTypeLabel(doc)} · ${segmentLabel(doc)} · ${statusLabel(doc)}`;
  const items = [
    ['文本名称', displayTitle(doc)],
    ['体裁判断', documentTypeLabel(doc)],
    ['阅读方式', strategyLabel(doc)],
    ['处理状态', statusLabel(doc)],
    ['原文段落', segmentLabel(doc)],
    ['来源', sourceLabel(doc.source_name)],
    ['作者', doc.author || '未标注'],
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
    els.citationsList.textContent = '回答时会在这里列出用到的原文。';
    return;
  }
  els.citationsList.className = 'citation-list';
  els.citationsList.innerHTML = state.citations.map((citation, index) => {
    const meta = [citation.title || citation.filename, sourceLocationLabel(citation.source_location)]
      .filter(Boolean)
      .join(' · ');
    return `
      <article class="citation-card">
        <p class="card-title">依据 ${index + 1} · ${escapeHtml(chunkTypeLabel(citation))}</p>
        <p class="card-meta">${escapeHtml(meta)}</p>
        <blockquote>${escapeHtml(citation.content)}</blockquote>
      </article>
    `;
  }).join('');
}

function renderRetrieveSummary(outputText) {
  let observation = null;
  try {
    observation = JSON.parse(outputText || '{}');
  } catch {
    return '<div class="step-output"><p>原文查找已完成，但结果暂时无法整理成可读摘要。</p></div>';
  }

  const citations = observation.citations || [];
  if (!citations.length) {
    return '<div class="step-output"><p>没有找到足够相关的原文。可以换一个更贴近文本内容的问题，或增加引用数量后再试。</p></div>';
  }

  const cards = citations.slice(0, 3).map((citation, index) => `
    <div class="mini-evidence">
      <strong>原文 ${index + 1} · ${escapeHtml(chunkTypeLabel(citation))}</strong>
      <span>${escapeHtml(truncateText(citation.content, 110))}</span>
    </div>
  `).join('');

  return `
    <div class="step-output">
      <p>已从当前文本中找到 ${citations.length} 段可引用原文。</p>
      <div class="mini-evidence-list">${cards}</div>
    </div>
  `;
}

function renderStepBody(step) {
  if (step.error_message) {
    return `<div class="step-output step-error"><p>${escapeHtml(step.error_message || '这一步没有成功完成。')}</p></div>`;
  }
  if (step.step_type === 'retrieve') {
    return renderRetrieveSummary(step.output_text);
  }
  return `<div class="step-output">${markdownToHtml(step.output_text || '这一步已经完成。')}</div>`;
}

function renderSteps(steps = state.steps) {
  state.steps = steps || [];
  els.stepCount.textContent = String(state.steps.length);
  if (!state.steps.length) {
    els.stepsList.className = 'steps-list empty';
    els.stepsList.textContent = '运行快速分析或深度细读后，这里会展示分析过程。';
    return;
  }
  els.stepsList.className = 'steps-list';
  els.stepsList.innerHTML = state.steps.map((step) => `
    <article class="step-card">
      <div class="step-head">
        <span class="step-type">${escapeHtml(stepTypeLabel(step))}</span>
        <span class="card-meta">${escapeHtml(roleLabel(step.role))}</span>
      </div>
      ${renderStepBody(step)}
    </article>
  `).join('');
}

function getTopK() {
  const value = Number.parseInt(els.topKInput.value, 10);
  if (Number.isNaN(value)) return 5;
  return Math.min(20, Math.max(1, value));
}

function getAgentMode() {
  return els.agentModeSelect?.value === 'fast' ? 'fast' : 'deep';
}

function agentModeLabel(mode) {
  return mode === 'fast' ? '快速分析' : '深度细读';
}

function agentStatusLabel(status, mode) {
  const labels = AGENT_STATUS_LABELS[status];
  if (labels) return labels[mode] || labels.deep;
  return agentModeLabel(mode);
}

function requireDocumentAndQuestion() {
  const doc = selectedDocument();
  const query = els.queryInput.value.trim();
  if (!doc) throw new Error('请先选择或上传一个文本。');
  if (!query) throw new Error('请先输入你想分析的问题。');
  return { doc, query };
}

async function uploadDocument() {
  const file = els.fileInput.files?.[0];
  if (!file) {
    showToast('请先选择文件。', 'error');
    return;
  }
  setBusy(els.uploadButton, true, '正在入库...');
  try {
    const body = new FormData();
    body.append('file', file);
    const doc = await apiFetch('/documents/upload', { method: 'POST', body });
    showToast('上传完成，已准备好细读。', 'success');
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
  els.sourceResults.textContent = '正在搜索公开文本...';
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
    els.sourceResults.textContent = '没有搜索到候选作品。可以换一个书名或作者名试试。';
    return;
  }
  els.sourceResults.className = 'source-results';
  els.sourceResults.innerHTML = results.map((item) => `
    <article class="source-card">
      <p class="card-title">${escapeHtml(item.title)}</p>
      <p class="card-meta">${escapeHtml(item.author || '未知作者')} · ${escapeHtml(languageLabel(item.language))} · ${escapeHtml(sourceLabel(item.source))}</p>
      <button class="secondary full import-button" data-source="${escapeHtml(item.source)}" data-id="${escapeHtml(item.source_id)}" type="button">导入这本书</button>
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
    showToast('导入完成，已准备好细读。', 'success');
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
  setBusy(els.ragButton, true, '正在阅读...');
  els.answerMode.textContent = '基于原文回答';
  els.answerContent.className = 'answer empty';
  els.answerContent.textContent = '正在查找相关原文，并组织回答...';
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
    showToast(`回答失败：${error.message}`, 'error');
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
  const mode = getAgentMode();
  setBusy(els.agentButton, true, mode === 'fast' ? '分析中...' : '细读中...');
  els.answerMode.textContent = agentModeLabel(mode);
  els.answerContent.className = 'answer empty';
  els.answerContent.textContent = mode === 'fast'
    ? '正在快速查找原文，并生成简要回答...'
    : '正在分步骤阅读原文、分析主题，并核查依据...';
  renderCitations([]);
  renderSteps([]);
  try {
    const payload = await apiFetch('/agent/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: doc.id, task: query, task_type: 'literature', top_k: getTopK(), mode }),
    });
    els.answerMode.textContent = agentStatusLabel(payload.status, mode);
    els.answerContent.className = 'answer';
    els.answerContent.innerHTML = markdownToHtml(payload.answer || '暂时没有生成回答。');
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
    showToast(`${agentModeLabel(mode)}失败：${error.message}`, 'error');
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
