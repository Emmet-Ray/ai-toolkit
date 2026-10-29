---
name: tldr-en-page-maintainer
description: Maintain English tldr pages, including creating missing pages, updating existing pages from current command evidence, and revising or polishing English content, with eligibility and duplicate checks, evidence-based research, deterministic validation, human review, local commit, fork push, and browser PR handoff. Use when the user provides one or more command names and wants to create or edit English pages in a local tldr-pages/tldr clone. Do not use for translations.
---

# Maintain English tldr Pages

Treat one invocation as one maintenance batch. Keep every user-provided command in the same branch, commit, and PR when repository limits and page relationships permit. Do not silently split or shrink the batch. Run from the root of a local `tldr-pages/tldr` clone.

## Scope and Intent

Support three operations:

- `create`: create a missing English page from current command evidence.
- `update`: update an existing page because command behavior, syntax, documentation, supported platforms, examples, or other factual content has changed or is incomplete.
- `revise`: correct, restructure, rewrite, or polish an existing page within the user's requested scope without intentionally changing documented command behavior.

Infer intent from the request, not merely from page existence. Treat wording such as “补充缺失页面” as `create`, “更新选项/与当前命令同步/补充示例” as `update`, and “修改描述/重写/润色” as `revise`. If a vague “修改” request can reasonably affect command behavior, disclose the ambiguity and recommend `update`; do not silently apply the lower-evidence `revise` workflow.

Default a batch to one operation. Allow mixed operations only when the user clearly assigns them to different commands. Preserve the user's command order.

Support ordinary command pages, subcommand pages, alias pages, grouped-command references, disambiguation pages, and justified platform variants. Do not create or edit translations. End after the PR is created and verified; do not track CI, handle review comments, monitor merging, or clean branches unless separately requested.

Use this state flow:

```text
REQUESTED
  -> REPOSITORY_READY
  -> RESEARCHED
  -> READY_FOR_EDITING
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

- Treat the ordered command set, operation, command identity, page type, and resolved target paths as the batch identity. If any changes, return to research and rerun all affected preflight checks.
- Aggregate all blockers found in a phase. Explain each cause, recommend a concrete resolution, and then ask the user what to do.
- Never invent command behavior, silently drop a command, choose an ambiguous platform or operation, expand a `revise` request into factual `update` work, install or upgrade documented software, stash work, overwrite a branch, bypass hooks, force-push, delete a branch, or rewrite commit history.
- Do not run an example that can modify real user data, devices, accounts, services, or remote state merely to verify it. Prefer official documentation, built-in help, source documentation, and isolated disposable environments.
- Bind every approval to the exact files, content, evidence summary, and plan shown to the user. Any page-content change invalidates `CONTENT_APPROVED`; factual changes also invalidate the affected evidence record. Any material commit or remote-plan change invalidates its corresponding approval.
- Keep `CONTENT_APPROVED`, `LOCAL_FINALIZATION_APPROVED`, and `REMOTE_PREPARATION_APPROVED` distinct.
- Resolve repository paths relative to the repository root and bundled resources relative to this `SKILL.md`.

## Parse the User Input

- Accept command names with an optional operation or requested change for each command. Do not require platform names, page paths, versions, or documentation links.
- Accept one command or a comma-, Chinese-enumeration-comma-, newline-, or natural-language-separated list.
- Preserve spaces inside subcommands. Treat `git commit` and `git-commit` as equivalent lookup forms.
- If command boundaries, command identity, or operation assignments are ambiguous, show the parsed batch, explain the ambiguity, recommend an interpretation, and ask the user before research proceeds.

## Phase 1: Repository Preflight

Enter with `REQUESTED`. Complete these checks without creating a branch:

1. Read the current `.github/PULL_REQUEST_TEMPLATE.md` and extract applicable page or batch limits. The repository document is authoritative; do not assume a new-page limit also applies to updates without reading its wording.
2. Require a clean worktree using `git status --porcelain=v1 --untracked-files=all`. If dirty, list every change and recommend that the user save or finish it. Do not stash, commit, or delete it.
3. Inspect every remote URL. Identify `tldr-pages/tldr` by normalized URL, never by assuming the remote is named `upstream` or `origin`.
4. Run `gh auth status`. If unauthenticated, recommend `gh auth login` and pause. Never handle or print credentials.
5. Fetch the official upstream `main` explicitly.
6. Inspect requested command names against the fetched ref:

   ```text
   python <skill-dir>/scripts/validate_batch.py inspect \
     --repo <repo-root> \
     --ref <official-remote>/main \
     --json \
     <commands...>
   ```

7. Report every existing English path for each normalized command. Enforce the assigned operation only after resolving name collisions and platform variants:
   - `create` requires the exact target path to be absent.
   - `update` and `revise` require the exact target path to exist.
8. Check the requested batch against any applicable repository limits. Include required base, alias-target, grouping, or disambiguation dependencies after research and check again.

Report repository checks, normalized inputs, operation assignments, existing matches, and `REPOSITORY_READY`.

## Phase 2: Research and Resolve the Batch

Enter only with `REPOSITORY_READY`.

Read [references/en-page-authoring-rules.md](references/en-page-authoring-rules.md) completely, then read every current repository section it routes. Current repository rules outrank the bundled summary.

Read the operation-specific instructions for every operation present:

- `create`: [references/create-pages.md](references/create-pages.md)
- `update`: [references/update-pages.md](references/update-pages.md)
- `revise`: [references/revise-pages.md](references/revise-pages.md)

For every command, resolve and record:

- Exact command identity, owning project or operating system, invocation spelling, page type, target path, and operation.
- Current authoritative documentation URL and documented version when known.
- Platform availability, name-collision, alias, grouping, and subcommand relationships relevant to the target.
- Related English pages consulted for style, granularity, and shared terminology.
- Claims requiring evidence under the assigned operation, their primary sources, and any safe verification performed or intentionally skipped.
- Unresolved facts, unsupported edits, safety limitations, and version/platform differences.

Use official documentation, built-in help/man output, and upstream source documentation as command-truth sources. Existing tldr pages are style references, not proof that syntax or behavior is correct. Safely execute examples only when it adds evidence and can be isolated from user data and external state. Do not install the command or broaden permissions without explicit authorization.

Resolve subcommands, aliases, grouping, platform variants, and collisions according to current repository rules. For `create`, apply current project eligibility rules and include missing required dependencies or pause for a scope choice. For `update` and `revise`, do not use maintenance work to introduce an unrelated new page without assigning it an explicit `create` operation.

After resolving exact targets:

1. Recheck applicable repository limits with all required pages.
2. Query open upstream PRs with file data:

   ```text
   gh pr list --repo tldr-pages/tldr --state open --limit 1000 \
     --json number,title,url,files
   ```

   Compare actual changed file paths with every target. Do not infer duplicates from PR titles alone.
3. Verify each target's presence or absence against the fetched upstream ref matches its assigned operation.
4. Create one branch from fetched upstream `main` only after all research and duplicate checks pass.

Choose the branch prefix from the batch operations:

- Only `create`: `add/<batch-slug>`
- Only `update`: `update/<batch-slug>`
- Only `revise`: `revise/<batch-slug>`
- Explicitly mixed: `maintain/<batch-slug>`

Normalize subcommands to hyphenated page names and join multiple commands with `_`. Do not add a date, hash, or random suffix preemptively. If the local name exists, do not reuse or delete it; recommend a readable numeric suffix and ask the user.

Report research records, operation/target mapping, open-PR result, branch name, known versions, unresolved limitations, `RESEARCHED`, and `READY_FOR_EDITING`.

## Phase 3: Edit the Whole Batch

Enter only with `READY_FOR_EDITING`.

Edit every page from the approved research records, current repository rules, and applicable operation references. Apply these shared boundaries:

- Keep a deliberately prioritized set of high-value examples within the current repository maximum. Approximately five examples remains a preference, not a reason to rewrite an unaffected page.
- Order newly created or materially reorganized examples from simple and common to advanced. Keep useful help and version examples last.
- Use imperative descriptions, supported long options when appropriate, standard placeholders, and required heading order.
- Make every new or behavior-changing claim traceable to recorded evidence. Remove or flag an affected claim that cannot be supported.
- Represent dangerous targets with conspicuous placeholders and include `sudo` when genuinely required; never weaken safety to shorten an example.
- Reuse established style from related English pages, but do not copy command-specific behavior without independent evidence.
- Use `python scripts/set-alias-page.py -p <platform>/<alias-command> -l en` without `--stage` when creating or regenerating an alias page, then verify its target and generated form.
- Finish the complete batch before validation.

Record meaningful editorial choices, factual changes, and evidence limitations for review. Report changed files, operation for each, concise change/evidence summary, limitations, and `DRAFTED`.

## Phase 4: Run Hard Validation

Enter only with `DRAFTED`. Hard validation does not decide whether examples are useful or behavior claims are true; those remain evidence and human-review concerns.

Run all of the following against exact target paths:

1. Run the project-local Markdown linter.
2. Run project-local `tldr-lint` against each exact English page without translation ignore codes.
3. Run the bundled validator with the fetched upstream ref, operation for every page, and scope checking:

   ```text
   python <skill-dir>/scripts/validate_batch.py validate \
     --repo <repo-root> \
     --ref <official-remote>/main \
     --check-scope \
     --json \
     --page create:pages/<platform>/<command>.md \
     --page update:pages/<platform>/<command>.md \
     --page revise:pages/<platform>/<command>.md
   ```

   Include only actual pages in the batch. The validator checks target path, operation/target state, platform directory, lowercase filename, heading/filename mapping, page structure, example/command counts, example limit, trailing whitespace, final newline, duplicate targets, and exact worktree scope. It is read-only.

Automatically fix only deterministic formatting or structural failures. After any fix, rerun the entire phase. Never change an option, argument, behavior claim, platform, operation, or example selection as an automatic lint fix. If a failure cannot be fixed reliably, aggregate it, recommend a resolution, and ask the user.

Report hard-check summary, automatic fixes, research limitations, and `VALIDATED`.

## Phase 5: Human Review and Iteration

Enter only with `VALIDATED`. Report exactly:

- Batch commands, operations, and changed-file list.
- Command versions, primary sources, and concise evidence summary appropriate to each operation.
- Unresolved limitations and meaningful factual or editorial decisions.
- Hard-validation summary.
- An explicit statement that nothing has been committed, pushed, or submitted as a PR.

Remind the user that the repository requires genuine human review of AI-assisted pages and ask them to inspect complete local pages. Do not claim human review merely because automated checks passed.

For every requested change, edit the affected page, invalidate evidence affected by factual changes, re-research those claims when needed, rerun the entire hard-validation phase, and present the complete review package again. Never infer approval from silence or an ambiguous reply.

On explicit approval of exact content after disclosure, report `CONTENT_APPROVED`. Do not commit yet.

## Phase 6: Local Finalization

Enter only with `CONTENT_APPROVED`.

1. Read the current `CONTRIBUTING.md` section “Commit message and PR title.”
2. Draft one commit message for the batch. Use current repository rules and recent accepted English-page commits only to resolve uncovered ambiguity.
3. Show exact target files and proposed commit message. Ask for explicit local-finalization authorization.
4. After approval, report `LOCAL_FINALIZATION_APPROVED` and rerun the entire hard-validation phase.
5. If page content changes during final validation, invalidate content approval and return to Phase 4 and human review.
6. Confirm the worktree contains only expected target changes and each change type matches its operation.
7. Stage exact paths with `git add -- <target-pages...>`; never use a broad add.
8. Run `git diff --cached --check`, inspect `git diff --cached --name-status`, and inspect complete staged content.
9. Create exactly one commit with the approved message. Do not use `--no-verify`.
10. Verify commit hash, message, files, content, and post-commit worktree status.

If a hook or commit fails, report the original error and staged state. Do not reset, delete files, bypass the hook, or rewrite history. If a successful commit is later found wrong, stop and ask; do not amend or reset automatically.

On success, report only commit hash/message, committed files, final validation and worktree result, an explicit statement that nothing has been pushed or submitted, and `LOCALLY_FINALIZED`.

## Phase 7: Remote Preparation and PR Handoff

Enter only with `LOCALLY_FINALIZED`. Do not repeat research by default, but recheck facts that became stale or changed after approval.

1. Use `gh api user` to identify the current account.
2. Reuse official upstream from preflight. Identify the user fork by URL, fork relationship, and permission with `gh repo view`; do not assume `origin` is the fork.
3. Require a unique writable fork remote. Never push to official upstream.
4. Read current commit/PR title rules and `.github/PULL_REQUEST_TEMPLATE.md`.
5. Default PR title to commit message and preserve the complete current PR template.
6. Fill in documented command version when known. Check only boxes supported by evidence. Check human review only because exact content reached `CONTENT_APPROVED`. Do not invent versions or issue references. Use `Closes` only when the PR fully resolves a known issue.
7. Show fork remote/repository, remote branch, PR base/head, title, and complete body. Ask for explicit remote-preparation authorization.
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

10. Stop at `PR_READY_FOR_REVIEW`. Ask the user to inspect full diff, base/head, title, version, body, and checklist in the browser.
11. Let the user click “Create pull request” by default. If explicitly asked to submit, reread visible base/head, title, and body first and submit only if they still match the authorized plan.
12. After creation, use `gh pr view` or `gh pr list` to verify PR number, title, URL, base/head, and state.

If push fails, do not force. If a remote branch exists or push is non-fast-forward, report it and ask. If the browser cannot open, preserve the remote branch and provide direct PR-creation target and prefilled content. If submission fails, do not click repeatedly. Never delete the remote branch or modify an already-created PR in this workflow.

On success, report PR number/title/link, base/head and remote branch, batch commands/operations/files, `PR_CREATED`, and that the workflow has ended.

## Bundled Resources

- Read [references/en-page-authoring-rules.md](references/en-page-authoring-rules.md) completely in Phase 2.
- Read only operation references used by the batch.
- Run [scripts/validate_batch.py](scripts/validate_batch.py) for repository inspection and hard validation. Use `--help` for its complete CLI.
