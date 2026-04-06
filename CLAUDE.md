# Radiology Wiki - Schema

A personal MSK radiology knowledge base maintained by LLM, following the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Core Principles

1. **Raw sources are immutable** — originals stay untouched in `raw/`
2. **Wiki is the compiled knowledge** — LLM writes and maintains all pages
3. **Knowledge compounds** — each source integrates into existing pages, not isolated
4. **Human curates, LLM maintains** — you decide what to ingest and ask questions; LLM handles organization, cross-referencing, and bookkeeping

## Directory Structure

```
radiology-wiki/
├── raw/                    # Source materials being processed (temporary)
├── wiki/                   # LLM-maintained knowledge base
│   ├── _index.md           # Master index
│   ├── _classifications.md # Quick reference to all classifications
│   ├── _log.md             # Operation log
│   ├── shoulder/           # Region folders
│   │   ├── _overview.md    # Protocol, checklist for this region
│   │   └── [topics].md     # Topic pages
│   ├── wrist/
│   ├── elbow/
│   ├── knee/
│   ├── ankle/
│   ├── hip/
│   ├── spine/
│   └── sources/            # Source summaries
└── CLAUDE.md               # This file
```

## Organization Principles

### By Region
Knowledge is organized by body region because that's how radiologists think.

### Grouping
Related knowledge stays together (anatomy + pathology + classification for a structure). Split into separate files only when content becomes too large.

### Flexibility
- Not every region needs the same pages
- Not every page needs the same sections
- Let content determine structure

## Knowledge Structure

### Anatomy (for structures)
Typical elements:
- Components / Attachments
- Function
- Normal MRI appearance
- Normal variants

### Pathology (for conditions)
Typical elements:
- Mechanism / Etiology
- Classification (if applicable)
- MRI Findings (primary & secondary signs)
- Associated conditions
- Pitfalls / DDx
- References

Not all elements are required — use what fits the content.

## Naming Conventions

- **Filenames**: kebab-case, lowercase (`rotator-cuff.md`)
- **Special files**: underscore prefix (`_index.md`, `_overview.md`)
- **Wiki links**: shortest path unless ambiguous (`[[rotator-cuff]]`, not `[[shoulder/rotator-cuff]]`)

## Operations

### Ingest
Add new source material to the wiki.

1. Read source from `raw/`
2. Discuss key content with user
3. Update or create relevant wiki pages
4. Add `[[wiki-links]]` to connect related content
5. Update `_index.md` and `_classifications.md` if needed
6. Log in `_log.md`

### Query
Answer questions using wiki knowledge.

1. Find relevant pages
2. Synthesize answer with citations to wiki pages
3. **Respond in Chinese, keep medical terms in English**
4. Offer to file valuable answers as new content

### Lint
Health check the wiki.

1. Find orphan pages (no inbound links)
2. Find mentioned concepts without pages
3. Find missing cross-references
4. Suggest improvements
5. Report and offer to fix

## Special Files

### _index.md
Master index organized by region. Lists all pages with brief descriptions.

### _classifications.md
Quick reference linking to classification sections across all pages.
```markdown
## Shoulder
- **Cofield (tear size)** — [[rotator-cuff#Cofield]]
- **Goutallier (fatty infiltration)** — [[rotator-cuff#Goutallier]]

## Wrist
- **Palmer (TFCC)** — [[tfcc#Palmer-Classification]]
```

### _log.md
Chronological record of operations.
```markdown
## [YYYY-MM-DD] ingest | Source Title
- Pages updated: [[page1]], [[page2]]
- Summary: [what was added]
```

### _overview.md (per region)
Region-specific imaging protocol and systematic review checklist.

## Language

- **Wiki content**: English
- **Responses to user**: Traditional Chinese (繁體中文)
- **Medical terms**: Always English

## Git Workflow

```bash
git add .
git commit -m "ingest: [source]"  # or "update:", "lint:"
git push
```

## Quick Commands

| Task | Command |
|------|---------|
| Add source | "Ingest [description]" |
| Ask question | Just ask in Chinese |
| Health check | "Lint" |
| Rebuild index | "Rebuild index" |
