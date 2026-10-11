# Zac 2.3 — Z-07 … Z-11 rewritten + Z-11 error contract

> Rework of the Z-07 → Z-11 tickets against the code as it actually stands.  
> Every claim below is line-referenced to the current tree; where a ticket's  
> original premise turned out to be wrong, that is called out rather than  
> silently dropped.
> Related: `docs/api-contract.md` (G-01, the live contract — its error tables  
> are stale, see Z-11).

---

## Preface ( corrections to the original tickets ; dev related)

**1. The frontend under review is `writer.html` + `openeditor.js` + `api.js`,**  
**not `index.html` + `script.js`.**  
`app/main.py:461` renders `writer.html` at `/`. `index.html` and `script.js`  
are the previous CopyBot UI, still in the tree but not served. Any analysis of  
the old files (including the "advertises `.doc`" and "reads `err.error`"  
observations from the first pass) applies to dead code, not to users.  
**Decision needed for devs:** delete the dead files or leave them? They are a  
maintenance hazard


**3. The upload screen already implements four of Z-11's six error variants.**  
`openeditor.js:69-103` validates file type, size, password-protection  
(via the `D0 CF 11 E0` OLE magic) and corruption (magic-byte check) before  
the request is sent. The original ticket's "define positive and error  
variants" is therefore mostly done — the real problem is that the **client and**  
**server disagree about the limits**, and neither matches the other. See Z-11.

---


## Z-08a — Revised Results page

**Priority:** P0 · **Deps:** Z-04, G-04

### Goal

Revise for subtracted implementation of Results output;  leads with what the author needs to do next.


 

### What to change 


1.  "Changes made" and "Things to review" aren't parallel comparisons, so side by side they read as a scorecard. Stack them instead.





6. **Explain the download before the click.** The current line, "Review the changes in your downloaded document", doesn't say what the author will find. Replace it with something like "The Word file keeps every change as a tracked change and adds a margin comment explaining it, so nothing has been altered behind your back. Open it in Word, then use Review › Accept or Reject to decide what to keep."

Have a manual review header that would be a filter for things which cant be parsed or would amount to some conundrum.
 

### Sketch (text only)

```
STEP 3 OF 4 / REVIEW
Your manuscript has been reviewed
41 corrections were applied to your document. 9 items need a decision from you before you submit.


References and Citations
Every in-text citation was matched to a reference in your list, and each reference was checked against Crossref. [Six] could not be confirmed — 


Structure and front page

Spelling and grammar
Spelling, Australian English usage and acronym definitions were corrected. These are applied as tracked changes, so you can accept or reject each one in Word.

 Needs manual review
 

[ Continue ]
```
## Z-08b

Make 2 seperate screen that  would account for 
 No issues found,  and a corrupted document/document with batch scripts

something like
1.
Main header
 No issues found
We checked your document and found nothing to correct. This is not the same as an empty file — we read 6,240 words and checked [x] references

And a banner below it stating something like

Your document had nothing to correct, so this copy is identical to the file you uploaded. There are no tracked changes or comments to review.
with a Download reviewed document button 

2.
Main header
We could not review this document
with stuff about 
The file opened, but it contains no text we can read (0 words). This usually means the text is in text boxes, a table, or an image.

this would also account for a if a file has been mislabelled as docx?

then make a message stating maybe 
"Select all your text in Word, cut it, and paste it as plain text into a new blank document. Then save that as .docx and upload it again. Your file has been deleted — nothing was saved."

and a what to do section 

Or the file has malicious code , and cant be executed ,. ,with a upload a different file button for both screens

## Z-09: Download choice

**Priority:** P1 · **Deps:** Z-08, G-04

### Goal

Give the author two ways to take their document away, with the second marked as work in progress. Devs will build it later.

### Do

1. **Primary action: Download reviewed document.** Unchanged from Z-08. It sits first and carries the full visual weight.
2. **Add a secondary button: Download with all changes accepted.** It is outlined or text-style, so it never competes with the primary. The "Coming soon" tag sits inside the button, not beside it.
3. **Put one line of helper copy under each button:**
   - Primary: *"Keeps every change as a tracked change with a margin comment. Review them in Word."*
   - Secondary: *"Applies every OpenEditor change for you. You won't be able to accept or reject them one by one."*
4. **Keep the tracked-changes explanation from Z-08 visible above both buttons**, so the author has read it before choosing.

### The WIP behaviour

The button should look available but be honest when clicked. A greyed-out button reads as broken.

- Style it as a normal secondary button with a small **Coming soon** tag.
- On click, don't download anything. Show an inline message under the button: *"This option isn't available yet. For now, download the reviewed document and use Review › Accept All Changes in Word."*
- Zac should design three states: default, after click (message showing), and the later live state.

### Do not do

- **Don't grey the button out.** The click-through message above does that job without the "broken" signal.
- **Don't call it "clean copy".** It implies a better document, and accepting everything loses the author's ability to reject individual changes.
- **Don't let the secondary button outweigh the primary.** Most authors should still be steered to the reviewed document.

 
### Acceptance

- Two download actions, the primary visually dominant and the secondary clearly labelled as coming soon.
- Clicking the secondary never fails silently. It always explains what to do instead.
- The tracked-changes explanation is visible before either click.

### Dev note (not for Zac)

`build_edited_document` produces one file and `/api/download/<id>` serves one path (`main.py:1105-1110`). Accepting every tracked change and handling comments is real docx work in `output_generation_samfix.py`, and `api-contract.md:176` already logs it as not built this sprint. The frontend button can ship now as a stub with no backend change.

 ## Z-10: References and DOI click-through

**Priority:** P1 · **Deps:** Z-08, G-04 · **Blocked by:** backend work (see dev note)

### Goal

Let the author check their references from the Results page, without having to hunt through the Word file.

### Do
Make a screen that would 

1. **Show each reference as its own row, stacked in a single column**.
 Each row has author and year, title, status, DOI, and source link where available.


2. **Link the DOI text to `https://doi.org/{doi}`**, opening in a new tab.

3. **Design four statuses**, each with a distinct label and a one-line explanation:
   - **Verified:** matched in Crossref.
   - **Not found:** Crossref couldn't confirm this reference. Suggest the author check the details.
   - **DOI mismatch:** the DOI given doesn't match the reference. Show the DOI as text, not a link.
   - **Not checked:** the reference was skipped. Hold this one until Joey confirms it exists (see open questions).
4. **When no DOI is available, say so in plain words**, e.g. *"No DOI found for this reference."* Never leave an empty field or a dead link.
5. **Lead with problems.** Order rows as Not found, DOI mismatch, then Verified, so the author sees what needs attention first. Verified rows can be collapsed or suggest and design a better sorting approach 

6. **Connect it to Z-08.** The "References and Citations" group on the Results page should link to this list.

### Sketch (text only) please improve upon ideation ,below thing is just my brainstormed thing

```
REFERENCES AND CITATIONS
6 of 48 references need your attention.

Not found
  Nguyen, T. (2021). Title of the article…
  We couldn't confirm this reference. Check the details.
  No DOI found for this reference.

DOI mismatch
  Smith, J. (2019). Title of the article…
  The DOI doesn't match this reference.
  DOI: 10.1234/example (not linked)

Verified (42)  [expand]
  Lee, A. (2020). Title of the article…
  Verified · 10.5678/example ↗
```

### Do not do

- Don't link a DOI that's mismatched or missing.
- Don't show a "Not checked" state until the backend can produce it.
- Don't use red-alarm styling for "Not found". A reference can be real and simply not in Crossref.


### Acceptance

- Every valid DOI is clickable and opens in a new tab.
- Mismatched DOIs are clearly labelled and never linked.
- A missing DOI shows a helpful message, never a broken link or blank field.
- Each status has its own label and plain-language explanation.

### Dev note (not for Zac)

This can't be built from the current payload. `ref_verifications` is `{rule_id, status, message}` (`main.py:978-982`), and the DOI is buried in the prose `message`. The backend needs to return a structured `references[]` array with `raw_text`, `authors`, `year`, `title`, `doi`, `source_url` and `status`. `reference_checker.py:799` already loops the references, so the data exists at check time.

Status mapping:
- Verified: `CREF` pass (`:770`)
- Not found: CrossRef couldn't verify (`:780-784`)
- DOI mismatch: `:676-702`
- Not checked: no current equivalent

The frontend should not regex-parse the prose messages.


## Z-07 — Support and Help

**Priority:** P1 · **Deps:** Z-02, Z-11 (corrected — see below)

### Goal

A place to understand requirements, troubleshoot failures, and reach support —  
without exposing manuscripts.

### Do

make a screen for /about which would include infinite scrolling , ,make a 
privacy disclosure, 
further, make a write up of deterministic and  
non-deterministic output rendered by the application.

Further, make a support section wrtie up and a prompt for filling out a form that would simply be linked to a Google Form Suggest to PM , what questions we could poll from the userbase, and what we could extract from them.



## Z-11 — File requirements and plain-language copy

Priority: P1 · Deps: Z-02, G-01  
Goal: Ensure upload requirements are accurate and consistent.
Do:
- Define positive and error variants for:
- unsupported file type;
- file too large;
- too many words;
- empty file;
- corrupted/password-protected file;
- upload/network failure.
- Apply the same wording to Upload, Help, accessibility labels, and support prefill.
.
Acceptance: One requirements statement appears everywhere; every rejection explains the corrective action.

> please flag if already done im not sure if this was done before

## Completion 
- Mention and Link the References used, along with  states made.
- Document required API fields and backend dependencies.
- Define success measures