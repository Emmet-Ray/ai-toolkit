# Create Missing Chinese Pages

Use these instructions only for a `create` operation.

- Require the target page to be absent from the fetched official upstream `main`.
- Create the target at the exact `pages.zh/<platform>/<command>.md` path mapped from the English source.
- Mirror the current English page's structure, meaning, example count, and example order.
- Translate all applicable natural-language content and translatable placeholders. Preserve command behavior, fixed literals, syntax, URLs, and official names.
- For an alias page, use the repository's `scripts/set-alias-page.py` with locale `zh`, then verify the generated page against the current template.
- Complete the full page; do not leave untranslated English prose unless current repository rules require it to remain unchanged.

A `create` operation is complete when the new page fully represents the current English source and all uncertain wording has been recorded for review.
