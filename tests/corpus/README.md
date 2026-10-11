# APA 7 Evaluation Corpus

This folder contains the documents we use to test how well OpenEditor follows APA 7 formatting rules.

The main purpose of the corpus is to give us a consistent set of documents that we can use before and after the Track C and Track D changes. This makes it easier to compare the old output with the updated APA 7 version.

## Folder structure

- `seed/` — contains 4 known-good APA 7 documents that we use as the main baseline.
- `injected/` — contains copies of the seed documents where we intentionally add one formatting error for testing.
- `composites/` — contains documents with several formatting errors added at the same time.
- `real/` — contains real student assignments from team members or other documents we have permission to use.
- `samples/` — contains external sample documents used for reference or testing.

## Seed documents

The seed folder should contain exactly 4 APA 7 `.docx` files.

These documents should give us a good mix of APA 7 formatting, including:

- student paper formatting
- professional paper formatting
- at least one document with an abstract
- references
- at least one document with a table or figure

Where possible, the documents should be student-written or student sample papers so they are closer to the type of documents OpenEditor is expected to process.

Good sources include:

1. Official APA sample papers
2. University writing centre examples
3. University or institutional repositories
4. OSF repositories
5. Other reliable sources if we need to fill a missing test case

## Upload checks

Before a document is added to the corpus, it needs to pass the same basic checks as a normal OpenEditor upload.

Each file should:

- be a valid `.docx` file
- contain valid XML
- not contain `word/vbaProject.bin`
- not contain files under `word/embeddings/`
- be no larger than 20 MB
- contain no more than 15,000 words

The upload gate can be tested with:

```powershell
python -m pytest tests/corpus/test_corpus_gate.py -v