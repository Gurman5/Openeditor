const API_BASE = '';

// ── Grouping helpers ─────────────────────────────────────────────────────────
function groupItems(items, getKey) {
  const groups = new Map();
  for (const item of items) {
    const key = getKey(item);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  return Array.from(groups.values());
}

function renderGrouped(groups, renderItem, threshold = 2) {
  let id = 0;
  return groups.map(group => {
    if (group.length <= threshold) return group.map(renderItem).join('');
    const gid = 'grp-' + (++id) + '-' + Date.now();
    const extra = group.length - 1;
    const label = `▼ Show ${extra} more instance${extra > 1 ? 's' : ''}`;
    return renderItem(group[0])
      + `<div class="grp-collapsed" id="${gid}" style="display:none">${group.slice(1).map(renderItem).join('')}</div>`
      + `<div class="grp-toggle" data-gid="${gid}" data-count="${extra}" onclick="toggleGroup(this)">${label}</div>`;
  }).join('');
}

function toggleGroup(btn) {
  const el = document.getElementById(btn.dataset.gid);
  const open = el.style.display !== 'none';
  el.style.display = open ? 'none' : '';
  btn.textContent = open
    ? `▼ Show ${btn.dataset.count} more instance${btn.dataset.count > 1 ? 's' : ''}`
    : `▲ Hide extra instances`;
}

// ── Step definitions for the processing phase ────────────────────────────────
const PROC_STEPS = [
  { id: 'step-structure' },
  { id: 'step-refs' },
  { id: 'step-llm' },
  { id: 'step-doc' },
];

const JUTLP_FALLBACK_ARTICLE = {
  title: 'The Artificial Intelligence Assessment Scale (AIAS): A Framework for Ethical Integration of Generative AI in Educational Assessment',
  author: 'Mike Perkins, Leon Furze, Jasper Roe, Jason MacVaugh',
  abstract: 'This JUTLP article introduces the AI Assessment Scale as a practical framework for deciding when and how generative AI can be used in educational assessment. It focuses on transparent, ethical integration of AI tools while keeping learning outcomes, academic integrity, and student engagement at the centre of assessment design.',
  url: 'https://open-publishing.org/journals/index.php/jutlp/article/view/810/769',
};
const JUTLP_ROTATE_MS = 150000;

let _jutlpArticles = [JUTLP_FALLBACK_ARTICLE];
let _jutlpArticleIndex = 0;
let _jutlpRotateTimer = null;
let _jutlpAbortController = null;

// ── Stage → step mapping ─────────────────────────────────────────────────────
// The backend reports a 'stage' string with each 202 poll response.
// We use that to activate the correct step label rather than fake timers.
const STAGE_TO_STEP = {
  'starting':   0,
  'structure':  0,
  'analysis':   0,
  'refs':       1,
  'references': 1,
  'llm':        2,
  'editorial':  2,
  'building':   3,
  'finalizing': 3,
  'done':       3,
};

let _currentStep = -1;

function _activateStep(index) {
  if (index <= _currentStep) return;   // never go backwards
  PROC_STEPS.forEach((s, i) => {
    const el = document.getElementById(s.id);
    if (!el) return;
    el.classList.remove('active', 'done');
    if (i < index)      el.classList.add('done');
    else if (i === index) el.classList.add('active');
  });
  _currentStep = index;
}
let _stepTimers = [];
let _crawlTimer = null;
let _elapsedTimer = null;
let _elapsedSeconds = 0;
let _processingAbortController = null;
let _processingCancelled = false;
let _pollDelayTimer = null;
let _pollDelayResolve = null;

function _startElapsedTimer() {
  _elapsedSeconds = 0;
  const el = document.getElementById('proc-timer');
  if (el) el.textContent = '0s elapsed';
  _elapsedTimer = setInterval(() => {
    _elapsedSeconds++;
    const m = Math.floor(_elapsedSeconds / 60);
    const s = _elapsedSeconds % 60;
    const label = m > 0 ? `${m}m ${s}s elapsed` : `${s}s elapsed`;
    const el = document.getElementById('proc-timer');
    if (el) el.textContent = label;
  }, 1000);
}

function _stopElapsedTimer() {
  if (_elapsedTimer) { clearInterval(_elapsedTimer); _elapsedTimer = null; }
}

function _waitForPoll(ms) {
  return new Promise(resolve => {
    _pollDelayResolve = resolve;
    _pollDelayTimer = setTimeout(() => {
      _pollDelayTimer = null;
      _pollDelayResolve = null;
      resolve();
    }, ms);
  });
}

function _clearPollDelay() {
  if (_pollDelayTimer) {
    clearTimeout(_pollDelayTimer);
    _pollDelayTimer = null;
  }
  if (_pollDelayResolve) {
    _pollDelayResolve();
    _pollDelayResolve = null;
  }
}

function setProgress(pct) {
  pct = Number(pct);
  if (!Number.isFinite(pct)) return;
  pct = Math.max(0, Math.min(100, Math.round(pct)));
  const bar   = document.getElementById('proc-progress');
  const label = document.getElementById('proc-pct');
  if (bar)   bar.style.width = pct + '%';
  if (label) label.textContent = pct + '%';
}

// Only ever move the bar forward — never backwards.
// The backend occasionally returns the same or lower value during
// rapid polls; this guard ensures the bar is always monotonically increasing.
let _lastProgress = 0;
function setBackendProgress(pct) {
  pct = Number(pct);
  if (!Number.isFinite(pct)) return;
  pct = Math.max(0, Math.min(100, Math.round(pct)));
  if (pct > _lastProgress) {
    _lastProgress = pct;
    setProgress(pct);
  }
}

function startStepAnimation(filename) {
  const docName = document.getElementById('proc-doc-name');
  if (docName) docName.textContent = filename;
  _currentStep = -1;
  PROC_STEPS.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) el.classList.remove('active', 'done');
  });
  setProgress(0);
  _lastProgress = 0;
  _startElapsedTimer();
  _activateStep(0);  // activate step 1 immediately on start
}

function finishStepAnimation() {
  _stepTimers.forEach(t => clearTimeout(t));
  _stepTimers = [];
  if (_crawlTimer) { clearInterval(_crawlTimer); _crawlTimer = null; }
  _stopElapsedTimer();
  _clearPollDelay();
  stopJutlpArticleRotation();
  PROC_STEPS.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) { el.classList.remove('active'); el.classList.add('done'); }
  });
  setProgress(100);
}

function resetStepAnimation() {
  _stepTimers.forEach(t => clearTimeout(t));
  _stepTimers = [];
  if (_crawlTimer) { clearInterval(_crawlTimer); _crawlTimer = null; }
  _stopElapsedTimer();
  _clearPollDelay();
  stopJutlpArticleRotation();
  _currentStep = -1;
  PROC_STEPS.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) el.classList.remove('active', 'done');
  });
  setProgress(0);
  _lastProgress = 0;
}

// ── JUTLP article rotation ───────────────────────────────────────────────────
function renderJutlpArticle(article) {
  const safeArticle = article || JUTLP_FALLBACK_ARTICLE;
  const title = safeArticle.title || JUTLP_FALLBACK_ARTICLE.title;
  const author = safeArticle.author || '';
  const abstract = safeArticle.abstract || JUTLP_FALLBACK_ARTICLE.abstract;
  const url = safeArticle.url || JUTLP_FALLBACK_ARTICLE.url;

  const titleEl = document.getElementById('jutlp-article-title');
  const authorEl = document.getElementById('jutlp-article-author');
  const abstractEl = document.getElementById('jutlp-article-abstract');
  const linkEl = document.getElementById('jutlp-article-link');

  if (titleEl) titleEl.textContent = title;
  if (authorEl) {
    authorEl.textContent = author ? `By ${author}` : '';
    authorEl.hidden = !author;
  }
  if (abstractEl) abstractEl.textContent = abstract;
  if (linkEl) linkEl.href = url;
  updateJutlpNextButton();
}

function updateJutlpNextButton() {
  const btn = document.getElementById('jutlp-article-next');
  if (!btn) return;
  btn.disabled = false;
}

async function fetchJutlpArticles(signal) {
  try {
    const res = await fetch(`${API_BASE}/api/jutlp-articles`, { signal });
    if (!res.ok) throw new Error('Article feed unavailable');
    const data = await res.json();
    return Array.isArray(data.articles) ? data.articles : [];
  } catch (e) {
    if (e.name !== 'AbortError') {
      console.warn('JUTLP article feed unavailable:', e);
    }
    return [];
  }
}

async function showNextJutlpArticle(forceRefresh = false) {
  if (forceRefresh || _jutlpArticles.length <= 1) {
    const freshArticles = await fetchJutlpArticles();
    if (freshArticles.length) {
      _jutlpArticles = freshArticles;
    }
  }

  if (!_jutlpArticles.length) {
    renderJutlpArticle(JUTLP_FALLBACK_ARTICLE);
    return;
  }

  if (_jutlpArticles.length === 1) {
    _jutlpArticleIndex = 0;
    renderJutlpArticle(_jutlpArticles[0]);
    return;
  }

  let nextIndex = Math.floor(Math.random() * _jutlpArticles.length);
  if (nextIndex === _jutlpArticleIndex) {
    nextIndex = (nextIndex + 1) % _jutlpArticles.length;
  }
  _jutlpArticleIndex = nextIndex;
  renderJutlpArticle(_jutlpArticles[_jutlpArticleIndex]);
}

function resetJutlpRotationTimer() {
  if (_jutlpRotateTimer) {
    clearInterval(_jutlpRotateTimer);
    _jutlpRotateTimer = null;
  }
  if (_jutlpArticles.length > 1) {
    _jutlpRotateTimer = setInterval(showNextJutlpArticle, JUTLP_ROTATE_MS);
  } else {
    _jutlpRotateTimer = setInterval(() => showNextJutlpArticle(true), JUTLP_ROTATE_MS);
  }
}

async function nextJutlpArticle() {
  await showNextJutlpArticle(true);
  resetJutlpRotationTimer();
}
window.nextJutlpArticle = nextJutlpArticle;

async function startJutlpArticleRotation() {
  stopJutlpArticleRotation();
  _jutlpArticles = [JUTLP_FALLBACK_ARTICLE];
  _jutlpArticleIndex = 0;
  renderJutlpArticle(JUTLP_FALLBACK_ARTICLE);

  _jutlpAbortController = new AbortController();
  try {
    const res = await fetch(`${API_BASE}/api/jutlp-articles`, {
      signal: _jutlpAbortController.signal,
    });
    if (!res.ok) throw new Error('Article feed unavailable');
    const data = await res.json();
    const articles = Array.isArray(data.articles) ? data.articles : [];
    _jutlpArticles = articles.length ? articles : [JUTLP_FALLBACK_ARTICLE];
    _jutlpArticleIndex = 0;
    renderJutlpArticle(_jutlpArticles[0]);
  } catch (e) {
    if (e.name !== 'AbortError') {
      console.warn('JUTLP article feed unavailable:', e);
    }
    _jutlpArticles = [JUTLP_FALLBACK_ARTICLE];
    _jutlpArticleIndex = 0;
    renderJutlpArticle(JUTLP_FALLBACK_ARTICLE);
  }

  resetJutlpRotationTimer();
}

function stopJutlpArticleRotation() {
  if (_jutlpRotateTimer) {
    clearInterval(_jutlpRotateTimer);
    _jutlpRotateTimer = null;
  }
  if (_jutlpAbortController) {
    _jutlpAbortController.abort();
    _jutlpAbortController = null;
  }
}

// ── Phase switching ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Phase 0 (password) is handled server-side via /login. Visiting / when not
  // authenticated redirects to /login automatically (see app/main.py).
  const phases = ['upload', 'processing', 'result'];

  function showPhase(name) {
    phases.forEach(p => {
      const el = document.getElementById('phase-' + p);
      if (!el) return;
      el.style.display = (p === name) ? 'flex' : 'none';
    });
  }

  showPhase('upload');

  const nextArticleBtn = document.getElementById('jutlp-article-next');
  if (nextArticleBtn) {
    nextArticleBtn.addEventListener('click', nextJutlpArticle);
  }
  updateJutlpNextButton();

  // ── Dropzone ──────────────────────────────────────────────────────────────
  const dz = document.getElementById('dropzone');

  dz.addEventListener('dragover', e => {
    e.preventDefault();
    dz.classList.add('drag-over');
  });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('drag-over');
    const f = e.dataTransfer.files[0];
    if (f) displayFile(f);
  });
  document.getElementById('file-input').addEventListener('change', function () {
    if (this.files[0]) displayFile(this.files[0]);
  });

  function displayFile(f) {
    clearUploadError();
    document.getElementById('sel-name').textContent = f.name;
    document.getElementById('sel-size').textContent =
      (f.size / 1024).toFixed(0) + ' KB · ' + f.name.split('.').pop().toUpperCase() + ' Document';
    document.getElementById('file-selected').classList.add('show');
    dz.style.display = 'none';
    document.getElementById('submit-btn').disabled = false;
    window._selectedFile = f;
  }

  window.removeFile = function () {
    clearUploadError();
    document.getElementById('file-selected').classList.remove('show');
    document.getElementById('file-input').value = '';
    dz.style.display = '';
    document.getElementById('submit-btn').disabled = true;
    window._selectedFile = null;
  };

  // ── Submit / processing ───────────────────────────────────────────────────
  function showUploadError(message) {
    const el = document.getElementById('upload-error');
    if (!el) return;
    el.textContent = message || 'Something went wrong. Please try again.';
    el.hidden = false;
  }

  function clearUploadError() {
    const el = document.getElementById('upload-error');
    if (el) { el.hidden = true; el.textContent = ''; }
  }

  window.cancelProcessing = async function () {
    _processingCancelled = true;
    _clearPollDelay();
    if (_processingAbortController) {
      _processingAbortController.abort();
      _processingAbortController = null;
    }

    const sessionId = window._sessionId;
    window._sessionId = null;
    if (sessionId) {
      fetch(`${API_BASE}/api/cancel/${sessionId}`, { method: 'POST' }).catch(() => {});
    }

    resetStepAnimation();
    showPhase('upload');
    document.getElementById('submit-btn').disabled = !window._selectedFile;
  };

  window.startProcessing = async function () {
    const fname = window._selectedFile ? window._selectedFile.name : 'document.docx';
    clearUploadError();
    _processingCancelled = false;
    _processingAbortController = new AbortController();
    window._sessionId = null;
    _lastProgress = 0;   // reset monotonic guard for new submission
    showPhase('processing');
    startStepAnimation(fname);
    startJutlpArticleRotation();

    const formData = new FormData();
    formData.append('file', window._selectedFile);

    let apiData = null;
    try {
      const uploadRes = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
        signal: _processingAbortController.signal,
      });
      if (_processingCancelled) return;
      if (!uploadRes.ok) {
        const err = await uploadRes.json().catch(() => ({}));
        throw new Error(err.error || 'Upload failed');
      }
      const { session_id } = await uploadRes.json();
      window._sessionId = session_id;

      let pollDelay = 2000;
      while (true) {
        if (_processingCancelled) return;
        const res = await fetch(`${API_BASE}/api/results/${session_id}`, {
          signal: _processingAbortController.signal,
        });
        if (_processingCancelled) return;
        if (res.status === 202) {
          const pollData = await res.json().catch(() => ({}));
          // Drive progress bar from real backend value
          setBackendProgress(pollData.progress);
          // Drive step labels from backend stage string
          const stepIndex = STAGE_TO_STEP[pollData.stage];
          if (typeof stepIndex === 'number') {
            _activateStep(stepIndex);
          }
          pollDelay = 2000;
          await _waitForPoll(pollDelay);
          continue;
        }
        if (res.status === 409) {
          _processingCancelled = true;
          resetStepAnimation();
          showPhase('upload');
          document.getElementById('submit-btn').disabled = !window._selectedFile;
          return;
        }
        if (res.status === 429) {
          pollDelay = Math.min(pollDelay * 2, 16000);
          await _waitForPoll(pollDelay);
          continue;
        }
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.error || 'Pipeline failed');
        }
        apiData = await res.json();
        break;
      }
    } catch (e) {
      if (_processingCancelled || e.name === 'AbortError') {
        return;
      }
      console.error('API error:', e);
      resetStepAnimation();
      showPhase('upload');
      showUploadError(e && e.message ? e.message : 'Something went wrong. Please try again.');
      document.getElementById('submit-btn').disabled = false;
      return;
    } finally {
      _processingAbortController = null;
      _clearPollDelay();
    }

    if (_processingCancelled) return;
    finishStepAnimation();
    showResult(fname, apiData);
  };

  // ── Tab switching ─────────────────────────────────────────────────────────
  window.showTab = function (name) {
    document.querySelectorAll('.tab-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.tab === name);
    });
    document.querySelectorAll('.tab-panel').forEach(p => {
      p.classList.toggle('active', p.id === 'tab-' + name);
    });
  };

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => showTab(btn.dataset.tab));
  });

  // ── Show result ───────────────────────────────────────────────────────────
  function showResult(fname, data) {
    let outputName = '';
    if (data && data.output_filename) {
      outputName = data.output_filename;
    } else {
      const baseName = fname.replace(/\.(docx?|pdf)$/i, '');
      outputName = baseName + '_reviewed.docx';
    }
    document.getElementById('res-filename').textContent = outputName;
    showPhase('result');

    if (!data) return;

    window._downloadUrl = data.download_url;

    document.getElementById('res-total').textContent = data.total_notes ?? '—';
    document.getElementById('res-high').textContent  = data.high_priority ?? '—';

    const crefPass = (data.ref_verifications || []).filter(r => r.status === 'pass').length;
    const crefFail = (data.ref_verifications || []).filter(r => r.status === 'fail').length;
    document.getElementById('res-refs-verified').textContent = crefPass;
    document.getElementById('res-refs-failed').textContent   = crefFail;

    // Stage-error banner — shown when one or more post-processing stages
    // (acronym, decimal, hyperlinking, etc.) failed silently in the pipeline.
    const stageErrors = Array.isArray(data.stage_errors) ? data.stage_errors : [];
    const stageBanner = document.getElementById('stage-error-banner');
    if (stageBanner) {
      if (stageErrors.length > 0) {
        const items = stageErrors.map(e => {
          const stage = (e && e.stage) ? String(e.stage) : 'Unknown stage';
          const err = (e && e.error) ? String(e.error) : '';
          return `<li><strong>${stage}</strong>${err ? ' — ' + err : ''}</li>`;
        }).join('');
        stageBanner.innerHTML =
          '<strong>Heads up:</strong> some post-processing stages did not complete. ' +
          'The reviewed document is still available, but it may be missing one or ' +
          'more of these corrections.<ul>' + items + '</ul>';
        stageBanner.hidden = false;
      } else {
        stageBanner.innerHTML = '';
        stageBanner.hidden = true;
      }
    }

    // Split issues by source
    const allIssues       = data.issues || [];
    const validatorIssues = allIssues.filter(i => i.source !== 'llm' && i.source !== 'sam');
    const llmIssues       = allIssues.filter(i => i.source === 'llm');
    const samIssues       = allIssues.filter(i => i.source === 'sam');

    // Structural & style issues
    const issuesSection = document.getElementById('issues-section');
    const issuesList    = document.getElementById('issues-list');
    if (validatorIssues.length > 0) {
      const renderValidator = issue => {
        const badgeClass = issue.status === 'fail' ? 'badge-high' : 'badge-warn';
        const badgeLabel = issue.status === 'fail' ? 'Required' : 'Advisory';
        return `<div class="issue-row">
          <span class="issue-badge ${badgeClass}">${badgeLabel}</span>
          <span class="issue-msg">${issue.message}</span>
        </div>`;
      };
      issuesList.innerHTML = renderGrouped(groupItems(validatorIssues, i => i.message), renderValidator);
      issuesSection.style.display = '';
    }

    // AI editorial notes — grouped by paper section in canonical JUTLP order
    // (Introduction → Literature → Method → Results → Discussion →
    // Conclusion), with anything else collected under "Other" at the end.
    // Groups are collapsible; click the heading to fold/unfold.
    const llmSection = document.getElementById('llm-section');
    const llmList    = document.getElementById('llm-list');

    // Canonical group order. Each entry: { key, label, aliases }.
    // `key` is the normalised lookup, `label` is what the user sees, and
    // `aliases` are the lower-case strings the LLM might emit for that
    // section (matches app/domain/canonical_jultp_template.py).
    const LLM_SECTION_GROUPS = [
      { key: 'introduction', label: 'Introduction', aliases: ['introduction'] },
      { key: 'literature',   label: 'Literature',
        aliases: ['literature', 'literature review', 'review of literature'] },
      { key: 'method',       label: 'Method',
        aliases: ['method', 'methods', 'methodology'] },
      { key: 'results',      label: 'Results',
        aliases: ['results', 'findings', 'results and discussion',
                  'findings and discussion'] },
      { key: 'discussion',   label: 'Discussion', aliases: ['discussion'] },
      { key: 'conclusion',   label: 'Conclusion',
        aliases: ['conclusion', 'conclusions'] },
    ];
    const OTHER_GROUP = { key: 'other', label: 'Other', aliases: [] };

    function normaliseSection(raw) {
      const s = String(raw || '').trim().toLowerCase();
      if (!s) return OTHER_GROUP.key;
      for (const g of LLM_SECTION_GROUPS) {
        if (g.aliases.includes(s)) return g.key;
      }
      return OTHER_GROUP.key;
    }

    function renderLlmNoteRow(note) {
      const severityClass = note.status === 'fail' ? 'badge-high' : 'badge-warn';
      const severityLabel = note.status === 'fail' ? 'Requires Attention' : 'Advisory';
      return `<div class="issue-row">
        <span class="issue-badge ${severityClass}">${severityLabel}</span>
        <span class="issue-msg">${note.message}</span>
      </div>`;
    }

    if (llmIssues.length > 0) {
      // Bucket each note by canonical section key.
      const buckets = new Map();
      for (const note of llmIssues) {
        const key = normaliseSection(note.section);
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push(note);
      }

      // Render in canonical order, then "Other" at the end if non-empty.
      const orderedGroups = LLM_SECTION_GROUPS.concat([OTHER_GROUP])
        .map(g => ({ ...g, notes: buckets.get(g.key) || [] }))
        .filter(g => g.notes.length > 0);

      llmList.innerHTML = orderedGroups.map((g, idx) => {
        const rows = renderGrouped(groupItems(g.notes, n => n.message), renderLlmNoteRow);
        const groupId = `llm-group-${g.key}`;
        const collapsed = idx > 0;
        return `<div class="llm-group ${collapsed ? 'collapsed' : ''}" data-group="${g.key}">
          <button type="button" class="llm-group-header" aria-expanded="${!collapsed}" aria-controls="${groupId}">
            <span class="llm-group-caret" aria-hidden="true">▾</span>
            <span class="llm-group-label">${g.label}</span>
            <span class="llm-group-count">${g.notes.length}</span>
          </button>
          <div class="llm-group-body" id="${groupId}" ${collapsed ? 'hidden' : ''}>${rows}</div>
        </div>`;
      }).join('');

      llmList.querySelectorAll('.llm-group-header').forEach(btn => {
        btn.addEventListener('click', () => {
          const group = btn.closest('.llm-group');
          const body = group.querySelector('.llm-group-body');
          const nowCollapsed = !group.classList.contains('collapsed');
          group.classList.toggle('collapsed', nowCollapsed);
          btn.setAttribute('aria-expanded', String(!nowCollapsed));
          if (nowCollapsed) body.setAttribute('hidden', '');
          else body.removeAttribute('hidden');
        });
      });
      llmSection.style.display = '';
    } else if (data.llm_error) {
      llmList.innerHTML = `<div class="issue-row">
        <span class="issue-badge">Notice</span>
        <span class="issue-msg">AI review unavailable — ${data.llm_error}</span>
      </div>`;
      llmSection.style.display = '';
    }

    // Sam's format & tracked-changes notes
    const samSection = document.getElementById('sam-section');
    const samList    = document.getElementById('sam-list');
    if (samSection && samList && samIssues.length > 0) {
      const renderSam = note => {
        const severityClass = note.status === 'fail' ? 'badge-high' : 'badge-warn';
        const severityLabel = note.status === 'fail' ? 'Requires Attention' : 'Advisory';
        return `<div class="issue-row">
          <span class="issue-badge ${severityClass}">${severityLabel}</span>
          <span class="issue-msg">${note.message}</span>
        </div>`;
      };
      samList.innerHTML = renderGrouped(groupItems(samIssues, n => n.message), renderSam);
      samSection.style.display = '';
    }

    // Language corrections (spelling + grammar)
    const langCorrections = data.language_corrections || [];
    const langSection     = document.getElementById('lang-section');
    const langList        = document.getElementById('lang-list');
    if (langSection && langList && langCorrections.length > 0) {
      const renderLang = c => {
        const typeMap = {
          grammar:  { cls: 'badge-grammar', label: 'Grammar'  },
          spelling: { cls: 'badge-spell',   label: 'Spelling' },
          typo:     { cls: 'badge-typo',    label: 'Typo'     },
        };
        const { cls, label } = typeMap[c.type] || { cls: 'badge-spell', label: 'Spelling' };
        const reason = c.reason && c.type !== 'spelling'
          ? `<span class="issue-reason">${c.reason}</span>` : '';
        const grouped = c.type === 'spelling' && c.grouped_repeats > 0
          ? `<span class="issue-reason">${c.grouped_repeats} later repeat${c.grouped_repeats > 1 ? 's' : ''} grouped</span>` : '';
        return `<div class="issue-row lang-row">
          <span class="lang-check">✓</span>
          <span class="issue-badge ${cls}">${label}</span>
          <span class="issue-msg"><span class="lang-del">${c.original}</span> → <span class="lang-ins">${c.replacement}</span>${reason}${grouped}</span>
        </div>`;
      };
      langList.innerHTML = renderGrouped(groupItems(langCorrections, c => c.original + '→' + c.replacement), renderLang);
      langSection.style.display = '';
    }

    // Reference verifications
    const refs        = data.ref_verifications || [];
    const consItems   = refs.filter(r => r.rule_id.startsWith('CONS'));
    const alphaItems  = refs.filter(r => r.rule_id === 'REF003');
    const crefItems   = refs.filter(r => !r.rule_id.startsWith('CONS') && r.rule_id !== 'REF003');

    const renderRef = ref => {
      const pass     = ref.status === 'pass';
      const warn     = ref.status === 'warn';
      const doiMatch = ref.message.match(/https?:\/\/doi\.org\/\S+/);
      const msgText  = ref.message.replace(/https?:\/\/doi\.org\/\S+/, '').trim();
      const doiLink  = doiMatch
        ? `<a class="ref-doi" href="${doiMatch[0]}" target="_blank" rel="noopener">${doiMatch[0]}</a>`
        : '';
      const badgeClass = pass ? 'badge-pass' : warn ? 'badge-warn' : 'badge-high';
      const badgeLabel = pass ? 'Verified' : warn ? 'Check' : 'Issue';
      return `<div class="issue-row">
        <span class="issue-badge ${badgeClass}">${badgeLabel}</span>
        <span class="issue-msg">${msgText} ${doiLink}</span>
      </div>`;
    };

    const consSection  = document.getElementById('cons-section');
    const consList     = document.getElementById('cons-list');
    if (consItems.length > 0) {
      consList.innerHTML = consItems.map(renderRef).join('');
      consSection.style.display = '';
    }

    const alphaSection = document.getElementById('alpha-section');
    const alphaList    = document.getElementById('alpha-list');
    if (alphaItems.length > 0) {
      alphaList.innerHTML = alphaItems.map(renderRef).join('');
      alphaSection.style.display = '';
    }

    const refsSection = document.getElementById('refs-section');
    const refsList    = document.getElementById('refs-list');
    const crefFailed = crefItems.filter(r => r.status !== 'pass' || r.rule_id.startsWith('HREF'));
    if (crefFailed.length > 0) {
      const sortedRefs = [...crefFailed].sort((a, b) => (a.status === 'pass') - (b.status === 'pass'));
      refsList.innerHTML = renderGrouped(groupItems(sortedRefs, r => r.rule_id + '|' + r.message.replace(/https?:\/\/doi\.org\/\S+/, '').trim()), renderRef);
      refsSection.style.display = '';
    }

    // ── Tab counts + empty states + auto-switch ──────────────────────────
    const structureCount  = validatorIssues.length + samIssues.length;
    const editorialCount  = llmIssues.length + (data.llm_error ? 1 : 0);
    const languageCount   = langCorrections.length;
    const referencesCount = consItems.length + crefFailed.length;

    const tabCountData = {
      structure:  structureCount,
      editorial:  editorialCount,
      language:   languageCount,
      references: referencesCount,
    };

    const visibleCategoryData = {
      structure:  structureCount,
      frontpage:  (data.categories || {})['Front Page'] || 0,
      references: referencesCount,
      editorial:  editorialCount,
    };
    const maxCategoryValue = Math.max(...Object.values(visibleCategoryData), 1);

    Object.entries(visibleCategoryData).forEach(([key, val]) => {
      const cntEl = document.getElementById('cnt-' + key);
      const barEl = document.getElementById('bar-' + key);
      if (cntEl) cntEl.textContent = val;
      if (barEl) barEl.style.width = Math.round((val / maxCategoryValue) * 100) + '%';
    });

    const styleRow = document.getElementById('cat-row-style');
    if (styleRow) styleRow.hidden = true;
    const styleCnt = document.getElementById('cnt-style');
    const styleBar = document.getElementById('bar-style');
    if (styleCnt) styleCnt.textContent = '0';
    if (styleBar) styleBar.style.width = '0%';

    Object.entries(tabCountData).forEach(([tab, count]) => {
      const countEl = document.getElementById('tc-' + tab);
      const btnEl   = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
      if (countEl) countEl.textContent = count || '—';

      // Show empty-state message if the panel has no populated sections
      const panel = document.getElementById('tab-' + tab);
      if (panel) {
        const hasSections = Array.from(panel.querySelectorAll('.issues-section'))
          .some(s => s.style.display !== 'none');
        const emptyEl = document.getElementById('tab-empty-' + tab);
        if (emptyEl) emptyEl.style.display = hasSections ? 'none' : '';
        if (btnEl) btnEl.classList.toggle('tab-has-issues',
          Array.from(panel.querySelectorAll('.issue-badge.badge-high')).length > 0);
      }
    });

    // Auto-switch to first tab with content, default to editorial
    const tabOrder   = ['editorial', 'structure', 'language', 'references'];
    const firstActive = tabOrder.find(name => {
      const panel = document.getElementById('tab-' + name);
      return panel && Array.from(panel.querySelectorAll('.issues-section'))
        .some(s => s.style.display !== 'none');
    });
    showTab(firstActive || 'editorial');
  }

  // ── Download ──────────────────────────────────────────────────────────────
  window.triggerDownload = function () {
    if (window._downloadUrl) {
      window.location.href = `${API_BASE}${window._downloadUrl}`;
    }
  };

  // ── Start over ────────────────────────────────────────────────────────────
  window.startOver = function () {
    resetStepAnimation();
    window._selectedFile = null;
    window._downloadUrl  = null;
    document.getElementById('file-input').value = '';
    document.getElementById('file-selected').classList.remove('show');
    dz.style.display = '';
    document.getElementById('submit-btn').disabled = true;

    document.querySelectorAll('.cat-bar').forEach(b => b.style.width = '0%');
    ['cnt-structure','cnt-frontpage','cnt-style','cnt-references','cnt-editorial'].forEach(id => {
      document.getElementById(id).textContent = '0';
    });
    const styleRow = document.getElementById('cat-row-style');
    if (styleRow) styleRow.hidden = true;

    ['issues-section', 'llm-section', 'sam-section', 'lang-section', 'cons-section', 'alpha-section', 'refs-section'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    });
    ['issues-list', 'llm-list', 'sam-list', 'lang-list', 'cons-list', 'alpha-list', 'refs-list'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = '';
    });
    ['structure', 'editorial', 'language', 'references'].forEach(tab => {
      const countEl = document.getElementById('tc-' + tab);
      if (countEl) countEl.textContent = '—';
      const emptyEl = document.getElementById('tab-empty-' + tab);
      if (emptyEl) emptyEl.style.display = 'none';
      const btn = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
      if (btn) btn.classList.remove('tab-has-issues');
    });
    showTab('editorial');

    showPhase('upload');
  };

});
