#!/usr/bin/env python3
"""Inspect and validate English tldr page maintenance batches."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


PAGE_PATH_RE = re.compile(r"^pages/([^/]+)/([^/]+)\.md$")
TITLE_RE = re.compile(r"^# (.+)$")
FULL_COMMAND_RE = re.compile(r"^`[^`]+`$")
TRAILING_WHITESPACE_RE = re.compile(r"[ \t]+$")
OPERATIONS = frozenset({"create", "update", "revise"})


class ValidationError(RuntimeError):
    """Represent an invalid invocation or unavailable repository operation."""


@dataclass
class Check:
    code: str
    ok: bool
    message: str
    page: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class PageSpec:
    operation: str
    path: str


def run_git(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise ValidationError(f"git {' '.join(args)} failed: {detail}")
    return result


def repository_root(value: str) -> Path:
    repo = Path(value).expanduser().resolve()
    result = run_git(repo, "rev-parse", "--show-toplevel")
    actual = Path(result.stdout.strip()).resolve()
    if actual != repo:
        raise ValidationError(f"--repo must be the repository root: {actual}")
    return repo


def normalize_command(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip()).lower()
    normalized = re.sub(r"-+", "-", normalized)
    return normalized.removesuffix(".md")


def list_english_pages(repo: Path, ref: str) -> list[str]:
    result = run_git(repo, "ls-tree", "-r", "--name-only", ref, "--", "pages")
    return sorted(
        path for path in result.stdout.splitlines() if PAGE_PATH_RE.fullmatch(path)
    )


def inspect_batch(repo: Path, ref: str, commands: list[str]) -> dict[str, Any]:
    pages = list_english_pages(repo, ref)
    normalized_inputs = [normalize_command(command) for command in commands]
    duplicates = {
        name for name in normalized_inputs if normalized_inputs.count(name) > 1
    }
    results: list[dict[str, Any]] = []
    for original, normalized in zip(commands, normalized_inputs, strict=True):
        matches = [
            path for path in pages if PurePosixPath(path).stem.lower() == normalized
        ]
        status = (
            "duplicate_input"
            if normalized in duplicates
            else ("existing" if matches else "absent")
        )
        results.append(
            {
                "input": original,
                "normalized": normalized,
                "status": status,
                "existing_pages": matches,
            }
        )
    return {
        "ok": not duplicates,
        "ref": ref,
        "command_count": len(commands),
        "commands": results,
    }


def safe_path(repo: Path, relative: str) -> Path:
    path = (repo / relative).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise ValidationError(f"path escapes repository root: {relative}") from exc
    return path


def parse_page_spec(value: str) -> PageSpec:
    if ":" not in value:
        raise ValidationError(f"invalid --page {value!r}; expected OPERATION:PAGE")
    operation, path = value.split(":", 1)
    operation = operation.strip().lower()
    path = path.strip()
    if operation not in OPERATIONS:
        allowed = ", ".join(sorted(OPERATIONS))
        raise ValidationError(
            f"invalid operation {operation!r}; expected one of: {allowed}"
        )
    if not path:
        raise ValidationError(f"invalid --page {value!r}; expected OPERATION:PAGE")
    return PageSpec(operation, path)


def read_page(path: Path) -> tuple[bytes, str, list[str]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"page is not valid UTF-8: {path}") from exc
    return raw, text, text.splitlines()


def add_check(
    checks: list[Check],
    code: str,
    ok: bool,
    message: str,
    page: str | None = None,
    line: int | None = None,
) -> None:
    checks.append(Check(code, ok, message, page, line))


def tracked_at_ref(repo: Path, ref: str, path: str) -> bool:
    return run_git(repo, "cat-file", "-e", f"{ref}:{path}", check=False).returncode == 0


def platform_exists_at_ref(repo: Path, ref: str, platform: str) -> bool:
    prefix = f"pages/{platform}/"
    result = run_git(repo, "ls-tree", "-r", "--name-only", ref, "--", prefix)
    return any(line.startswith(prefix) for line in result.stdout.splitlines())


def nonblank_line_kinds(lines: list[str]) -> list[str]:
    kinds: list[str] = []
    for line in lines:
        if not line:
            continue
        if TITLE_RE.fullmatch(line):
            kinds.append("title")
        elif line.startswith("> "):
            kinds.append("header")
        elif line.startswith("- "):
            kinds.append("example")
        elif FULL_COMMAND_RE.fullmatch(line):
            kinds.append("command")
        else:
            kinds.append("other")
    return kinds


def valid_structure(kinds: list[str]) -> bool:
    if not kinds or kinds[0] != "title" or "header" not in kinds:
        return False
    index = 1
    while index < len(kinds) and kinds[index] == "header":
        index += 1
    if index == len(kinds):
        return False
    while index < len(kinds):
        if kinds[index : index + 2] != ["example", "command"]:
            return False
        index += 2
    return True


def validate_page(repo: Path, ref: str, spec: PageSpec) -> list[Check]:
    checks: list[Check] = []
    operation, page = spec.operation, spec.path
    match = PAGE_PATH_RE.fullmatch(page)
    add_check(
        checks,
        "page_path",
        match is not None,
        "page path has the form pages/<platform>/<filename>.md"
        if match
        else "expected pages/<platform>/<filename>.md",
        page,
    )
    if not match:
        return checks

    platform, filename = match.groups()
    add_check(
        checks,
        "filename_lowercase",
        filename == filename.lower(),
        "filename is lowercase"
        if filename == filename.lower()
        else "filename must be lowercase",
        page,
    )
    platform_exists = platform_exists_at_ref(repo, ref, platform)
    add_check(
        checks,
        "platform_directory",
        platform_exists,
        "platform directory exists in the fetched ref"
        if platform_exists
        else f"platform directory pages/{platform} does not exist in {ref}",
        page,
    )
    tracked = tracked_at_ref(repo, ref, page)
    expected_tracked = operation != "create"
    state_ok = tracked == expected_tracked
    if operation == "create":
        state_message = (
            f"create target is absent from {ref}"
            if state_ok
            else f"create target already exists in {ref}"
        )
    else:
        state_message = (
            f"{operation} target exists in {ref}"
            if state_ok
            else f"{operation} target is absent from {ref}"
        )
    add_check(
        checks,
        "operation_target_state",
        state_ok,
        state_message,
        page,
    )

    page_path = safe_path(repo, page)
    exists = page_path.is_file()
    add_check(
        checks,
        "page_exists",
        exists,
        "page exists in the worktree" if exists else "page is missing",
        page,
    )
    if not exists:
        return checks

    raw, text, lines = read_page(page_path)
    add_check(
        checks,
        "final_newline",
        raw.endswith(b"\n"),
        "page ends with a newline",
        page,
    )
    trailing_lines = [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if TRAILING_WHITESPACE_RE.search(line)
    ]
    add_check(
        checks,
        "trailing_whitespace",
        not trailing_lines,
        "page has no trailing whitespace"
        if not trailing_lines
        else f"trailing whitespace on lines {trailing_lines}",
        page,
        trailing_lines[0] if trailing_lines else None,
    )

    title_match = TITLE_RE.fullmatch(lines[0]) if lines else None
    add_check(
        checks,
        "title",
        title_match is not None,
        "first line is a page title"
        if title_match
        else "first line must be '# <command>'",
        page,
        1,
    )
    if title_match:
        expected_filename = normalize_command(title_match.group(1))
        filename_matches = filename == expected_filename or filename.startswith(
            f"{expected_filename}."
        )
        add_check(
            checks,
            "title_filename",
            filename_matches,
            "title maps to the page filename or its disambiguation suffix"
            if filename_matches
            else f"title maps to {expected_filename}.md, not {filename}.md",
            page,
            1,
        )

    kinds = nonblank_line_kinds(lines)
    structure_ok = valid_structure(kinds)
    add_check(
        checks,
        "structure",
        structure_ok,
        "nonblank lines follow title, headers, and example/command pairs"
        if structure_ok
        else f"unexpected nonblank line order: {kinds}",
        page,
    )
    example_count = sum(line.startswith("- ") for line in lines)
    command_count = sum(FULL_COMMAND_RE.fullmatch(line) is not None for line in lines)
    add_check(
        checks,
        "example_count",
        1 <= example_count <= 8,
        f"page has {example_count} examples within the 1-8 limit"
        if 1 <= example_count <= 8
        else f"page has {example_count} examples; expected 1-8",
        page,
    )
    add_check(
        checks,
        "command_count",
        command_count == example_count,
        f"command count matches example count ({example_count})"
        if command_count == example_count
        else f"found {example_count} descriptions and {command_count} commands",
        page,
    )
    return checks


def porcelain_changes(repo: Path) -> list[tuple[str, str]]:
    result = run_git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    records = result.stdout.split("\0")
    changes: list[tuple[str, str]] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise ValidationError(f"unexpected git status record: {record!r}")
        status = record[:2]
        path = record[3:]
        changes.append((status, path))
        if "R" in status or "C" in status:
            if index >= len(records) or not records[index]:
                raise ValidationError(f"missing source path for status: {record!r}")
            changes.append(("source-of-rename", records[index]))
            index += 1
    return changes


def allowed_worktree_statuses(operation: str | None) -> set[str]:
    if operation == "create":
        return {"??", "A ", "AM"}
    if operation in {"update", "revise"}:
        return {" M", "M ", "MM"}
    return set()


def validate_scope(repo: Path, specs: list[PageSpec]) -> list[Check]:
    checks: list[Check] = []
    expected_operations = {spec.path: spec.operation for spec in specs}
    expected = set(expected_operations)
    changes = porcelain_changes(repo)
    actual = {path for _, path in changes}
    add_check(
        checks,
        "worktree_scope",
        actual == expected,
        "worktree contains exactly the expected target pages"
        if actual == expected
        else f"expected {sorted(expected)}, got {sorted(actual)}",
    )
    for status, path in changes:
        operation = expected_operations.get(path)
        allowed = status in allowed_worktree_statuses(operation)
        add_check(
            checks,
            "worktree_change_type",
            allowed,
            f"{status} {path} matches {operation}"
            if allowed
            else f"status {status} does not match operation {operation or '<none>'}",
            path,
        )
    return checks


def validation_report(
    repo: Path, ref: str, specs: list[PageSpec], check_scope: bool
) -> dict[str, Any]:
    checks: list[Check] = []
    seen: set[str] = set()
    for spec in specs:
        if spec.path in seen:
            add_check(
                checks,
                "duplicate_page",
                False,
                f"page repeated: {spec.path}",
                spec.path,
            )
        seen.add(spec.path)
        checks.extend(validate_page(repo, ref, spec))
    if check_scope:
        checks.extend(validate_scope(repo, specs))
    failures = [check for check in checks if not check.ok]
    return {
        "ok": not failures,
        "ref": ref,
        "page_count": len(specs),
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": [asdict(check) for check in checks],
    }


def print_inspection(report: dict[str, Any]) -> None:
    for command in report["commands"]:
        print(
            f"{command['status'].upper():<16} {command['input']} -> {command['normalized']}"
        )
        for page in command["existing_pages"]:
            print(f"  {page}")


def print_validation(report: dict[str, Any]) -> None:
    for item in report["checks"]:
        status = "PASS" if item["ok"] else "FAIL"
        location = item["page"] or "batch"
        if item["line"] is not None:
            location = f"{location}:{item['line']}"
        print(f"{status:<4} {item['code']:<24} {location} - {item['message']}")
    print(
        f"Summary: {report['check_count']} checks, {report['failure_count']} failures"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser("inspect", help="find existing English pages")
    inspect.add_argument("--repo", required=True, help="repository root")
    inspect.add_argument("--ref", required=True, help="fetched official Git ref")
    inspect.add_argument("--json", action="store_true", dest="output_json")
    inspect.add_argument("commands", nargs="+", help="user-provided command names")

    validate = subparsers.add_parser("validate", help="validate English page changes")
    validate.add_argument("--repo", required=True, help="repository root")
    validate.add_argument("--ref", required=True, help="fetched official Git ref")
    validate.add_argument(
        "--page",
        action="append",
        required=True,
        help="OPERATION:PAGE; repeat for the complete batch",
    )
    validate.add_argument("--check-scope", action="store_true")
    validate.add_argument("--json", action="store_true", dest="output_json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        repo = repository_root(args.repo)
        if args.command == "inspect":
            report = inspect_batch(repo, args.ref, args.commands)
            if args.output_json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print_inspection(report)
        else:
            specs = [parse_page_spec(value) for value in args.page]
            report = validation_report(repo, args.ref, specs, args.check_scope)
            if args.output_json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print_validation(report)
        return 0 if report["ok"] else 1
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
