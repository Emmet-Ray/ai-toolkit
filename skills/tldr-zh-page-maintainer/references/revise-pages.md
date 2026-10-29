# Revise Existing Chinese Pages

Use these instructions only for a `revise` operation.

- Require the target page to exist in the fetched official upstream `main`.
- Treat the user's requested correction, retranslation, terminology change, or polishing scope as the editing boundary.
- Read the complete English and Chinese pages before editing. Use the English page to preserve meaning, structure, examples, command behavior, literals, URLs, and placeholders.
- Before branching, disclose English/Chinese structural or content drift outside the requested revision. Ask whether to expand the page to `sync`; do not silently include unrelated synchronization work.
- Improve the requested wording in context, not as an isolated sentence. Reuse established terminology from current project templates and nearby `pages.zh` pages.
- Do not opportunistically rewrite unrelated acceptable wording. Directly adjacent changes are allowed only when needed for grammar, terminology consistency, or readability; record material discretionary changes.
- If the requested wording would change the command's behavior or contradict the English source, stop and explain the conflict.
- Summarize the revised passages by purpose for human review without attaching a full diff unless requested.

A `revise` operation is complete when the requested language change is accurate and natural, the page remains structurally and semantically compatible with the English source, and no undisclosed scope expansion occurred.
