"""Validation utility for Track K corpus manifest files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1

REQUIRED_FIELDS = {
    "id",
    "source_url",
    "license",
    "license_status",
    "mode",
    "consent_ref",
    "defects_injected",
    "verdicts",
    "notes",
}

VALID_MODES = {
    "student",
    "professional",
}

VALID_VERDICTS = {
    "pass",
    "fail",
    "na",
}


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON manifest and return its root object."""

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path}: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ValueError(f"{path}: could not be read: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{path}: manifest root must be a JSON object")

    return data


def _validate_document(
    document: Any,
    manifest_path: Path,
    index: int,
) -> list[str]:
    """Validate one document entry from a manifest."""

    errors: list[str] = []

    prefix = f"{manifest_path}: documents[{index}]"

    if not isinstance(document, dict):
        return [f"{prefix} must be a JSON object"]

    missing = REQUIRED_FIELDS - document.keys()

    if missing:
        errors.append(
            f"{prefix} missing required fields: "
            f"{', '.join(sorted(missing))}"
        )

        # Do not continue field-specific checks for fields that are absent.
        return errors

    document_id = document["id"]

    if not isinstance(document_id, str) or not document_id.strip():
        errors.append(f"{prefix}.id must be a non-empty string")

    for field in (
        "source_url",
        "license",
        "license_status",
        "consent_ref",
        "notes",
    ):
        if not isinstance(document[field], str):
            errors.append(f"{prefix}.{field} must be a string")

    mode = document["mode"]

    if mode not in VALID_MODES:
        errors.append(
            f"{prefix}.mode must be one of "
            f"{sorted(VALID_MODES)}, got {mode!r}"
        )

    defects = document["defects_injected"]

    if not isinstance(defects, list):
        errors.append(
            f"{prefix}.defects_injected must be a list"
        )
    else:
        for defect_index, defect in enumerate(defects):
            if not isinstance(defect, str):
                errors.append(
                    f"{prefix}.defects_injected[{defect_index}] "
                    "must be a string"
                )
            elif not defect.startswith("APA-"):
                errors.append(
                    f"{prefix}.defects_injected[{defect_index}] "
                    f"must be an APA matrix ID, got {defect!r}"
                )

    verdicts = document["verdicts"]

    if not isinstance(verdicts, dict):
        errors.append(f"{prefix}.verdicts must be an object")
    else:
        for matrix_id, verdict in verdicts.items():
            if not isinstance(matrix_id, str):
                errors.append(
                    f"{prefix}.verdicts keys must be strings"
                )
                continue

            if not matrix_id.startswith("APA-"):
                errors.append(
                    f"{prefix}.verdicts contains invalid "
                    f"matrix ID {matrix_id!r}"
                )

            if verdict not in VALID_VERDICTS:
                errors.append(
                    f"{prefix}.verdicts[{matrix_id!r}] "
                    f"must be pass, fail, or na; got {verdict!r}"
                )

    return errors


def validate_manifest(path: Path) -> list[str]:
    """Validate one manifest.json file."""

    errors: list[str] = []

    try:
        data = _load_json(path)
    except ValueError as exc:
        return [str(exc)]

    schema_version = data.get("schema_version")

    if schema_version != SCHEMA_VERSION:
        errors.append(
            f"{path}: schema_version must be {SCHEMA_VERSION}, "
            f"got {schema_version!r}"
        )

    documents = data.get("documents")

    if documents is None:
        errors.append(f"{path}: missing 'documents' array")
        return errors

    if not isinstance(documents, list):
        errors.append(f"{path}: 'documents' must be an array")
        return errors

    seen_ids: set[str] = set()

    for index, document in enumerate(documents):
        errors.extend(
            _validate_document(
                document=document,
                manifest_path=path,
                index=index,
            )
        )

        if isinstance(document, dict):
            document_id = document.get("id")

            if isinstance(document_id, str) and document_id:
                if document_id in seen_ids:
                    errors.append(
                        f"{path}: duplicate document id "
                        f"{document_id!r}"
                    )

                seen_ids.add(document_id)

    return errors


def find_manifests(root: Path) -> list[Path]:
    """Find manifest.json files below a corpus path."""

    if root.is_file():
        if root.name != "manifest.json":
            raise ValueError(
                f"{root} is a file but is not named manifest.json"
            )
        return [root]

    if not root.exists():
        raise ValueError(f"{root} does not exist")

    manifests = sorted(root.rglob("manifest.json"))

    if not manifests:
        raise ValueError(
            f"No manifest.json files found under {root}"
        )

    return manifests


def validate_path(root: Path) -> int:
    """Validate every manifest beneath root."""

    try:
        manifests = find_manifests(root)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    all_errors: list[str] = []

    for manifest in manifests:
        errors = validate_manifest(manifest)

        if errors:
            print(f"FAIL: {manifest}")

            for error in errors:
                print(f"  - {error}")

            all_errors.extend(errors)

        else:
            print(f"PASS: {manifest}")

    print()

    if all_errors:
        print(
            f"Manifest validation failed with "
            f"{len(all_errors)} error(s)."
        )
        return 1

    print(
        f"Manifest validation passed for "
        f"{len(manifests)} manifest file(s)."
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Track K corpus manifest files."
    )

    parser.add_argument(
        "--validate",
        metavar="PATH",
        help=(
            "Validate a manifest.json file or every "
            "manifest.json below a corpus directory."
        ),
    )

    args = parser.parse_args()

    if not args.validate:
        parser.print_help()
        return 1

    return validate_path(Path(args.validate))


if __name__ == "__main__":
    sys.exit(main())