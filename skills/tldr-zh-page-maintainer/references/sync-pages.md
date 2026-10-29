# Synchronize Existing Chinese Pages

Use these instructions only for a `sync` operation.

- Require the target page to exist in the fetched official upstream `main`.
- Compare the entire current English page with the existing Chinese page before editing. Identify structural, semantic, command, placeholder, URL, and standard-template differences.
- Treat the current English page as authoritative for content, structure, example count, example order, and command behavior.
- Preserve existing Chinese wording when it remains accurate, natural, and consistent with current project rules. Do not rewrite unaffected text merely to produce a larger diff.
- Add, remove, split, merge, or reorder Chinese content only as needed to match the current English page.
- Apply current Chinese templates and style rules to newly synchronized content. Fix directly adjacent inconsistencies when necessary for a coherent result, and record material discretionary changes.
- For an alias page, use the repository's current alias template and tooling rather than manually preserving an outdated generated form.
- Summarize material synchronization changes for human review, such as added examples, removed descriptions, changed URLs, or updated command syntax.

A `sync` operation is complete when the whole Chinese page represents the current English page, accurate existing translations have been retained where practical, and material changes have been recorded.
