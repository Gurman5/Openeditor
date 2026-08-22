import argparse
import sys
from pathlib import Path
from pprint import pprint

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _status(message: str) -> None:
    # Show live build progress in the terminal while keeping the main printed
    # report output separate.
    print(f"[copybot] {message}", file=sys.stderr, flush=True)


def _heading_level_1_sections(docx_path: str) -> list[dict]:
    from app.services.document_analysis_services import detect_heading_level_1

    return detect_heading_level_1(docx_path)


def _show_heading_level_1_sections(docx_path: str, label: str = "Heading 1 sections detected") -> None:
    headings = _heading_level_1_sections(docx_path)
    if not headings:
        _status(f"{label}: none")
        return

    _status(f"{label}:")
    for heading in headings:
        _status(f"  {heading['position']}: {heading['text']}")


def _print_heading_normalization_summary(input_headings: list[dict], output_headings: list[dict]) -> None:
    print("")
    print("HEADING NORMALIZATION")

    changes = []
    for before, after in zip(input_headings, output_headings):
        before_text = before.get("text", "")
        after_text = after.get("text", "")
        if before_text != after_text:
            changes.append((before, after))

    if not changes:
        print("No Heading 1 names needed normalization.")
        return

    for before, after in changes:
        print(
            f"{before['text']} -> {after['text']} "
            f"(input position {before['position']}, output position {after['position']})"
        )


def _is_generic_copyedit_output(input_path: Path, output_path: str | None) -> bool:
    if output_path is None:
        return False
    name = Path(output_path).name
    if name == f"{input_path.stem}_CopyEdit.docx":
        return True
    return name.endswith("_CopyEdit.docx") and "_JUTLP_" not in name


def _rename_generic_copyedit_output(input_path: Path, output_path: str, author_line: str) -> str:
    if _is_generic_copyedit_output(input_path, output_path) is False:
        return output_path

    from app.services.output_filename import build_output_filename_from_author_line

    output = Path(output_path)
    final = output.with_name(
        build_output_filename_from_author_line(
            str(input_path),
            str(output.parent),
            author_line,
            ignore_path=str(output),
        )
    )
    if output.resolve() != final.resolve():
        output.replace(final)
    return str(final)


def main():
    parser = argparse.ArgumentParser(prog="copybot")
    parser.add_argument("--analyse", metavar="FILE", help="Path to a .docx file to analyse")
    parser.add_argument("--analyze", dest="analyse", metavar="FILE", help=argparse.SUPPRESS)
    parser.add_argument("--build", action="store_true", help="Also build reviewed output document")
    parser.add_argument("--output", metavar="FILE", help="Optional output .docx path", default=None)
    args = parser.parse_args()

    if args.analyse is None:
        parser.error("Use: copybot --analyse <yourfile.docx>")

    input_path = Path(args.analyse)
    if input_path.exists() is False:
        print("Error: file not found -> " + str(input_path))
        return 1

    if input_path.suffix.lower() != ".docx":
        print("Error: only .docx files are supported")
        return 1

    _status(f"Input file found: {input_path}")
    _status("Loading analysis modules...")

    from app.services.output_generation import generate_commented_docx
    from app.services.output_generation_samfix import (
        build_abstract_check_plan,
        build_author_check_plan,
        build_citation_check_plan,
        build_document_body_check_plan,
        build_edited_document,
        build_keywords_check_plan,
        build_title_check_plan,
    )
    from app.services.reference_checker import check_and_report

    input_heading_1_sections = _heading_level_1_sections(str(input_path))
    _show_heading_level_1_sections(str(input_path), "Input Heading 1 sections detected")

    if args.build is True or args.output is not None:
        # Build mode creates the reviewed document, checks references, then adds
        # reference comments to the reviewed file.
        _status("Build mode started.")
        _status("Creating edited Word document with tracked changes...")
        result = build_edited_document(str(input_path), args.output)
        built_plan = result.get("plan", {})
        built_output_path = result.get("output_path", "")
        built_output_path = _rename_generic_copyedit_output(
            input_path,
            built_output_path,
            built_plan.get("author", {}).get("corrected_authors_line", ""),
        )
        result["output_path"] = built_output_path

        _status(f"Edited document created: {built_output_path}")
        _status("Checking references...")
        reference_report = check_and_report(built_output_path)
        _status("Adding reference comments to the reviewed document...")
        generate_commented_docx(
            input_path=built_output_path,
            output_path=built_output_path,
            report={"results": []},
            ref_results=reference_report.get("results", []),
            llm_results=None,
        )
        _status("Reference comments added.")
        output_heading_1_sections = _heading_level_1_sections(built_output_path)

        print("TITLE PLAN")
        pprint(built_plan.get("title", {}))
        print("")
        print("AUTHOR PLAN")
        pprint(built_plan.get("author", {}))
        print("")
        print("ABSTRACT PLAN")
        pprint(built_plan.get("abstract", {}))
        print("")
        print("KEYWORDS PLAN")
        pprint(built_plan.get("keywords", {}))
        print("")
        print("CITATION PLAN")
        pprint(built_plan.get("citation", {}))
        print("")
        print("DOCUMENT BODY PLAN")
        pprint(built_plan.get("document_body", {}))

        print("")
        print("REFERENCE CHECK")
        pprint(reference_report)

        print("")
        print("BUILD RESULT")
        pprint(result.get("plan", {}))
        print(built_output_path)
        _status(f"Build finished. Output file: {built_output_path}")
        _print_heading_normalization_summary(input_heading_1_sections, output_heading_1_sections)
        return 0

    # Analysis-only mode runs the same checks but does not create a reviewed docx.
    _status("Analysis mode started.")
    _status("Checking title...")
    title_plan = build_title_check_plan(str(input_path))
    _status("Checking author details...")
    author_plan = build_author_check_plan(str(input_path))
    _status("Checking abstract...")
    abstract_plan = build_abstract_check_plan(str(input_path))
    _status("Checking keywords...")
    keywords_plan = build_keywords_check_plan(str(input_path))
    _status("Checking citation...")
    citation_plan = build_citation_check_plan(str(input_path))
    _status("Checking document body...")
    body_plan = build_document_body_check_plan(str(input_path))
    _status("Analysis checks finished.")

    print("TITLE PLAN")
    pprint(title_plan)
    print("")
    print("AUTHOR PLAN")
    pprint(author_plan)
    print("")
    print("ABSTRACT PLAN")
    pprint(abstract_plan)
    print("")
    print("KEYWORDS PLAN")
    pprint(keywords_plan)
    print("")
    print("CITATION PLAN")
    pprint(citation_plan)
    print("")
    print("DOCUMENT BODY PLAN")
    pprint(body_plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
