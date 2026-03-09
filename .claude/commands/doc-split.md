---
name: doc-split
description: Auto-split documentation files exceeding size threshold
---

Split oversized documentation files into a directory of smaller, self-contained sub-documents.

## Setup

1. Read `harness.yaml` at the project root. Extract:
   - `docs.max_doc_lines` (default: 200)
   - `docs.root` (default: `docs/`)

2. Determine target files:
   - If a specific file path is provided as an argument, process that file
   - If no argument is provided, scan all `.md` files in `docs/` and process any exceeding `docs.max_doc_lines`

## Splitting Process

For each oversized file:

1. Read the file content in full.

2. Identify natural split points at `##` (h2) headings. Each `##` section becomes a candidate sub-document.

3. **Minimum size guard:** If splitting would produce any sub-document with fewer than 20 lines, merge it with the adjacent section. Do not split a file into fragments that are too small to be useful on their own.

4. Create a directory with the same name as the file (without `.md` extension):
   - `docs/conventions.md` becomes `docs/conventions/`

5. Write each section as a separate file in the new directory:
   - Filename: descriptive kebab-case derived from the heading text
   - Example: `## Import Rules` becomes `import-rules.md`
   - Each sub-doc must be self-contained — include a brief context line at the top if the section assumes knowledge from elsewhere (e.g., "These conventions apply to the source files under `src/`.")

6. Create an index file at `docs/<name>/index.md`:
   - Title: same as the original document title (h1 heading, if present)
   - Body: a brief description of each sub-doc with relative links
   - Example:
     ```markdown
     # Conventions

     - [Import Rules](./import-rules.md) — module import ordering and restrictions
     - [Naming](./naming.md) — variable, function, and file naming standards
     ```

7. Update `AGENTS.md`: find references to the old file path and replace them with the new directory path or index file path.

8. Search the rest of the repo for any other references to the old file path (other docs, comments, config files). Update those references to point to the new index file.

9. Delete the original oversized file.

10. Commit with message: `docs: split <filename> into sub-documents (exceeded <N> line threshold)`

## Rules

- Each sub-doc must be self-contained enough to be useful when read in isolation.
- Sub-doc filenames must be descriptive kebab-case (no generic names like `part-1.md`).
- The index file must briefly describe what each sub-doc covers, not just list links.
- Do not split if the result would produce any sub-doc with fewer than 20 lines — merge small sections together instead.
- Preserve all content from the original file. Do not drop or summarize anything during the split.
- If the original file has a preamble before the first `##` heading, include it in the index file.

$ARGUMENTS
