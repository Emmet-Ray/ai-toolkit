# tldr English Page Maintenance Rules

This document summarizes English-page research and editing decisions that are easy to miss. It applies to creating, updating, and revising pages and routes to the current tldr repository rather than replacing its rules. Operation-specific references determine the editing and evidence scope.

## Authority Order

When sources disagree, use this order:

1. The command's observed behavior in the documented version, when safely reproducible.
2. Current official usage documentation and built-in help/man output.
3. Current upstream source documentation, tests, and release notes.
4. The tldr repository's current `CONTRIBUTING.md` and `contributing-guides/style-guide.md` for page policy and presentation.
5. Existing related English tldr pages for style and granularity only.
6. Maintained third-party documentation when the project explicitly lacks usable primary documentation.
7. General knowledge.

Never let an existing tldr page override primary evidence about another command's syntax or behavior. If primary sources disagree materially, record the command version and the discrepancy and stop before drafting the disputed example.

## Required Repository Reading

For every batch, read the current versions of:

- `.github/PULL_REQUEST_TEMPLATE.md` for applicable page limits, checklist, version field, and AI-assisted human-review requirement.
- `CONTRIBUTING.md` sections covering project eligibility, Guidelines, Directory structure, Markdown format, Subcommands, Inclusive language, local testing, PR submission, commit/PR titles, and Name collisions.
- `contributing-guides/style-guide.md` sections covering General layout, Pages, General writing, Heading, Example descriptions, Example commands, and English-Specific Rules.
- `scripts/test.sh` and `package.json` to determine the current project-local lint entry points.

Read the Windows-Specific Rules when any target is under `pages/windows`. Read alias, grouping, disambiguation, subcommand, and keypress sections only when the corresponding page type needs them.

## Establish Command Identity and Eligibility

Before choosing a filename, distinguish the executable or subcommand from the project name, similarly named commands, shell built-ins, aliases, plugins, and legacy versions.

Record:

- Exact invocation and case.
- Owning project or operating system.
- Official documentation and source repository.
- Documented or observed version.
- Supported operating systems.
- Whether the page describes a base command, subcommand, alias, grouped reference, or disambiguation.

Always establish command identity. Apply the current repository eligibility rule for project age and notability when creating a page or when an update introduces a newly documented command or project. Prefer dated releases, repository history, package history, or longstanding OS inclusion as evidence. If a young project may qualify as notable, treat notability as a maintainer judgment and ask the user before proceeding rather than asserting it.

## Resolve Page Type, Name, and Platform

- Match the filename to the invoked command, not the project name, whenever possible.
- Lowercase Markdown filenames. Convert spaces between a program and subcommand to hyphens; preserve meaningful punctuation that belongs to the invoked command.
- Preserve the command's official casing in the page heading and examples, especially for PowerShell.
- Use `pages/common` only when the command is available on at least two supported platforms and the documented examples behave compatibly there.
- Use the current platform directory from `CONTRIBUTING.md` when the command is available on only one supported platform or when behavior requires a platform-specific page.
- Do not infer cross-platform support merely because a package can theoretically be compiled elsewhere. Require documented support or safe evidence.
- If a same-named page exists on another platform, determine whether the request is already adequately covered, needs a legitimate platform variant, or is a name collision.
- For a subcommand page, ensure the base command page exists or include the necessary base page in the same batch. Follow the repository's current rule for subcommand references.
- For an alias, ensure the target page exists and use `scripts/set-alias-page.py` with language `en`.
- For collisions, follow the current disambiguation format and include every newly required page in the batch count.

Do not create separate subcommand pages merely because the command has subcommands. Split only when the base page cannot clearly cover the important workflows or the command family already uses that granularity.

## Build an Evidence Record

For `create`, create one record per proposed example before drafting. For `update`, create records for every new, changed, removed, or behavior-affected claim and example. For `revise`, record enough source context to prove the revised wording preserves existing command meaning; if meaning changes, reclassify the page as `update` before editing.

Each required record should include:

- Intended user task and why it belongs among the page's limited examples.
- Exact command skeleton, including subcommands, options, positional arguments, redirections, and fixed literals.
- Primary source supporting each syntax element and behavior claim.
- Applicable version and platform constraints.
- Verification method: official docs, built-in help/man, source tests, or safe isolated execution.
- Safety notes and whether execution was intentionally skipped.

The evidence record stays outside the contribution unless the user asks to preserve it. Summarize it during human review.

### Verification Boundaries

- Prefer read-only built-in commands such as `--help`, `--version`, `man`, or `Get-Help` when available.
- Use a disposable temporary directory or other isolated local fixture for safe filesystem examples.
- Do not use actual credentials, production services, personal repositories, real devices, system configuration, package installation, privileged mutations, paid APIs, or remote writes for verification.
- Do not install or upgrade the documented command without explicit user authorization.
- A successful lint proves page syntax, not command correctness.
- If an example cannot be executed safely, primary documentation can support it; disclose the skipped execution instead of treating it as a failure.
- If no reliable source supports a behavior claim, remove the claim or ask the user. Never fill the gap from analogy.

## Select and Order Examples

Use the current repository maximum; it is presently eight, while approximately five examples is the normal target.

Prioritize:

1. The simplest useful invocation or the command's primary purpose.
2. Frequent tasks that distinguish this command from its parent or related tools.
3. Important options that users commonly need and can understand without unrelated setup.
4. A safe way to inspect or simulate destructive work when the command supports one.
5. Help and version commands last, when they are useful enough to include.

Avoid exhaustive option catalogs, redundant examples, obscure combinations, explanations of general shell concepts, and examples that require large external setups merely to look realistic. Introduce complexity gradually.

For command families, inspect the closest sibling pages before drafting. Reuse appropriate shared descriptions, placeholders, option formatting, and page granularity, while independently verifying command-specific syntax and behavior.

## Write the Page

### Heading

- Keep the program description short and do not begin by repeating the page title unless the executable and project names differ.
- Use the repository's required order for clarification, notes, subcommand mentions, See also, and More information.
- Prefer a direct, unversioned or latest English usage-documentation URL from the author. Use the current repository-supported fallback only when primary documentation is unavailable.
- Enclose links in angle brackets and remove redundant locale or version components when repository rules require it.

### Example Descriptions

- Use imperative mood.
- Use inclusive language and the repository's standardized terms.
- Wrap commands, paths, extensions, environment variables, and standard streams in backticks as specified by the style guide.
- Add short-option mnemonics only when they accurately match official documentation and improve comprehension.
- State meaningful version or platform limitations without bloating every example.

### Example Commands

- Prefer supported long options. If both forms help clients, use the repository's option-placeholder syntax.
- Use short, descriptive `snake_case` placeholders for user-chosen values.
- Keep mandatory syntax outside placeholders and user choices inside them.
- Use explicit literals when the description promises that exact value.
- Use conspicuous placeholders for devices, destructive paths, identifiers, and other targets that must not be copied thoughtlessly.
- Include `sudo` when root privileges are genuinely required and the command does not prompt for privilege itself.
- Follow platform path and PowerShell casing rules.
- Keep help and version examples in that order at the end when included.

## Editing Completion Conditions

A batch is ready for hard validation only when:

- Every target path is resolved and its presence or absence matches the assigned operation.
- Every required base, alias target, grouped reference, or disambiguation dependency is satisfied.
- Project eligibility and platform placement have evidence where the operation affects them.
- Every claim requiring evidence under the assigned operation has a traceable source.
- The page stays within the current example limit and contains a deliberately prioritized set of examples.
- All known version differences, unsafe verification gaps, and editorial uncertainties are recorded for human review.

Hard validation checks formatting and local invariants. It does not replace evidence review or the user's required human review.
