---
name: tldr-zh-page-maintainer
description: Maintain Simplified Chinese tldr pages from their current English sources, including creating missing translations, synchronizing existing pages, and revising or polishing Chinese wording, with deterministic validation, human review, local commit, fork push, and browser PR handoff. Use when the user provides one or more tldr command names and wants to create or update pages.zh content in a local tldr-pages/tldr clone. Do not use for editing English pages or adding other locales.
---

# Maintain tldr Simplified Chinese Pages

Treat one skill invocation as one maintenance batch. Keep every user-provided command in the same branch, commit, and PR unless the user explicitly changes the batch. Run from the root of a local `tldr-pages/tldr` clone.

## Scope and Intent

Support three operation types:

- `create`: create a missing Chinese page from the current English page.
- `sync`: synchronize an existing Chinese page with the current English page while preserving accurate existing Chinese wording.
- `revise`: correct, retranslate, or polish an existing Chinese page within the user's requested scope, using the English page as the semantic and structural boundary.

Infer intent from the user's request, not merely from whether the target exists. Treat wording such as “补充缺失翻译” as `create`, “与英文同步” as `sync`, and “修正翻译” or “润色” as `revise`. If the request only says “翻译” and the target already exists, report that fact and ask whether the user wants synchronization or revision; do not silently choose.

Default a batch to one operation type. Allow a mixed batch only when the user clearly requests different operations for different commands. Preserve the user's command order.

End after the PR is created and verified. Do not track CI, handle review comments, monitor merging, clean branches, or edit English pages unless separately requested.

Use this state flow:

```text
REQUESTED
  -> PREFLIGHTED
  -> READY_FOR_EDIT
  -> DRAFTED
  -> VALIDATED
  -> CONTENT_APPROVED
  -> LOCAL_FINALIZATION_APPROVED
  -> LOCALLY_FINALIZED
  -> REMOTE_PREPARATION_APPROVED
  -> PR_READY_FOR_REVIEW
  -> PR_CREATED
```

## Global Controls

- Treat the ordered command set, operation assigned to each command, and resolved source/target mapping as the batch identity. If any of them changes, return to preflight and rerun it completely.
- Aggregate all blockers found in a phase. Explain each cause, recommend a concrete resolution, and then ask the user what to do.
- Never silently drop a command, choose an ambiguous platform or operation, expand a `revise` request into a full synchronization, stash work, overwrite a branch, bypass hooks, force-push, delete a branch, or rewrite commit history.
- Bind every approval to the exact files and plan shown to the user. Any page-content change invalidates `CONTENT_APPROVED`. Any material commit or remote-plan change invalidates its corresponding approval.
- Keep `CONTENT_APPROVED`, `LOCAL_FINALIZATION_APPROVED`, and `REMOTE_PREPARATION_APPROVED` distinct.
- Resolve paths relative to the repository root. Resolve bundled resources relative to this `SKILL.md`.

## Parse the User Input

- Accept command names with an optional operation for each command. Do not require platform names, repository paths, or page paths.
- Accept one command or a comma-, Chinese-enumeration-comma-, newline-, or natural-language-separated list.
- Preserve spaces inside subcommands. Treat `git commit` and `git-commit` as equivalent lookup forms.
- If command boundaries or operation assignments are ambiguous, show the parsed batch, explain the ambiguity, recommend an interpretation, and ask the user to confirm within preflight.

## Phase 1: Preflight

Enter with `REQUESTED`. Complete all checks before creating a branch.

1. Read the current `.github/PULL_REQUEST_TEMPLATE.md` and extract any applicable page or batch limit. The repository document is authoritative; do not assume a limit applies equally to new and updated pages without reading its wording.
2. Require a clean worktree using `git status --porcelain=v1 --untracked-files=all`. If dirty, list every change and recommend that the user save or finish it. Do not stash, commit, or delete it.
3. Inspect every remote URL. Identify `tldr-pages/tldr` by normalized URL, never by assuming the remote is named `upstream` or `origin`.
4. Run `gh auth status`. If unauthenticated, recommend `gh auth login` and pause. Never handle or print credentials.
5. Fetch the official upstream `main` explicitly.
6. Run the bundled resolver against the fetched ref:

   ```text
   python <skill-dir>/scripts/validate_batch.py resolve \
     --repo <repo-root> \
     --ref <official-remote>/main \
     --json \
     <commands...>
   ```

7. Require exactly one English source page for every command. Use the returned `target_exists` fact to enforce the assigned operation:
   - `create` requires a missing Chinese target.
   - `sync` and `revise` require an existing Chinese target.
8. For every `revise` page, compare the current English and Chinese pages before branching. If the English page contains structural or content changes outside the requested revision, report them and ask whether to expand that page to `sync`; do not make that scope change implicitly.
9. Query open upstream PRs with file data, using a sufficiently high limit:

   ```text
   gh pr list --repo tldr-pages/tldr --state open --limit 1000 \
     --json number,title,url,files
   ```

   Compare actual changed file paths with every target page. Do not infer duplicates from PR titles alone.
10. Create one branch from the fetched upstream `main` only after every check passes.

Choose the branch prefix from the batch operations:

- Only `create`: `translate-zh/<batch-slug>`
- Only `sync`: `sync-zh/<batch-slug>`
- Only `revise`: `revise-zh/<batch-slug>`
- Explicitly mixed: `maintain-zh/<batch-slug>`

Normalize a subcommand to a hyphenated page name and join multiple commands with `_`. Do not add a date, hash, or random suffix preemptively. If the local name already exists, do not reuse or delete it; recommend a readable numeric suffix and ask the user.

Report the ordered operation/source/target mapping, all check results, the branch name, `PREFLIGHTED`, and then `READY_FOR_EDIT`.

## Phase 2: Edit the Whole Batch

Enter only with `READY_FOR_EDIT`.

Read [references/zh-translation-rules.md](references/zh-translation-rules.md) completely, then read every fixed and conditional repository reference routed by that document. Current repository rules outrank the bundled summary.

Read the operation-specific instructions for every operation present in the batch:

- `create`: [references/create-pages.md](references/create-pages.md)
- `sync`: [references/sync-pages.md](references/sync-pages.md)
- `revise`: [references/revise-pages.md](references/revise-pages.md)

Before editing each page, search `pages.zh` for the closest pages in the same command family. Reuse established terminology, recurring descriptions, and placeholders when they fit the current English source. Treat sibling pages as wording references only; the current English source remains authoritative for meaning, structure, and command behavior.

Finish every page in the batch before validation. Record uncertain terminology and material editing decisions without repeatedly interrupting the user. Pause only when the English meaning cannot be understood reliably or a requested revision would change command behavior.

Report the edited files, operation for each file, material synchronization or revision decisions, uncertainty list, and `DRAFTED`.

## Phase 3: Run Hard Validation

Enter only with `DRAFTED`. Do not judge naturalness or translation preference here.

Run all of the following against the exact target paths:

1. Run the project-local Markdown linter.
2. Read the current `scripts/test.sh` and run the project-local `tldr-lint` with the exact ignore codes currently used for `pages.zh`. Do not use a bare invocation whose behavior differs from CI.
3. Run the bundled validator with every source/target pair, its operation, and scope checking enabled:

   ```text
   python <skill-dir>/scripts/validate_batch.py validate \
     --repo <repo-root> \
     --check-scope \
     --json \
     --pair create:pages/<platform>/<command>.md=pages.zh/<platform>/<command>.md \
     --pair sync:pages/<platform>/<command>.md=pages.zh/<platform>/<command>.md \
     --pair revise:pages/<platform>/<command>.md=pages.zh/<platform>/<command>.md
   ```

   Include only the actual pairs in the batch. The validator checks operation/target state, mapping, titles, structural order, header/example/command counts, URLs, inline command references, command integrity with translatable placeholders masked, trailing whitespace, final newlines, and exact worktree scope. It is read-only.

Automatically fix only deterministic hard failures. After any fix, rerun the entire phase. If a failure cannot be fixed reliably, aggregate it, recommend a resolution, and ask the user. Do not advance while any hard failure remains.

Report the hard-check summary, automatic fixes, carried uncertainty list, and `VALIDATED`.

## Phase 4: Human Review and Iteration

Enter only with `VALIDATED`. By default, report exactly:

- Batch commands, operation assignments, and changed-file list.
- Recorded uncertain terms and material synchronization or revision decisions.
- Hard-validation summary.
- An explicit statement that nothing has been committed, pushed, or submitted as a PR.

Do not attach full pages, a complete diff, or auto-fix details unless requested. Ask the user to inspect the local pages.

For every requested change, edit the affected page, invalidate `VALIDATED`, rerun the entire hard-validation phase, and present the same four-item review package. Never infer approval from silence or an ambiguous reply.

On explicit overall content approval after disclosure, report `CONTENT_APPROVED`. Do not commit yet.

## Phase 5: Local Finalization

Enter only with `CONTENT_APPROVED`.

1. Read the current `CONTRIBUTING.md` section “Commit message and PR title.”
2. Draft one commit message for the entire batch. Use current repository rules and recent accepted commits only to resolve uncovered ambiguity.
3. Show the exact target files and proposed commit message. Ask for explicit local-finalization authorization.
4. After approval, report `LOCAL_FINALIZATION_APPROVED` and rerun the entire hard-validation phase.
5. If any file changes during final validation, invalidate content approval and return to Phase 3 and human review.
6. Confirm that the worktree contains only the expected target changes and that each target's change type matches its assigned operation.
7. Stage exact paths with `git add -- <target-pages...>`; never use a broad add.
8. Run `git diff --cached --check`, inspect `git diff --cached --name-status`, and inspect the staged content.
9. Create exactly one commit with the approved message. Do not use `--no-verify`.
10. Verify the new commit's hash, message, files, content, and post-commit worktree status.

If a hook or commit fails, report the original error and staged state. Do not reset, delete files, bypass the hook, or rewrite history. If a successful commit is later found wrong, stop and ask the user; do not amend or reset automatically.

On success, report only the commit hash/message, committed files, final validation and worktree result, an explicit statement that nothing has been pushed or submitted, and `LOCALLY_FINALIZED`.

## Phase 6: Remote Preparation and PR Handoff

Enter only with `LOCALLY_FINALIZED`. Do not repeat preflight's upstream fetch, page-state checks, or open-PR duplicate scan by default.

1. Use `gh api user` to identify the current account.
2. Reuse the official upstream found in preflight. Identify the user fork by URL, fork relationship, and permission with `gh repo view`; do not assume `origin` is the fork.
3. Require a unique writable fork remote. Never push to the official upstream.
4. Read the current commit/PR title rule and `.github/PULL_REQUEST_TEMPLATE.md`.
5. Default the PR title to the commit message. Preserve the complete current PR template.
6. Check only boxes supported by actual evidence. Check the human-review item only because the batch reached `CONTENT_APPROVED`. Do not invent command versions or issue references. Use `Closes` only when the PR fully resolves a known issue.
7. Show the fork remote/repository, remote branch, PR base/head, title, and complete body. Ask for explicit remote-preparation authorization.
8. After approval, report `REMOTE_PREPARATION_APPROVED` and push with `git push -u <fork-remote> HEAD`. Never force-push.
9. Open the prefilled form without creating the PR:

   ```text
   gh pr create --repo tldr-pages/tldr \
     --base main \
     --head <user>:<branch> \
     --title <title> \
     --body-file <temporary-body-file> \
     --web
   ```

10. Stop at `PR_READY_FOR_REVIEW`. Ask the user to inspect the full diff, base/head, title, body, and checklist in the browser.
11. Let the user click “Create pull request” by default. If the user explicitly asks the agent to submit, reread the visible base/head, title, and body first and submit only if base/head still match the authorized plan.
12. After creation, use `gh pr view` or `gh pr list` to verify the PR number, title, URL, base/head, and state.

If push fails, do not force. If a remote branch already exists or the push is non-fast-forward, report it and ask. If the browser cannot open, preserve the remote branch and provide the direct PR-creation target and prefilled content. If submission fails, do not click repeatedly. Never delete the remote branch or modify an already-created PR in this workflow.

On success, report the PR number/title/link, base/head and remote branch, batch commands/operations/files, `PR_CREATED`, and that the workflow has ended.

## Bundled Resources

- Read [references/zh-translation-rules.md](references/zh-translation-rules.md) completely in Phase 2.
- Read only the operation references used by the batch.
- Run [scripts/validate_batch.py](scripts/validate_batch.py) for source resolution and hard validation. Use `--help` for its complete CLI.
