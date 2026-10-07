import { uploadManuscript, pollUntilDone, cancelJob, fetchCarouselArticles, downloadUrl, CAROUSEL_ENABLED } from './api.js';

document.addEventListener('alpine:init', () => {
  Alpine.data('openEditorApp', () => ({
    currentPhase: 'upload',
    selectedFile: null,
    isDragOver: false,
    fileError: null,
    sessionId: null,
    uploadError: null,
    processingError: null,

    processingPercent: 0,
    elapsedSeconds: 0,
    elapsedTimer: null,
    pollHandle: null,
    carouselEnabled: CAROUSEL_ENABLED,
    jutlpArticles: [{
      title: 'The Artificial Intelligence Assessment Scale (AIAS): A Framework for Ethical Integration of Generative AI in Educational Assessment',
      author: 'Mike Perkins, Leon Furze, Jasper Roe, Jason MacVaugh',
      abstract: 'This JUTLP article introduces the AI Assessment Scale as a practical framework for deciding when and how generative AI can be used in educational assessment.',
      url: 'https://open-publishing.org/journals/index.php/jutlp/article/view/810/769'
    }],
    carouselDegraded: false,
    jutlpArticleIndex: 0,
    jutlpRotateTimer: null,
    showCancelConfirm: false,
    showLeaveConfirm: false,
    hasDownloaded: false,
    resultsPayload: null,
    showCleanCopyNote: false,
    showReferences: false,
    showVerified: false,
    openGroups: [],

    get fileSizeLabel() {
      if (!this.selectedFile) return '';
      const mb = this.selectedFile.size / (1024 * 1024);
      return mb.toFixed(1) + ' MB';
    },

    get manualReviewItems() {
      if (!this.resultsPayload) return [];
      const issueFails = (this.resultsPayload.issues || []).filter(i => i.status === 'fail');
      const refFails = (this.resultsPayload.ref_verifications || []).filter(r => r.status === 'fail');
      return [...issueFails, ...refFails];
    },

    get manualReviewGroups() {
      const map = new Map();
      for (const item of this.manualReviewItems) {
        const label = this._manualReviewCategory(item.rule_id);
        if (!map.has(label)) map.set(label, []);
        map.get(label).push(item);
      }
      return [...map.entries()].map(([label, items]) => ({ label, count: items.length, items }));
    },

    _manualReviewCategory(ruleId) {
      if (/^(CREF|HREF|DOIT|CONS|REF)/.test(ruleId)) return 'References and citations';
      if (/^(SEC|MET|DIS|CON|SPE|FIG|TAB)/.test(ruleId)) return 'Structure';
      if (/^(FP|AFF)/.test(ruleId)) return 'Front page';
      if (/^STY/.test(ruleId)) return 'Style';
      if (/^LLM/.test(ruleId)) return 'Editorial';
      if (/^SAM/.test(ruleId)) return 'Front page';
      return 'Other';
    },

    referenceStatusLabel(status) {
      return { verified: 'Verified', doi_mismatch: 'DOI mismatch', not_found: 'Not found' }[status] || status;
    },
    toggleGroup(label) {
      this.openGroups[label] = !this.openGroups[label];
    },
    viewReferences() { this.showReferences = true; },
    backToResults() { this.showReferences = false; },
    toggleVerified() { this.showVerified = !this.showVerified; },
    notFoundExplanation(kind) {
      if (kind === 'thesis') return 'Theses are often not in Crossref. Check it against the original.';
      if (kind === 'report') return 'Reports and grey literature are often not in Crossref. Check it against the original.';
      return 'We could not confirm this reference in Crossref. Check the author, year and title.';
    },

    get manualReviewTotal() {
      return this.manualReviewItems.length;
    },

    get changesMadeGroups() {
      if (!this.resultsPayload) return [];
      return (this.resultsPayload.changes_made || {}).groups || [];
    },

     get sortedReferences() {
      if (!this.resultsPayload) return [];
      const order = { not_found: 0, doi_mismatch: 1, verified: 2 };
      return [...(this.resultsPayload.references || [])]
        .sort((a, b) => (order[a.status] ?? 3) - (order[b.status] ?? 3));
    },
    get references() {
      return this.resultsPayload ? (this.resultsPayload.references || []) : [];
    },
    get notFoundReferences()  { return this.references.filter(r => r.status === 'not_found'); },
    get doiMismatchReferences() { return this.references.filter(r => r.status === 'doi_mismatch'); },
    get verifiedReferences()  { return this.references.filter(r => r.status === 'verified'); },
    get attentionCount() { return this.notFoundReferences.length + this.doiMismatchReferences.length; },
    get totalReferences() { return this.references.length; },

    get changesMadeTotal() {
      if (!this.resultsPayload) return 0;
      return (this.resultsPayload.changes_made || {}).total || 0;
    },

    get downloadFileLabel() {
      if (!this.resultsPayload) return '';
      return this.resultsPayload.output_filename || this.resultsPayload.filename || '';
    },
     get isCleanResult() {
      return this.resultsPayload
        && this.manualReviewTotal === 0
        && this.changesMadeTotal === 0;
    },
    get wordCount() {
      return this.resultsPayload ? (this.resultsPayload.word_count || 0) : 0;
    },
    get referenceCount() {
      return this.resultsPayload ? (this.resultsPayload.reference_count || 0) : 0;
    },
    init() {
      window.onbeforeunload = () => {
        if ((this.currentPhase === 'results' || this.currentPhase === 'upgrade' || this.currentPhase === 'download') && !this.hasDownloaded) {
          return 'You have a completed report you have not downloaded yet.';
        }
      };
    },

    onFileSelected(event) {
      this.applyFile(event.target.files[0]);
    },

    async onFileDropped(event) {
      const file = event.dataTransfer.files[0];
      await this.applyFile(file);
      const input = document.getElementById('file-input');
      if (input && this.selectedFile) input.files = event.dataTransfer.files;
    },

    async applyFile(file) {
      if (!file) return;
      this.selectedFile = null;
      this.fileError = null;

      const fail = (message) => {
        this.fileError = message;
        const input = document.getElementById('file-input');
        if (input) input.value = '';
      };

      if (!file.name.toLowerCase().endsWith('.docx')) {
        return fail('This file type is not supported. Please upload a Microsoft Word document (.docx).');
      }

      const maxMb = window.MAX_UPLOAD_MB || 20;

      if (file.size > maxMb * 1024 * 1024) {
        return fail(`This file is larger than ${maxMb} MB. Please upload a smaller file.`);
      }

      const readable = await this.checkReadable(file);
      if (readable === 'locked') {
        return fail('This file is password protected. Remove the password and upload it again.');
      }
      if (readable === 'corrupt') {
        return fail('This file could not be read. Please check it opens in Word and try again.');
      }

      this.selectedFile = file;
    },

    async checkReadable(file) {
      const b = new Uint8Array(await file.slice(0, 4).arrayBuffer());
      if (b[0] === 0x50 && b[1] === 0x4B) return 'ok';
      if (b[0] === 0xD0 && b[1] === 0xCF && b[2] === 0x11 && b[3] === 0xE0) return 'locked';
      return 'corrupt';
    },

    removeFile() {
      this.selectedFile = null;
      const input = document.getElementById('file-input');
      if (input) input.value = '';
    },

    get canSubmit() {
      return !!this.selectedFile && !this.fileError;
    },

    get elapsedFormatted() {
      const m = Math.floor(this.elapsedSeconds / 60);
      const s = this.elapsedSeconds % 60;
      return `${m}:${s.toString().padStart(2, '0')}`;
    },

    stepNumber() {
      if (this.currentPhase === 'upload') return 1;
      if (this.currentPhase === 'processing' || this.currentPhase === 'cancelled' || this.currentPhase === 'timeout') return 2;
      if (this.currentPhase === 'results' || this.currentPhase === 'upgrade') return 3;
      return 4;
    },

    // ─── REAL upload + processing ───
    async startProcessing() {
      if (!this.canSubmit) return;
      this.currentPhase = 'processing';
      this.processingPercent = 0;
      this.elapsedSeconds = 0;
      this.uploadError = null;
      this.processingError = null;

      this.elapsedTimer = setInterval(() => {
        this.elapsedSeconds++;
      }, 1000);

      this.fetchJutlpArticles().then(() => this.startJutlpRotation());

      try {
        const { session_id } = await uploadManuscript(this.selectedFile);
        this.sessionId = session_id;
      } catch (err) {
        clearInterval(this.elapsedTimer);
        this.stopJutlpRotation();
        this.uploadError = err.message || 'Upload failed. Please try again.';
        this.fileError = this.uploadError;
        this.currentPhase = 'upload';
        return;
      }

      this.pollHandle = pollUntilDone(
        this.sessionId,
        (payload) => {
          this.processingPercent = payload.progress ?? this.processingPercent;
        }
      );

      this.pollHandle.promise
        .then((resultsPayload) => {
          clearInterval(this.elapsedTimer);
          this.stopJutlpRotation();
          this.resultsPayload = resultsPayload;
          this.currentPhase = 'results';
        })
        .catch((err) => {
          clearInterval(this.elapsedTimer);
          this.stopJutlpRotation();
          if (err.errorCode === 'CANCELLED') {
            this.currentPhase = 'cancelled';
          } else if (err.errorCode === 'TIMEOUT') {
            this.processingError = null;
            this.currentPhase = 'timeout';
          } else {
            console.error('Processing failed:', err);
            this.processingError = `${err.errorCode || 'ERROR'}: ${err.message || 'Unknown error'}`;
            this.currentPhase = 'timeout';
          }
        });
    },

    requestCancel() {
      this.showCancelConfirm = true;
    },

    async confirmCancel() {
      this.showCancelConfirm = false;
      if (this.pollHandle) this.pollHandle.cancel();
      if (this.sessionId) {
        try {
          await cancelJob(this.sessionId);
        } catch (err) {
          console.warn('Cancel request failed:', err);
        }
      }
      if (this.elapsedTimer) clearInterval(this.elapsedTimer);
      this.stopJutlpRotation();
      this.selectedFile = null;
      const input = document.getElementById('file-input');
      if (input) input.value = '';
      this.currentPhase = 'cancelled';
    },

    keepProcessing() {
      this.showCancelConfirm = false;
    },

    resetToUpload() {
      if (this.pollHandle) this.pollHandle.cancel();
      if (this.elapsedTimer) clearInterval(this.elapsedTimer);
      this.selectedFile = null;
      this.hasDownloaded = false;
      this.sessionId = null;
      this.currentPhase = 'upload';
      const input = document.getElementById('file-input');
      if (input) input.value = '';
    },

    goToUpgrade() {
      this.currentPhase = 'upgrade';
    },
    goToDownload() {
      this.currentPhase = 'download';
    },

    downloadManuscript() {
      if (this.sessionId) {
        window.location.href = downloadUrl(this.sessionId);
      }
      this.hasDownloaded = true;
    },
    
    requestCleanCopy() {
      this.showCleanCopyNote = true;
    },

    get currentArticle() {
      return this.jutlpArticles[this.jutlpArticleIndex];
    },

     async fetchJutlpArticles() {
      const { articles, degraded } = await fetchCarouselArticles();
      this.carouselDegraded = degraded;
      if (articles.length) {
        this.jutlpArticles = articles;
        this.jutlpArticleIndex = 0;
      }
    },

    nextJutlpArticle() {
      if (this.jutlpArticles.length <= 1) return;
      let nextIndex = Math.floor(Math.random() * this.jutlpArticles.length);
      if (nextIndex === this.jutlpArticleIndex) {
        nextIndex = (nextIndex + 1) % this.jutlpArticles.length;
      }
      this.jutlpArticleIndex = nextIndex;
    },

    startJutlpRotation() {
      this.stopJutlpRotation();
      if (this.jutlpArticles.length > 1) {
        this.jutlpRotateTimer = setInterval(() => this.nextJutlpArticle(), 150000);
      }
    },

    stopJutlpRotation() {
      if (this.jutlpRotateTimer) {
        clearInterval(this.jutlpRotateTimer);
        this.jutlpRotateTimer = null;
      }
    },

    retryProcessing() {
      this.resetToUpload();
    },

    requestProcessAnother() {
      if (this.hasDownloaded) {
        this.resetToUpload();
      } else {
        this.showLeaveConfirm = true;
      }
    },

    downloadFirst() {
      this.showLeaveConfirm = false;
      this.downloadManuscript();
    },

    continueWithoutDownloading() {
      this.showLeaveConfirm = false;
      this.resetToUpload();
    },
  }));
});