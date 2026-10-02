import { uploadManuscript, pollUntilDone, cancelJob, fetchCarouselArticles, downloadUrl, CAROUSEL_ENABLED } from './api.js';

document.addEventListener('alpine:init', () => {
  Alpine.data('openEditorApp', () => ({
    currentPhase: 'upload',
    selectedFile: null,
    isDragOver: false,
    fileError: null,
    sessionId: null,
    uploadError: null,

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
    jutlpArticleIndex: 0,
    jutlpRotateTimer: null,
    showCancelConfirm: false,
    showLeaveConfirm: false,

    // ─── RESULTS state ───
    totalCorrections: 34,
    freeItems: [
      { label: 'Heading hierarchy', status: '12 FIXED' },
      { label: 'Line spacing and margins', status: '9 FIXED' },
      { label: 'In-text citation format', status: '8 FIXED' },
      { label: 'Title page and running head', status: '5 FIXED' }
    ],
    reviewItems: [
      { label: '6 references could not be verified' },
      { label: '2 DOIs did not resolve' },
      { label: '1 table caption format unclear' }
    ],
    hasDownloaded: false,
    resultsPayload: null,

    get fileSizeLabel() {
      if (!this.selectedFile) return '';
      const mb = this.selectedFile.size / (1024 * 1024);
      return mb.toFixed(1) + ' MB';
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
            this.currentPhase = 'timeout';
          } else {
            console.error('Processing failed:', err);
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

    get currentArticle() {
      return this.jutlpArticles[this.jutlpArticleIndex];
    },

    async fetchJutlpArticles() {
      const articles = await fetchCarouselArticles();
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