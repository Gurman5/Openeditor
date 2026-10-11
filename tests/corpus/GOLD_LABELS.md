# APA 7 Gold Labels

This file explains the expected results we use when testing documents in the Track K corpus.

The main idea is to have a simple reference for what should pass or fail for each APA rule. This will help us compare the current OpenEditor output with the updated APA 7 version later.

The rules use the matrix IDs APA-00 to APA-20.

Some checks can be tested automatically by the conformance harness. Other checks are marked as manual if the current project documents do not give enough information to test them safely.

## Verdicts

The corpus uses three possible verdicts:

- `pass` - the document follows the expected APA rule.
- `fail` - the document breaks the expected APA rule.
- `na` - the rule does not apply to that document.

A rule can also be marked as `MANUAL` in this document if we do not currently have a reliable automatic check for it.

## Gold label table

| Matrix ID | What we are checking | Expected pass | Example fail / injected defect | Harness check | Status |
|---|---|---|---|---|---|
| APA-00 | Page margins | All document sections use 1 inch margins, which is 1440 twips | Change a section margin so it is not 1440 twips | Margins check | Automatic |
| APA-01 | Line spacing | Normal body text is double spaced and does not add incorrect extra spacing around headings | Change body spacing to 1.15 or another incorrect value | Spacing check | Automatic |
| APA-02 | Rule not clearly defined in the current Track K backlog | To be confirmed from the main APA matrix | To be confirmed | Not assigned yet | MANUAL / confirm |
| APA-03 | Paragraph alignment | Normal body paragraphs are left aligned and are not fully justified | Set a body paragraph to `w:jc="both"` | Alignment check | Automatic |
| APA-04 | First-line indentation | Normal body paragraphs use a 0.5 inch first-line indent, which is 720 twips | Remove the first-line indent from a body paragraph | Indent check | Automatic |
| APA-05 | Page numbers | A valid PAGE field is present in the required document header | Remove the PAGE field from the header | Page-number check | Automatic |
| APA-06 | Rule not clearly defined in the current Track K backlog | To be confirmed from the main APA matrix | To be confirmed | Not assigned yet | MANUAL / confirm |
| APA-07 | Rule not clearly defined in the current Track K backlog | To be confirmed from the main APA matrix | To be confirmed | Not assigned yet | MANUAL / confirm |
| APA-08 | Abstract | Abstract heading is correctly formatted, abstract is no more than 250 words, and the paragraph is not incorrectly indented | Remove the Abstract heading, make the abstract longer than 250 words, or indent it incorrectly | Abstract check | Automatic |
| APA-09 | Keywords | Keywords are formatted correctly when the document contains them | Remove or incorrectly format the Keywords label | Abstract/keywords check | Automatic |
| APA-10 | Headings | APA heading levels and formatting are correct and an unnecessary `Introduction` heading is not added | Change a heading level, use the wrong heading style, or add an `Introduction` heading | Heading check | Automatic |
| APA-11 | Rule not clearly defined in the current Track K backlog | To be confirmed from the main APA matrix | To be confirmed | Not assigned yet | MANUAL / confirm |
| APA-12 | References section | References begins correctly on a new page and uses the expected APA formatting | Remove the page break before References or format the heading incorrectly | References check | Automatic |
| APA-13 | In-text citations | Parenthetical and narrative citations use the expected APA author format | Use `&` incorrectly in a narrative citation or fail to use `et al.` for 3 or more authors | Citation check | Automatic later |
| APA-14 | Block quotations | A quotation of 40 or more words uses block quote formatting | Leave a long quotation inline with quotation marks instead of using block formatting | Citation/block quote check | Automatic later |
| APA-15 | Tables | Table captions and numbering follow the required format | Give a table the wrong number or incorrectly format its caption | Table/figure check | Deferred |
| APA-16 | Figures | Figure captions and numbering follow the required format | Give a figure the wrong number or incorrectly format its caption | Table/figure check | Deferred |
| APA-17 | Numbers / decimal policy | The final expected behaviour has not been confirmed by the team | Decimal formatting that conflicts with the final project decision | Manual review only | MANUAL |
| APA-18 | Reference formatting | References use expected APA formatting such as hanging indent, alphabetical ordering and DOI format | Remove hanging indent, place references out of alphabetical order, or use an incorrect DOI form | References check | Automatic |
| APA-19 | Appendices | If the input document contains an appendix, the appendix is still present in the output | Remove an appendix that existed in the input | Appendices check | Automatic |
| APA-20 | JUTLP residue | A normal APA document should not gain JUTLP-specific content such as Practitioner Notes, journal banners, CRediT blocks or other JUTLP wording | Output contains JUTLP-specific text or elements that were not in the clean seed input | Residue check | Automatic |

## Injected defects

Later in Track K, some known-good documents will have one formatting problem added on purpose.

For example, APA-03 can be tested by changing a normal left-aligned paragraph to justified alignment.

The original document should have:

```text
APA-03 = pass