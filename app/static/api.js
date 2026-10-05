/**
 * OpenEditor data layer — G-07 handoff module.
 *
 * Wraps every backend call the frontend needs: upload, poll, cancel, and the
 * carousel feed. Humaid's screens import from here rather than calling
 * fetch() directly, so all the endpoint/error-code details live in one place.
 *
 * See docs/api-contract.md for the full contract this module implements.
 */

// Toggle for the abstract carousel — pending Joey sign-off (see G-03).
// Set to false to disable the carousel entirely without removing the code.
export const CAROUSEL_ENABLED = true;

// Stage string -> UI step number, matching STAGE_TO_STEP in the old script.js.
const STAGE_TO_STEP = {
  starting: 0, structure: 0, analysis: 0,
  refs: 1, references: 1,
  llm: 2, editorial: 2,
  building: 3, finalizing: 3, done: 3,
};

export function stageToStep(stage) {
  return STAGE_TO_STEP[stage] ?? 0;
}

/**
 * Upload a manuscript. Returns { session_id } on success.
 * Throws an Error with .errorCode and .payload attached on failure, so
 * callers can branch on the specific G-02 error code.
 */
export async function uploadManuscript(file) {
  const formData = new FormData();
  formData.append("file", file);

  let response;
  try {
    response = await fetch("/api/upload", { method: "POST", body: formData });
  } catch {
    // Network failure mid-upload — no response at all.
    const err = new Error("Network error during upload.");
    err.errorCode = "NETWORK_FAIL";
    throw err;
  }

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const err = new Error(payload.error || "Upload failed.");
    err.errorCode = _mapUploadErrorCode(response.status, payload);
    err.payload = payload;
    throw err;
  }

  return payload; // { session_id }
}

function _mapUploadErrorCode(status, payload) {
  if (status === 413) return "TOO_LARGE";
  if (payload.word_count !== undefined) return "OVER_WORD_LIMIT";
  if ((payload.error || "").toLowerCase().includes("no file")) return "EMPTY";
  if ((payload.error || "").toLowerCase().includes(".docx")) return "BAD_TYPE";
  // FAKE_DOCX / CORRUPT / PASSWORD_LOCKED are not yet distinguishable from the
  // backend — see docs/api-contract.md G-02 "Action required" note. Until
  // that backend work lands, these all fall through to a generic code.
  return "UPLOAD_FAILED";
}

/**
 * Poll once for results. Returns the raw parsed payload plus response.status,
 * so callers can branch on 202 (still processing) vs 200 (done) vs error codes.
 */
export async function pollResults(sessionId) {
  const response = await fetch(`/api/results/${sessionId}`);
  const payload = await response.json().catch(() => ({}));
  return { status: response.status, payload };
}

/**
 * Poll repeatedly until done/cancelled/timeout/error, calling onProgress
 * after every poll. Returns the final payload. Stops polling once a
 * terminal status is reached.
 *
 * @param {string} sessionId
 * @param {(payload: object, step: number) => void} onProgress
 * @param {{ intervalMs?: number, clientTimeoutMs?: number }} [options]
 */
export function pollUntilDone(sessionId, onProgress, options = {}) {
  const intervalMs = options.intervalMs ?? 1500;
  // Slightly after the server's own 10-min ceiling, so the server's clean
  // timeout message always wins over a generic client-side give-up message.
  const clientTimeoutMs = options.clientTimeoutMs ?? 10 * 60 * 1000 + 5000;

  let stopped = false;
  const startedAt = Date.now();

  const cancel = () => { stopped = true; };

  const promise = new Promise((resolve, reject) => {
    const tick = async () => {
      if (stopped) return;

      if (Date.now() - startedAt > clientTimeoutMs) {
        stopped = true;
        reject(Object.assign(new Error("Client-side timeout waiting for results."), {
          errorCode: "TIMEOUT",
        }));
        return;
      }

      let result;
      try {
        result = await pollResults(sessionId);
      } catch {
        // Transient network hiccup while polling — retry on next tick
        // rather than failing the whole flow immediately.
        setTimeout(tick, intervalMs);
        return;
      }

      const { status, payload } = result;

      if (status === 202) {
        onProgress(payload, stageToStep(payload.stage));
        setTimeout(tick, intervalMs);
        return;
      }

      if (status === 200) {
        resolve(payload); // done — full results payload
        return;
      }

      // 409 cancelled, 504 timeout, 500 error, 404 not found — all terminal.
      const err = new Error(payload.error || "Processing failed.");
      err.errorCode =
        status === 409 ? "CANCELLED" :
        status === 504 ? "TIMEOUT" :
        status === 404 ? "SESSION_NOT_FOUND" :
        "PIPELINE_ERROR";
      err.payload = payload;
      reject(err);
    };

    tick();
  });

  return { promise, cancel };
}

/**
 * Cancel an in-progress job. Not instant server-side — the pipeline stops
 * cooperatively at its next checkpoint. Caller should still immediately
 * treat the UI as "returning to Upload" per the Z-03 guarantee.
 */
export async function cancelJob(sessionId) {
  const response = await fetch(`/api/cancel/${sessionId}`, { method: "POST" });
  return response.json().catch(() => ({}));
}

/**
 * Fetch carousel articles. Respects CAROUSEL_ENABLED — returns an empty
 * array immediately without calling the backend if the flag is off.
 */
export async function fetchCarouselArticles(limit = 10) {
  if (!CAROUSEL_ENABLED) return { articles: [], degraded: false };
  try {
    const response = await fetch(`/api/jutlp-articles?limit=${limit}`);
    const payload = await response.json();
    return {
      articles: payload.articles || [],
      degraded: Boolean(payload.degraded),
    };
  } catch {
    // Total failure → degraded, so the UI can say so instead of silently
    // showing the fallback.
    return { articles: [], degraded: true };
  }
}

export function downloadUrl(sessionId) {
  return `/api/download/${sessionId}`;
}