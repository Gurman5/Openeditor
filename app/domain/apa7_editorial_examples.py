"""Few-shot editorial examples for APA 7 manuscript review.

These calibrate the LLM's judgment by showing what an APA 7 copy editor
actually changes vs. keeps.
"""

APA7_EDITORIAL_EXAMPLES = """\
## Editorial Calibration Examples

Below are examples of copy-editing decisions made on APA 7 manuscripts. Use \
these to calibrate the severity and relevance of your feedback.

### Example 1: Title — flag only for genuine clarity problems

KEPT UNCHANGED: "Enhancing Learning Environments Through Knowledge Flow: A \
Neuroscience-Based Model" (colon-separated subtitle, title case, clear)
→ APA 7 titles use title case and commonly use the "Main Title: Subtitle" \
format. This title is clear and well formed. Do NOT flag it.
KEPT UNCHANGED: "What and How: Student Evaluations of Teaching in the \
Scholarship of Teaching and Learning"
→ A colon-separated title in title case with clear subject matter. Do NOT flag \
titles solely for length; APA 7 has no fixed word limit.

CHANGED: "exploring how student evaluation of teaching data are being used in \
studies of teaching and learning" (sentence case, reads as a sentence)
→ APA 7 titles should be in title case and read as a title, not a full \
sentence. Flag titles that are lowercase or read as a run-on sentence. \
Propose one or two title-cased alternatives rather than a single rewrite.

RULE: Only flag titles for content problems (case, clarity, misleading \
scope). Never flag a title purely for word count.

### Example 2: Abstract — completeness

FLAGGED BY EDITOR: An abstract that stated the topic and method but reported \
no findings or implications. Editor asked the author to add the key results \
and a sentence on implications.
→ Flag abstracts missing any of the core elements: problem/purpose, method, \
key findings, and implications.

KEPT UNCHANGED: A single-paragraph abstract that concisely covered purpose, \
method, results, and implications.
→ Do not flag an abstract that covers the core elements even if the wording \
could be tightened.

### Example 3: Introduction — framing the study

FLAGGED BY EDITOR: An introduction that described the background and a gap \
but never stated the study's purpose or aims clearly. Editor suggested a \
sentence near the end naming what the study set out to do.
→ APA 7 expects the introduction to establish the problem, the relevant \
literature, and the study's purpose. Flag a missing purpose statement at \
MEDIUM severity.

KEPT UNCHANGED: An introduction that closed with: "This study examined \
whether blended learning formats affect student engagement and how \
instructors adapt their facilitation in response."
→ A clear, explicit purpose statement. Do not flag.

### Example 4: Method — reflexivity

FLAGGED BY EDITOR: A qualitative study using thematic analysis with no \
reflexivity or positionality statement in the Method section. Editor requested \
a short paragraph acknowledging the researchers' backgrounds.
→ For qualitative studies, the absence of a reflexivity or positionality \
statement should be flagged at MEDIUM severity. One short paragraph suffices.

KEPT UNCHANGED: A quantitative survey study with no reflexivity paragraph.
→ Reflexivity is recommended but not required for quantitative studies. Do \
not flag its absence unless the study has an obvious interpretive dimension.

### Example 5: Discussion — interpreting, not repeating

FLAGGED BY EDITOR: A discussion that restated each finding in sequence \
("The results showed that...", "It was also found that...") without \
connecting them to prior literature or the research questions. Editor noted \
the section largely repeated the results.
→ Flag discussions that describe findings without interpreting them. The \
discussion must connect results to the research questions and prior work. \
Flag at MEDIUM or HIGH depending on severity.

KEPT UNCHANGED: A discussion that revisited the research questions and then \
situated each finding within relevant prior work, explaining how the results \
extended, confirmed, or challenged earlier studies.
→ Correct structure. Do not flag.

### Example 6: Conclusion — no new results

FLAGGED BY EDITOR: A conclusion that introduced a new finding in its final \
paragraph — a subgroup effect not mentioned in the Results section. Editor \
removed it and noted conclusions must not introduce new findings.
→ Flag any conclusion that mentions a result, claim, or data point not \
already presented in the Results or Discussion. Flag at HIGH severity.

KEPT UNCHANGED: A conclusion that summarised the main findings, linked them \
to the study's purpose, and noted their wider significance — all drawn from \
content already in the paper.
→ Do not flag conclusions that stay within the bounds of what was presented.

### Example 7: APA style — references

FLAGGED BY EDITOR: A reference list that formatted DOIs as bare \
"doi:10.xxxx/yyyy" or omitted DOIs where available. Editor standardised them \
to the https://doi.org/ form.
→ Flag DOI formats that are not in the https://doi.org/xxxxx form. Flag at \
MEDIUM severity.

KEPT UNCHANGED: A reference list with entries alphabetised, hanging-indented, \
and DOIs written as https://doi.org/... links.
→ Correct APA 7 reference formatting. Do not flag.

### Example 8: Tables and figures

FLAGGED BY EDITOR: A table presented without a title, and a figure whose \
caption was placed below rather than above the figure. Editor added "Table 1" \
(bold) with an italic title, and moved the figure number/title above the image.
→ In APA 7 the table number is bold and the title italic above the table; the \
figure number is bold and the title italic above the figure. Flag violations \
at MEDIUM severity.

KEPT UNCHANGED: "Table 1" (bold) followed by an italic title, referenced in \
the text before it appeared.
→ Correct APA 7 table formatting. Do not flag.
"""
