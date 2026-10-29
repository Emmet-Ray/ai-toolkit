#!/usr/bin/env python3
"""Resolve and validate Simplified Chinese tldr page maintenance batches."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


FULL_COMMAND_RE = re.compile(r"^`[^`]+`$")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
PLACEHOLDER_RE = re.compile(r"\{\{(.*?)\}\}")
URL_RE = re.compile(r"https?://[^\s>`]+")
TRAILING_WHITESPACE_RE = re.compile(r"[ \t]+$")
OPERATIONS = frozenset({"create", "sync", "revise"})


class ValidationError(RuntimeError):
    """Represent an invalid invocation or an unavailable repository operation."""


@dataclass
class Check:
    code: str
    ok: bool
    message: str
    source: str | None = None
    target: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class Pair:
    operation: str
    source: str
    target: str


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


def list_tree_paths(repo: Path, ref: str) -> list[str]:
    result = run_git(
        repo, "ls-tree", "-r", "--name-only", ref, "--", "pages", "pages.zh"
    )
    return [line for line in result.stdout.splitlines() if line]


def resolve_batch(repo: Path, ref: str, commands: list[str]) -> dict[str, Any]:
    tree_paths = list_tree_paths(repo, ref)
    tree_set = set(tree_paths)
    english_paths = [
        path for path in tree_paths if re.fullmatch(r"pages/[^/]+/[^/]+\.md", path)
    ]
    normalized_inputs = [normalize_command(command) for command in commands]
    duplicate_names = {
        name for name in normalized_inputs if normalized_inputs.count(name) > 1
    }
    results: list[dict[str, Any]] = []

    for original, normalized in zip(commands, normalized_inputs, strict=True):
        sources = sorted(
            path
            for path in english_paths
            if PurePosixPath(path).stem.lower() == normalized
        )
        candidates = []
        for source in sources:
            target = f"pages.zh/{source.removeprefix('pages/')}"
            candidates.append(
                {
                    "source": source,
                    "target": target,
                    "target_exists": target in tree_set,
                }
            )

        if normalized in duplicate_names:
            status = "duplicate_input"
        elif not sources:
            status = "missing_source"
        elif len(sources) > 1:
            status = "ambiguous_source"
        else:
            status = "resolved"

        results.append(
            {
                "input": original,
                "normalized": normalized,
                "status": status,
                "candidates": candidates,
            }
        )

    resolved = all(item["status"] == "resolved" for item in results)
    return {
        "ok": resolved,
        "ref": ref,
        "command_count": len(commands),
        "commands": results,
    }


def parse_pair(value: str) -> Pair:
    if ":" not in value or "=" not in value:
        raise ValidationError(
            f"invalid --pair {value!r}; expected OPERATION:SOURCE=TARGET"
        )
    operation, mapping = value.split(":", 1)
    operation = operation.strip().lower()
    if operation not in OPERATIONS:
        allowed = ", ".join(sorted(OPERATIONS))
        raise ValidationError(
            f"invalid operation {operation!r}; expected one of: {allowed}"
        )
    source, target = mapping.split("=", 1)
    source = source.strip()
    target = target.strip()
    if not source or not target:
        raise ValidationError(
            f"invalid --pair {value!r}; expected OPERATION:SOURCE=TARGET"
        )
    return Pair(operation, source, target)


def safe_path(repo: Path, relative: str) -> Path:
    resolved_repo = repo.resolve()
    path = (resolved_repo / relative).resolve()
    try:
        path.relative_to(resolved_repo)
    except ValueError as exc:
        raise ValidationError(f"path escapes repository root: {relative}") from exc
    return path


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


def line_kinds(lines: Iterable[str]) -> list[str]:
    kinds: list[str] = []
    for line in lines:
        if not line:
            continue
        if line.startswith("# "):
            kinds.append("title")
        elif line.startswith("> "):
            kinds.append("header")
        elif line.startswith("- "):
            kinds.append("example-description")
        elif FULL_COMMAND_RE.fullmatch(line):
            kinds.append("command")
        else:
            kinds.append("other")
    return kinds


def full_commands(lines: Iterable[str]) -> list[str]:
    return [line for line in lines if FULL_COMMAND_RE.fullmatch(line)]


def header_inline_code(lines: Iterable[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        if line.startswith("> "):
            values.extend(INLINE_CODE_RE.findall(line))
    return values


def normalize_command_line(line: str) -> str:
    def replace_placeholder(match: re.Match[str]) -> str:
        content = match.group(1)
        # Optional option groups and literal alternatives affect command behavior.
        if (content.startswith("[-") and content.endswith("]")) or "|" in content:
            return match.group(0)
        return "{{<translated-placeholder>}}"

    return PLACEHOLDER_RE.sub(replace_placeholder, line)


def add_check(
    checks: list[Check],
    code: str,
    ok: bool,
    message: str,
    source: str | None = None,
    target: str | None = None,
    line: int | None = None,
) -> None:
    checks.append(Check(code, ok, message, source, target, line))


def validate_pair(repo: Path, pair: Pair) -> list[Check]:
    checks: list[Check] = []
    operation, source, target = pair.operation, pair.source, pair.target
    source_path = safe_path(repo, source)
    target_path = safe_path(repo, target)
    expected_target = (
        f"pages.zh/{source.removeprefix('pages/')}"
        if source.startswith("pages/")
        else ""
    )
    path_ok = (
        source.startswith("pages/")
        and target.startswith("pages.zh/")
        and target == expected_target
    )
    add_check(
        checks,
        "path_mapping",
        path_ok,
        "source and target platform/filename mapping matches"
        if path_ok
        else f"expected target {expected_target or '<invalid source path>'}",
        source,
        target,
    )

    source_exists = source_path.is_file()
    target_exists = target_path.is_file()
    add_check(
        checks, "source_exists", source_exists, "source page exists", source, target
    )
    add_check(
        checks, "target_exists", target_exists, "target page exists", source, target
    )
    if not source_exists or not target_exists:
        return checks

    tracked = (
        run_git(repo, "cat-file", "-e", f"HEAD:{target}", check=False).returncode == 0
    )
    expected_tracked = operation != "create"
    state_ok = tracked == expected_tracked
    if operation == "create":
        state_message = (
            "create target is new relative to HEAD"
            if state_ok
            else "create target already exists in HEAD"
        )
    else:
        state_message = (
            f"{operation} target exists in HEAD"
            if state_ok
            else f"{operation} target does not exist in HEAD"
        )
    add_check(
        checks,
        "operation_target_state",
        state_ok,
        state_message,
        source,
        target,
    )

    source_raw, source_text, source_lines = read_page(source_path)
    target_raw, target_text, target_lines = read_page(target_path)
    del source_raw

    add_check(
        checks,
        "final_newline",
        target_raw.endswith(b"\n"),
        "target ends with a newline",
        source,
        target,
    )
    trailing_lines = [
        index
        for index, line in enumerate(target_text.splitlines(), start=1)
        if TRAILING_WHITESPACE_RE.search(line)
    ]
    add_check(
        checks,
        "trailing_whitespace",
        not trailing_lines,
        "target has no trailing whitespace"
        if not trailing_lines
        else f"trailing whitespace on lines {trailing_lines}",
        source,
        target,
        trailing_lines[0] if trailing_lines else None,
    )

    source_title = source_lines[0] if source_lines else ""
    target_title = target_lines[0] if target_lines else ""
    add_check(
        checks,
        "title",
        source_title == target_title and source_title.startswith("# "),
        "page titles match"
        if source_title == target_title
        else f"{source_title!r} != {target_title!r}",
        source,
        target,
        1,
    )

    source_kinds = line_kinds(source_lines)
    target_kinds = line_kinds(target_lines)
    add_check(
        checks,
        "structure_order",
        source_kinds == target_kinds,
        "nonblank structural line order matches"
        if source_kinds == target_kinds
        else f"expected {source_kinds}, got {target_kinds}",
        source,
        target,
    )

    for label, marker in (
        ("header_count", "> "),
        ("example_count", "- "),
    ):
        source_count = sum(line.startswith(marker) for line in source_lines)
        target_count = sum(line.startswith(marker) for line in target_lines)
        add_check(
            checks,
            label,
            source_count == target_count,
            f"count matches ({source_count})"
            if source_count == target_count
            else f"expected {source_count}, got {target_count}",
            source,
            target,
        )

    source_commands = full_commands(source_lines)
    target_commands = full_commands(target_lines)
    add_check(
        checks,
        "command_count",
        len(source_commands) == len(target_commands),
        f"command count matches ({len(source_commands)})"
        if len(source_commands) == len(target_commands)
        else f"expected {len(source_commands)}, got {len(target_commands)}",
        source,
        target,
    )
    normalized_source = [normalize_command_line(line) for line in source_commands]
    normalized_target = [normalize_command_line(line) for line in target_commands]
    add_check(
        checks,
        "command_integrity",
        normalized_source == normalized_target,
        "commands match after masking translatable placeholders"
        if normalized_source == normalized_target
        else f"expected {normalized_source}, got {normalized_target}",
        source,
        target,
    )

    source_urls = URL_RE.findall(source_text)
    target_urls = URL_RE.findall(target_text)
    add_check(
        checks,
        "urls",
        source_urls == target_urls,
        "URL sequence matches"
        if source_urls == target_urls
        else f"expected {source_urls}, got {target_urls}",
        source,
        target,
    )

    source_inline = header_inline_code(source_lines)
    target_inline = header_inline_code(target_lines)
    add_check(
        checks,
        "header_inline_code",
        source_inline == target_inline,
        "inline command references match"
        if source_inline == target_inline
        else f"expected {source_inline}, got {target_inline}",
        source,
        target,
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
                raise ValidationError(
                    f"missing source path for status record: {record!r}"
                )
            changes.append(("source-of-rename", records[index]))
            index += 1
    return changes


def allowed_worktree_statuses(operation: str | None) -> set[str]:
    if operation == "create":
        return {"??", "A ", "AM"}
    if operation in {"sync", "revise"}:
        return {" M", "M ", "MM"}
    return set()


def validate_scope(repo: Path, pairs: list[Pair]) -> list[Check]:
    checks: list[Check] = []
    expected_operations = {pair.target: pair.operation for pair in pairs}
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
            target=path,
        )
    return checks


def validation_report(
    repo: Path, pairs: list[Pair], check_scope: bool
) -> dict[str, Any]:
    checks: list[Check] = []
    targets: set[str] = set()
    for pair in pairs:
        if pair.target in targets:
            add_check(
                checks,
                "duplicate_target",
                False,
                f"target appears more than once: {pair.target}",
                pair.source,
                pair.target,
            )
        targets.add(pair.target)
        checks.extend(validate_pair(repo, pair))
    if check_scope:
        checks.extend(validate_scope(repo, pairs))
    failures = [check for check in checks if not check.ok]
    return {
        "ok": not failures,
        "pair_count": len(pairs),
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": [asdict(check) for check in checks],
    }


def print_resolve_text(report: dict[str, Any]) -> None:
    for command in report["commands"]:
        print(
            f"{command['status'].upper():<18} {command['input']} -> {command['normalized']}"
        )
        for candidate in command["candidates"]:
            suffix = " (Chinese target exists)" if candidate["target_exists"] else ""
            print(f"  {candidate['source']} -> {candidate['target']}{suffix}")


def print_validation_text(report: dict[str, Any]) -> None:
    for item in report["checks"]:
        status = "PASS" if item["ok"] else "FAIL"
        location = item["target"] or item["source"] or "batch"
        if item["line"] is not None:
            location = f"{location}:{item['line']}"
        print(f"{status:<4} {item['code']:<24} {location} - {item['message']}")
    print(
        f"Summary: {report['check_count']} checks, {report['failure_count']} failures"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve = subparsers.add_parser(
        "resolve", help="resolve command names against a Git ref"
    )
    resolve.add_argument("--repo", required=True, help="repository root")
    resolve.add_argument("--ref", required=True, help="fetched upstream Git ref")
    resolve.add_argument("--json", action="store_true", dest="output_json")
    resolve.add_argument("commands", nargs="+", help="user-provided command names")

    validate = subparsers.add_parser(
        "validate", help="validate source/target page pairs"
    )
    validate.add_argument("--repo", required=True, help="repository root")
    validate.add_argument(
        "--pair",
        action="append",
        required=True,
        help="OPERATION:SOURCE=TARGET; repeat for the complete batch",
    )
    validate.add_argument("--check-scope", action="store_true")
    validate.add_argument("--json", action="store_true", dest="output_json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        repo = repository_root(args.repo)
        if args.command == "resolve":
            report = resolve_batch(repo, args.ref, args.commands)
            if args.output_json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print_resolve_text(report)
        else:
            pairs = [parse_pair(value) for value in args.pair]
            report = validation_report(repo, pairs, args.check_scope)
            if args.output_json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print_validation_text(report)
        return 0 if report["ok"] else 1
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
