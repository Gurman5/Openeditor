Here's the revised brief:

---

# Dev Tasks — OpenEditor Demo (Frontend Only)

> Split:
  Humaid → happy path (screens 01–06) 
  Gurman → wrong file type + cancel + solo demo

Both developers work from the Figma file: *OpenEditor — Concept A (OAPA). All screens are `1440×900` white frames with content at `x120` and the OAPA signature block (`220×54`) at `1100,726`. The four-segment progress indicator sits at `y80` — black for completed steps, `#C7C7C7` for pending. Error states replace it with a single `1200×4` black bar.

**No backend integration this sprint.** All processing is simulated via Alpine state transitions and hardcoded mock data. The `/api/*` endpoints are not wired up.

**Code contract (both):** New template `app/templates/writer.html` at route `/openeditor`. No Flask auth gate. HTMX + Alpine via CDN, no build step. Reuse tokens from `app/static/style.css`. Run locally via `python -m app.main` → `http://127.0.0.1:5009`.

---

## Humaid — Happy Path (screens 01–06)

### H1 · Upload (`01-upload`, `1:10`)

Dashed dropzone (`1200×280`, radius 2, dash `[6,5]`) with heading, lead copy, and pill limits (`.docx only · 20 MB · 15,000 words`). Alpine tracks selected file name and size. Submit button stays disabled until a file is chosen. On selection, Alpine transitions state to checking — no POST fired.

**Acceptance:**

- [x] Layout, copy, and pill limits match `01-upload`
- [ ] Submit stays disabled with no file selected
- [ ] Valid file selection transitions to checking via Alpine state change

---

### H2 · Checking + Processing (`02-checking` `2:2` · `03-processing` `2:28`)

**Checking** plays through four hardcoded rows (File type / File size / Word count / Document readable) with ■/□ markers and `1200×1 #C7C7C7` dividers. Each row resolves on a short `setTimeout` delay to simulate validation. *Nothing is charged…* sits below.

**Processing** shows the `1200×3` progress track with an animated black fill, an Alpine `setInterval` elapsed timer (*Elapsed 1:42 · Stops at 5:00*), and a Secondary Cancel button. After a fixed timeout, Alpine auto-advances to results.

**Acceptance:**

- [ ] Checklist rows, markers, dividers, and timer match `02` and `03`
- [ ] Rows resolve sequentially with visible delay; timer ticks in real time
- [ ] Screen auto-advances to results after the simulated processing duration

---

### H3 · Results, Upgrade, Download (`04-results` `2:42` · `05-upgrade` `2:73` · `06-download` `2:94`)

**Results** shows hardcoded correction counts in the two-column layout — left column black (free tier fixes), right column `#737373` muted (locked full-version items). Italic aside below. Two buttons: *Download free version* [Secondary] and *See the full version* [Primary].

**Upgrade** shows the two `580×400` cards (Free `1px` border / Full `2px` selected border) with their respective copy and buttons.

**Download** shows the hardcoded filename, the one-time-access note, a Primary *Download manuscript* button (no actual file returned), and a muted *Process another file* link that resets Alpine state to upload.

**Acceptance:**

- [ ] Counts, locked-muted column, card borders, and one-time copy match `04`, `05`, `06`
- [ ] *Process another file* resets Alpine state cleanly back to upload
- [ ] Tabs (Editorial / Structure / Language / References) switch via Alpine `x-show`

---

## Gurman — Wrong File Type + Cancel + Solo Demo

### G1 · Wrong file type error (`08-blocked` variant)

Client-side only. When a non-`.docx` / non-`.rtf` file is selected, show the `1200×4` black error bar and the relevant blocked copy (*Unsupported file type* variant from `08`). No POST is fired. *Upload a different file* [Primary] resets to the upload screen. *Nothing was charged.* note visible.

**Acceptance:**

- [ ] Wrong file type triggers the error bar and correct copy before any network request
- [ ] *Upload a different file* resets to upload screen cleanly
- [ ] *Nothing was charged.* note is present

---

### G2 · Cancel button (`03-processing`)

On the processing screen, Cancel [Secondary] resets Alpine state back to the upload screen. No API call required — the button just clears state and returns to step 1.

**Acceptance:**

- [ ] Cancel appears on the processing screen matching the `03` design
- [ ] Clicking Cancel returns to the upload screen with state fully reset
- [ ] Progress indicator resets to step 1

---

### G3 · Solo demo to Joey and Michael

Prep for the demonstration during the client meeting

Demo order: **(1)** full happy path — upload a `.docx` through to the download screen,  
**(2)** wrong file type rejection,  
**(3)** cancel the job mid-processing. All three are frontend-only;

Prep for talking points during demo. Prep for talking points if Alpine state breaks live.

**Acceptance:**

- [ ] All three demo scenarios run end-to-end in the browser without errors
- [ ] Dry run completed with Humaid and Zac
- [ ] Fallback ready if something breaks  

