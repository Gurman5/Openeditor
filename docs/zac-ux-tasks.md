# Z-01 -- Lock Concept A IA: 4 screens + states map

Effort: S · Deps: none · Priority: P0

Objective: Produce one agreed screen map so Z-02–Z-09 all build from the same base. Therefore  nothing would be duplicated  .

Context: The current writer.html has 6 named phases (upload / checking / processing / results / upgrade / download) with a confused "STEP X OF 4" counter. Concept A (wizard flow) is confirmed. The upgrade/paywall screen from the current prototype is scrapped — Joey confirmed members get the full output for free, non-members pay ~$5 AUD, but the product is identical either way.

Do:

Map 4 canonical screens: Upload → Processing → Results → Download + "process another"
Decide where Checking lives (inline sub-state of Processing, or its own transition step)
For each screen, list which error/edge conditions are handled inline, modal, or banner
Define how the 4-step progress indicator maps across all screens
Note that APA 7 is the only style sheet for MVP — no selector shown unless >1 style exists (Joey's explicit ask — design should accommodate this future case without cluttering the current UI)

Don't: No visual polish, no paywall screen, no history/library states.

Deliverable: 1-page IA diagram + state inventory table (screen → error → pattern).

Acceptance criteria: Every scenario from User Flow §8 has an assigned home; team gives sign-off before Z-02 starts; "STEP X OF 4" numbering is resolved.

Refs: Ideation Concept A; User Flow §9–10; transcript (Joey: "less is more").

# Z-02 -- Upload page: validation + error states

Effort: M · Deps: Z-01 · Priority: P0

Objective: User knows exactly why a file is rejected before anything is submitted to the backend.

Context: Current prototype says ".docx or .rtf" (.doc/.x only for MVP; .doc status TBC with Dev). Joey confirmed wrong-type errors should stay on the same upload page as inline red text, not navigate to a separate error screen ("people will get lost, like, how do I go back?"). "Nothing was charged" copy also needs to go — there's no free vs. full split.

Do:

Drag-drop + browse; display upload rules (20 MB, ~15k words, .docx only) before the user picks a file
Inline red-text error states (no separate page) for: wrong type ( .pdf / .bat / .exe / .php / .html), fake .docx (wrong content), >20 MB, over word limit, empty file, corrupted file, password-protected file, network fail mid-upload
Continue button disabled until a valid file is loaded
Fix ".docx or .rtf" wording to ".doc/.docx only"
Remove "Nothing was charged" copy entirely

Don't: No backend validation logic (Dev owns that); no conversion of non-.docx files; no separate error page.

Deliverable: Upload screen design + error copy deck (one message per failure mode).

Acceptance criteria: Every error case shows a specific message on the same page (e.g. "This file type is not supported. Please upload a Microsoft Word document (.docx)."); Continue stays disabled on any error; Joey's inline-error feedback from the meeting is fully addressed.

Refs: FR-04–09; PRD §11; User Flow §2, §8; transcript (Joey: "just kind of like put it like a red line… on that first page").

# Z-03 — Processing screen: status + carousel + Cancel/timeout

Effort: M · Deps: Z-01 · Priority: P0

Objective: User trusts the system hasn't frozen during a 2–3 minute run.

Context: Current prototype simulates 5 seconds and hardcodes "STOPS AT 5:00". Joey confirmed CopyBot currently takes 2–3 minutes, which is normal. PRD specifies a ~10 min timeout ceiling. The abstract carousel exists in index.html but is missing from writer.html. Joey confirmed a Cancel button is wanted.

Do:

Show filename prominently (Joey's W2 feedback)
Live progress indicator (loading bar confirmed; change hardcoded percentages as final design — mark as Dev-dependency)
"Still working / longer manuscripts take a few minutes" message
Rotating abstracts carousel (port from index.html)
Elapsed time display + 10:00 timeout ceiling (fix current 5:00)
Cancel button → confirm dialog → cancelled state → returns to fresh Upload (no retained file)
Timeout state: "Unable to finish processing your manuscript. Please try again." → returns to Upload

Don't: Don't hardcode fake progress percentages as final behaviour; mark Cancel feasibility as a Dev open question (annotate for Z-09 handoff).

Deliverable: Processing screen + two exit states (cancelled, timed-out).

Acceptance criteria: Filename always visible; carousel rotates; both Cancel and timeout paths return cleanly to Upload; elapsed time buffer

Refs: FR-14–18; User Flow §3–4; transcript (Joey: "2 to 3 minutes… have some kind of way of measuring progress"; Gurman: "we will have the cancel button").

# Z-04 — Results screen: issues vs. no-issues + track changes context

Effort: M · Deps: Z-01 · Priority: P1

Objective: User always lands on a Results screen with a clear picture of what changed and a clear next action.

Context: Current prototype splits Results into Free vs. Locked/$12 — scrapped. Joey clarified the output is CopyBot's track-changes model: the bot edits the Word XML and surfaces changes as Word track changes. Zac raised the question of showing the document being scanned vs. just showing the end result — Joey said ideally show both clean and tracked-changes views; if only one, tracked changes.

Do:

Two states: (a) issues found — what was auto-changed, what was flagged for user review, what still needs attention; (b) no issues — success message ("Your manuscript was processed successfully. No major formatting issues were found.")
In the issues-found state, show what was auto-fixed vs. what needs the user's own correction (mirrors the track-changes model)
Successful checks list visible in both states
If feasible within design scope, propose a "clean vs. tracked" toggle for the preview (flag as Dev dependency if not)
Remove all paywall/free-vs-full copy

Don't: No payment UI; no document history; no per-journal formatting options.

Deliverable: Results screen, 2 states; optional tracked-vs-clean toggle proposal for Dev discussion.

Acceptance criteria: Zero-issue runs still reach Results (not a blank or error); auto-fixed items are visually distinguished from flagged/needs-action items; no paywall copy remains.

Refs: FR-19–21; User Flow §5; transcript (Joey: "track version… if it makes an error… simple enough for them to see that change has been made"; Zac: "highlight them… visibility for somebody putting their document in").

# Z-05 — Download + process-another guard

Effort: S · Deps: Z-04 · Priority: P1

Objective: User doesn't lose their only copy of the processed file.

Context: Joey confirmed: no history, no storage — file is deleted after first download or after 24 hours (Darian's proposal, confirmed fine). The current prototype doesn't surface this to the user.

Do:

Prominent Download button
Visible note: "This is the only time you can download your processed file. It will be deleted after you leave this page."
"Process another document" → guard modal: "Have you downloaded your file? It will not be saved." → confirm → returns to fresh Upload (no retained file)
Post-download state: allow "process another" without the guard (they've already downloaded)

Don't: No history/library/queue UI; no "processed file" storage or re-download.

Deliverable: Download screen + guard modal copy.

Acceptance criteria: Navigating away or choosing "process another" before downloading triggers the warning; post-download flow resets cleanly; copy matches Joey's confirmed deletion model.

Refs: FR-22–26; User Flow §6–7; transcript (Darian/Joey: "output will be deleted after the first download or after 24 hours… that's all fine").



Z-07 — NEW PROPOSAL: Support / error-log + feedback (pending Joey/client sign-off)

Effort: M · Deps: Z-01, Z-02 · Priority: P2 — scope decision required

Objective: User can report a failure or send feedback without exposing their manuscript.

Context: Not in current PRD/MVP scope. Needs Joseph/client approval before any design work starts. Privacy constraint is firm: no manuscript retention (FR-25/26, and Joey confirmed "it doesn't need to store it anywhere"). Z-07 should be raised at the next client check-in as a proposal.

Do :

Entry points: footer link + all error screens + Results screen
Form fields: issue type (bug / feedback), auto-populated error code or session ID, filename (text, not the file), free-text description, optional contact email
Submission route: email or GitHub issue (no DB, no stored manuscripts)
Define what is explicitly not sent: file contents, manuscript text
Confirm triage owner (Joey/Sam?) and expected response time

Don't: No file attachments by default; no stored history; no live chat; no building this until client OK is received.

Deliverable (once approved): Support page/modal spec + field list + privacy note.

Acceptance criteria: Every error state links to support with a pre-filled error code; submission never retains the manuscript; triage owner is named.

Refs: NFR security/privacy; User Flow §8; no PRD ref — flag this explicitly.



# Z-09 —   Dev handoff

Effort: M · Deps: Z-02–Z-07 · Priority: P2

Objective: Humaid and Gurman can build against these screens without guessing on intent or open questions.

Context: The Figma prototype (Concept A, 9 screens) is the current reference; this task updates it to reflect Z-01–Z-08 and annotates it with Dev questions .

Do:

Flag open Dev questions/suggestions explicitly per screen via annotations /comments:
Cancel: feasibility + how the backend job is stopped (Humaid/Gurman)
Word count method: loaded from client-side pre-check vs. backend validation
Partial pipeline failure: what does the user see if the job fails mid-run?
Temp file delete timing: immediately post-download or on session end?
MemberPress token method and expiry handling (Humaid)
Style sheet selector: how does the frontend know whether >1 style is available?
Track-changes preview: is a clean vs. tracked toggle feasible in the results payload?
List the props/events Dev needs per screen (file object, progress updates, cancel signal, timeout flag, results payload structure)


Deliverable: Updated linked prototype + handoff to Dev.

Acceptance criteria: Every screen maps to FRs; every open Dev question has a named owner; Zac, Humaid, and Gurman agree on Cancel/timeout/word-count approach



# DONT DO (  Archived coz im not sure)



# Z-06 — MemberPress access states

Effort: S · Deps: Z-01 · Priority: P1

Objective: The tool is members-only with no second login screen inside OpenEditor itself.

Context: Joey confirmed the architecture: OpenEditor lives behind a MemberPress member wall on the OAPA WordPress site. Members access the full tool for free. Non-members hit a public-facing page that requires payment (~$5 AUD). The two entry points are separate pages — same product, different access gate. Token handoff from WordPress → Flask is Dev's responsibility; Zac annotates it as a dependency.

Do:

Design the member entry state (user arrives already authenticated — no login form inside OpenEditor)
Denied/no-membership message for anyone who somehow reaches the URL without a valid session
Session-expired-mid-use state (e.g. token expires during a long processing run) → prompt to re-login, note that in-progress job is lost
Placeholder for the public-facing paid entry point (same UI, different access gate — flag for Dev)

Don't: No OpenEditor-native login or signup form; no payment/checkout UI inside the tool; no WP account management.

Deliverable: 3 access states + copy; note on dual-entry-point architecture for Dev handoff.

Acceptance criteria: Non-member (no valid session) cannot reach the Upload screen; session expiry mid-use is handled gracefully; no native login form exists inside OpenEditor.

Refs: FR-01–03; PRD §7; User Flow §1, §8; transcript (Joey: "member-only page… only members can kind of get access… a different one that they have to go through some kind of dollar wall").

# Z-08 — Copy + plain-language + accessibility/responsive pass

Effort: S · Deps: Z-02–Z-05 · Priority: P2

Objective: Usable by non-technical academic writers (PhD students, researchers) on desktop and mobile, including keyboard-only users.

Context: Target users are academics, not technical. Joey confirmed "less is more". Remove any remaining paywall copy. PRD NFR §10 covers simplicity and accessibility.

Do:

Plain-English copy sweep across all screens — aim for ~Grade 8 reading level, no jargon
Remove all remaining "Nothing was charged" / "See the full version" copy
Keyboard-operable drop zone and progress indicator
ARIA-live regions for status changes (processing progress, carousel rotation, phase transitions)
Focus management on screen transitions
360px mobile viewport check across all screens

Don't: No IA changes; no new screens.

Deliverable: Copy sheet (final strings per screen) + accessibility checklist applied to Z-02–Z-05.

Acceptance criteria: All interactive elements keyboard-reachable; status changes announced to screen readers; no paywall copy remains anywhere; 360px layout holds.

Refs: PRD §4, §10 NFR; transcript (Joey: "less is more in this case").