# JUTLP DOCX Validator

deterministic checker for JUTLP `.docx` files.

This checker should look for:
- required headings
- required subsections
- basic front-page rules
- page breaks
- important styles
- obvious submission issues

Do the deterministic checks first. Leave AI or semantic checks until later.

---

## Build order

## Recommended implementation path (ground-up)
Use this exact sequence. Do not skip ahead.

### Step A: Basel
  - `read_docx(path)`
  - `print_all_paragraphs(document)`
  - `print_headings_only(document)`
- Run:
  - `python app/services/document_analysis_services.py`
- Checkpoint:
  - you can see index + style + text for every paragraph
  - you can see heading rows only

### Step B: Add a reusable paragraph model
- Add one helper function:
  - `get_paragraph_rows(document) -> list[dict]`
- Each row should contain:
  - `index`, `text`, `style`, `is_empty`
- Replace direct loops in print functions to use `get_paragraph_rows`.
- Checkpoint:
  - output is identical to Step A

### Step C: First real check (section existence)
- Add required Heading 1 names.
- Implement:
  - `check_required_sections(rows) -> list[result]`
- Keep result format very simple:
  - `{"rule_id": "SEC001", "status": "pass|fail", "message": "..."}`
- Checkpoint:
  - script prints pass/fail for required sections only

### Step D: Add heading order check
- Reuse the same heading list from Step C.
- Implement:
  - `check_heading_order(rows) -> list[result]`
- Checkpoint:
  - detects missing and out-of-order headings

### Step E: Add Method/Discussion subsection checks
- Implement two checks:
  - required Method subsections
  - required Discussion subsections
- Checkpoint:
  - these show separate rule IDs and messages

### Step F: Add front-page deterministic checks
- Add only deterministic checks:
  - abstract exists
  - abstract <= 250 words
  - practitioner note count
  - keyword count
- Checkpoint:
  - all front-page checks report pass/fail

### Step G: Add style checks last
- Add:
  - `Guidance Notes` still present
  - heading styles correct
  - references style check
- Checkpoint:
  - style issues appear as warnings/fails

### Step H: Output format cleanup
- Add one function:
  - `build_report(results) -> dict`
- Include:
  - total pass/warn/fail counts
  - ordered list of rule results
- Checkpoint:
  - one clean report object printed at the end

### 1. Learn how to read the DOCX
Start by using `python-docx` to print:
- paragraph index
- paragraph text
- paragraph style name

First goal: make sure you can see what styles and headings are in the document.

---

### 2. Build a simple paragraph list
For each paragraph, store:
- index
- text
- style
- is_empty

This becomes the base for all checks.

---

### 3. Write helper functions
Make small helper functions like:
- find first paragraph by text
- find all paragraphs with a style
- find heading positions
- get the text inside a section
- detect a page break near a paragraph

---

### 4. Implement the easiest checks first

#### Front page
- title exists
- authors block exists
- affiliations block exists
- `Abstract` heading exists
- abstract body exists
- abstract is one paragraph
- abstract is 250 words or less
- `Practitioner Notes` heading exists
- there are 5 practitioner notes
- `Keywords` heading exists
- there are 5 keywords or fewer
- page break before `Introduction`

#### Main sections
- `Introduction`
- `Literature`
- `Method`
- `Results`
- `Discussion`
- `Conclusion` or `Conclusions`
- `Acknowledgements`
- `References`
- `Results` and `Discussion` are separate

#### Required Method subsections
Under `Method`, check for:
- `Research Design`
- `Participants`
- `Measures`
- `Procedure`
- `Analysis`

#### Required Discussion subsections
Under `Discussion`, check for:
- `Practical Implications`
- `Theoretical Implications`
- `Limitations and Future Research`

---

## Style checks
After the basic structure works, add these:
- body paragraphs mainly use `Normal`
- main headings use `Heading 1`
- subheadings use `Heading 2`
- references use `APA 7 Reference List Entry`
- `Guidance Notes` are not still in the draft

Do these after section detection is working.

---

## Reference and page-break checks
Then add:
- `References` exists
- page break before `References`
- figure/table number is followed by figure/table title
- figure/table numbering is sequential

---

## Blind review checks
Later, add checks for:
- identified version includes authors and affiliations
- deidentified version removes authors and affiliations
- deidentified version removes names from CRediT

---

## Leave these until later
Do **not** start with these:
- whether the abstract is well written
- whether the introduction has a strong problem statement
- whether results are too interpretive
- whether discussion links back to research questions
- line-count or exact page-fit checks

These are harder and should come after deterministic checks.

---

## Suggested rule format
For each rule, write down:
- rule ID
- what it checks
- whether it is deterministic or semantic
- whether it is fail or warn
- how you will detect it

Example:

- `SEC001`
- Check: `Introduction` exists as `Heading 1`
- Type: deterministic
- Severity: fail
- Detection: find paragraph with text `Introduction` and style `Heading 1`

---

## Good first milestone
A strong first milestone is:
- open the DOCX
- print every paragraph's text and style
- find the main headings
- output whether each required section exists

If that works, you are on the right track.

---

## Testing plan
Make a few broken test files and check that your validator catches the right issue.

Examples:
- remove `Participants`
- make abstract over 250 words
- use 6 keywords
- remove one practitioner note
- remove page break before `References`
- leave `Guidance Notes` in the file

---

## MVP definition
The first version is good enough when it can:
- read a DOCX
- identify paragraph styles
- detect required headings
- detect required subsections
- count abstract words
- count practitioner notes
- count keywords
- detect page breaks before `Introduction` and `References`
- output a simple pass/fail/warn report
