"""Few-shot editorial examples extracted from real JUTLP editor decisions.

These calibrate the LLM's judgment by showing what editors actually changed
vs. kept in real submissions.
"""

EDITORIAL_EXAMPLES = """\
## Editorial Calibration Examples

Below are real examples of editorial decisions made by JUTLP editors. Use \
these to calibrate the severity and relevance of your feedback.

### Example 1: Title — when to flag vs. keep

KEPT UNCHANGED: "Enhance Learning Environments Using Knowledge Flow: A Living \
Systems, Neuroscience-based Model" (13 words, colon-separated subtitle, clear)
→ This title uses the standard "Main Title: Subtitle" format recommended by \
JUTLP guidelines. It is 13 words (under the 15-word limit) and clearly \
conveys the topic. Do NOT flag it. Colon-separated subtitles, technical \
terms, and compound modifiers (e.g. "Neuroscience-based") are normal in \
academic titles.

KEPT UNCHANGED: "What and How: Investigating the Use of Student Evaluations \
in Scholarship of Teaching and Learning Research" (15 words, within limit)
→ Even at exactly 15 words, this title is within guidelines and should not \
be flagged.

CHANGED: "Exploring how student evaluation of teaching (SETs) data are being \
used in studies of teaching and learning" (17 words, reads as a sentence, \
lacks focus)
→ Flag titles that exceed 15 words or read as a full sentence rather than \
a focused title.

RULE: Before flagging any title for length, count the words. If the title \
is 15 words or fewer, do NOT flag it for length. Only flag titles for \
content issues if they are genuinely unclear or misleading.

### Example 2: Abstract — when to flag

FLAGGED BY EDITOR: An abstract that stated the topic and methods but reported \
no specific findings or implications. Editor rewrote to include problem, \
method, key results, and implications.
→ Flag abstracts that are missing any of the five required elements: problem \
statement, theoretical framework, method, key findings, and implications.

KEPT UNCHANGED: An abstract that concisely covered all five elements in a \
single paragraph.
→ Do not flag abstracts that cover all required elements, even if wording \
could be improved.

### Example 3: Practitioner notes — requires_attention when missing or weak

FLAGGED BY EDITOR: Paper had no practitioner notes. Editor wrote all five \
from scratch based on the paper's findings.
→ When practitioner notes exist, check whether they are action-oriented \
and practice-focused. Vague or overly academic statements should be flagged.

### Example 4: Acknowledgements — AI disclosure

KEPT UNCHANGED: "The authors acknowledge not using AI tools or technologies \
to prepare this article."
→ This is a valid AI disclosure. Do not flag papers that clearly state AI \
was not used. Only flag when the disclosure is ambiguous or missing entirely.

### Example 5: Introduction — research questions

FLAGGED BY EDITOR: An introduction that clearly described the background, \
identified a gap in practice, and outlined the paper's structure — but never \
explicitly stated research questions. Editor added: "This study therefore \
asks: (1) How do students experience... (2) What factors influence..."
→ Research questions are a firm expectation for JUTLP. If the introduction \
does not include at least one explicitly stated research question (usually \
near the end), flag it at HIGH severity. Framing such as "this paper \
explores..." or "we aim to investigate..." is NOT a substitute for clearly \
stated research questions.

KEPT UNCHANGED: An introduction that ended with: "This study therefore \
addresses the following research questions: (1) To what extent do blended \
learning formats affect student engagement? (2) How do instructors adapt \
their facilitation strategies in response?"
→ Clearly stated, numbered research questions at the end of the \
introduction. Do not flag.

### Example 6: Method — reflexivity and positionality

FLAGGED BY EDITOR: A qualitative study using thematic analysis with no \
reflexivity or positionality statement anywhere in the Method section. \
Editor requested a short paragraph acknowledging the researchers' \
backgrounds and how these may have shaped data collection and analysis.
→ For qualitative studies, the absence of a reflexivity or positionality \
statement should be flagged at MEDIUM severity. It need not be long — one \
short paragraph is sufficient.

KEPT UNCHANGED: A quantitative survey study with no reflexivity paragraph. \
→ Reflexivity is strongly recommended but not required for quantitative \
studies. Do not flag its absence in quantitative or mixed-methods papers \
unless the paper has an obvious interpretive dimension that is unaddressed.

### Example 7: Discussion — interpreting results vs. repeating them

FLAGGED BY EDITOR: A discussion section that opened by restating each \
finding in sequence ("The results showed that...", "It was also found \
that...") with no connection to prior literature or the practice problem. \
Editor noted: "This section largely repeats the results. Please reframe \
each finding in relation to what the literature says and what it means for \
practice."
→ Flag discussions that describe findings without interpreting them. The \
discussion must connect results to the research questions, to existing \
literature, and to practical implications — not just restate what was found. \
Flag at MEDIUM or HIGH depending on severity.

KEPT UNCHANGED: A discussion that opened by revisiting the research \
questions and then situated each finding within relevant prior work, \
explaining how the results extended, confirmed, or challenged earlier studies.
→ This is the correct structure. Do not flag.

### Example 8: Conclusion — no new results

FLAGGED BY EDITOR: A conclusion that introduced a new finding in its final \
paragraph — a subgroup effect not mentioned anywhere in the Results section. \
Editor removed it and noted: "Conclusions must not introduce new findings."
→ Flag any conclusion that mentions a result, claim, or data point that \
does not appear in the Results or Discussion sections. Flag at HIGH severity.

KEPT UNCHANGED: A conclusion that summarised the main findings, linked them \
to the practice problem, and ended with a brief note on wider significance — \
all drawn from content already in the paper.
→ Do not flag conclusions that stay within the bounds of what was already \
presented.

### Example 9: Acknowledgements — CRediT contributions

FLAGGED BY EDITOR: Acknowledgements section that included funding and \
AI disclosure but no CRediT author contribution statement.
→ CRediT contributions are mandatory for JUTLP. If the acknowledgements \
section does not include a statement attributing specific contributions \
to named authors (e.g. "Conceptualization: J. Smith; Methodology: A. Jones; \
Writing – original draft: J. Smith, A. Jones"), flag it at HIGH severity. \
See https://credit.niso.org/ for the full taxonomy.

KEPT UNCHANGED: "Author contributions: Conceptualization, J.S. and A.B.; \
Methodology, J.S.; Formal analysis, A.B.; Writing – original draft, J.S.; \
Writing – review & editing, A.B.; Funding acquisition, J.S."
→ This is a valid CRediT statement. Do not flag.
"""
