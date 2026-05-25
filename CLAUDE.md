# Research Wiki: [Your Topic]

## Project Structure

- `research/raw/` — Immutable source documents. Never modify files here.
- `research/wiki/` — LLM-generated and maintained markdown pages.
- `research/wiki/index.md` — Master content catalog. Update on every operation.
- `research/wiki/log.md` — Append-only operation log.
- `research/outputs/` — Generated reports, presentations, lint results.

## Page Types and Conventions

Every wiki page must have YAML frontmatter:

    ---
    title: Page Title
    type: concept | entity | source-summary | comparison
    sources:
      - research/raw/papers/filename.md
    related:
      - "[[related-concept]]"
    created: YYYY-MM-DD
    updated: YYYY-MM-DD
    confidence: high | medium | low
    ---

### Naming

- Filenames: kebab-case matching the concept (e.g., attention-mechanism.md)
- Cross-references: use [[wikilinks]] for all internal links
- Source references: always link back to research/raw/ file paths

## Workflows

### Ingest

1. Read the source document in research/raw/
2. Discuss key takeaways with the user
3. Create research/wiki/sources/[source-name].md summary
4. Update or create concept/entity pages as needed
5. Update research/wiki/index.md with new entries
6. Append to research/wiki/log.md

### Query

1. Read research/wiki/index.md to identify relevant pages
2. Read those pages and synthesize an answer
3. Cite sources using [[wikilinks]]
4. If the answer is novel and valuable, offer to save it as a new wiki page

### Lint

1. Scan all wiki pages for contradictions
2. Identify orphan pages (no incoming links)
3. Flag missing concepts referenced but not created
4. Find stale claims superseded by newer sources
5. Save results to research/outputs/lint-YYYY-MM-DD.md
