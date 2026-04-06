# Radiology Wiki - Claude Code Schema

This document defines the structure, conventions, and workflows for maintaining a personal radiology knowledge base using LLM assistance.

## Overview

This wiki follows the **LLM Wiki pattern**: raw sources remain immutable, while the LLM incrementally builds and maintains a structured, interlinked collection of markdown files. The human curates sources and asks questions; the LLM handles summarizing, cross-referencing, and maintenance.

## Directory Structure

```
radiology-wiki/
│
├── raw/                              # Immutable source materials (user's own folder structure)
│
├── wiki/                             # LLM-maintained knowledge base
│   ├── index.md                      # Master index of all pages
│   ├── log.md                        # Chronological operation log
│   │
│   ├── shoulder/                     # Topic-based: each file = anatomy + pathology + classification
│   │   ├── rotator-cuff.md           # Includes Cofield, Goutallier, Bigliani, Neer
│   │   ├── instability.md            # GH ligaments + Bankart variants + Hill-Sachs
│   │   ├── labrum.md                 # Anatomy + normal variants
│   │   ├── slap-lesion.md            # Types I-IV + paralabral cysts
│   │   ├── biceps-long-head.md
│   │   ├── rotator-interval.md       # Includes adhesive capsulitis
│   │   ├── nerve-entrapment.md       # Suprascapular + quadrilateral + Parsonage-Turner
│   │   └── shoulder-mri-protocol.md
│   │
│   ├── wrist/                        # (future)
│   ├── elbow/                        # (future)
│   ├── knee/                         # (future)
│   ├── ankle/                        # (future)
│   ├── hip/                          # (future)
│   ├── spine/                        # (future)
│   │
│   ├── _index/                       # Cross-cutting index pages
│   │   └── classifications.md        # All classification systems by region
│   │
│   └── sources/                      # Source summaries
│
├── exports/                          # Generated HTML/PDF outputs
│
└── CLAUDE.md                         # This file
```

### Organization Principle
Each topic page combines **anatomy + pathology + classification** in one file. Classifications are embedded in their relevant topic page (e.g., Goutallier inside rotator-cuff.md) with a separate `_index/classifications.md` as a quick-lookup index. This mirrors clinical thinking: when reading about rotator cuff tears, you want Cofield/Goutallier right there, not in a separate folder.

## File Naming Conventions

- Use **kebab-case** for all filenames: `slap-lesion.md`, `rotator-cuff.md`
- Use **lowercase** only
- No spaces, use hyphens
- Be specific: `goutallier-fatty-infiltration.md` not `goutallier.md`

## Wiki Links

Use Obsidian-style wiki links for cross-references:

```markdown
See also: [[rotator-cuff]], [[slap-lesion]]
Associated with [[bankart-lesion]] in 22% of cases.
Classification: [[goutallier-fatty-infiltration]]
```

## Page Templates

### Topic Page (`wiki/[region]/[topic].md`)

Each topic page combines anatomy, pathology, and classification in one file:

```markdown
# [Topic Name]

## Anatomy
- Structure, origin, insertion, innervation
- MRI appearance by plane

---

## Pathology: [Condition Name]

### Definition
[Brief definition]

### Mechanism / Etiology
- [Cause 1]

### Classification: [Name] {#anchor-id}
| Grade/Type | Criteria | Significance |
|------------|----------|-------------|
| I          | ...      | ...         |

### MRI Findings
- [Finding 1]

### Associated Conditions
- [[related-topic]] (percentage if known)

---

## Pitfalls
- [Common mistakes across all sections]

## Key Points
- [Most important takeaways]

## References
- Author et al. Journal. Year;Volume:Pages.
```

### Imaging Protocol Page (`wiki/[region]/[region]-mri-protocol.md`)

```markdown
# [Body Part] MRI Protocol

## Coil / Patient Position
## Sequences (tables for conventional + arthrography)
## Key Structures to Evaluate (checklists by plane)
## Common Pitfalls
## References
```

### Source Summary Page (`wiki/sources/`)

```markdown
# [Source Title]

## Metadata
- **Type**: Lecture / Paper / Textbook Chapter
- **Date**: YYYY-MM-DD
- **Author**: 
- **Source file**: `raw/[path]/[filename]`

## Summary
[2-3 sentence overview]

## Key Topics Covered
- [[topic-1]]
- [[topic-2]]

## New Information Added
- [What was learned from this source]

## Pages Updated
- [[page-1]] - added X
- [[page-2]] - updated Y
```

## Special Files

### index.md

Master index organized by category:

```markdown
# Radiology Wiki Index

Last updated: YYYY-MM-DD
Total pages: [count]

## Anatomy
### Shoulder
- [[rotator-cuff]] - Supraspinatus, infraspinatus, teres minor, subscapularis
- [[labrum]] - Glenoid labrum anatomy and variants
...

## Pathology
### Shoulder
- [[slap-lesion]] - Superior labrum anterior to posterior tear
- [[bankart-lesion]] - Anterior labral tear with/without bone
...

## Classifications
- [[goutallier-fatty-infiltration]] - Muscle fatty degeneration grading
- [[cofield-tear-size]] - Rotator cuff tear size classification
...

## Syndromes
- [[throwing-shoulder]] - Overhead athlete shoulder complex
...

## Imaging Protocols
- [[shoulder-mri-protocol]]
- [[wrist-mri-protocol]]
...
```

### log.md

Chronological operation log:

```markdown
# Wiki Operation Log

## [YYYY-MM-DD] ingest | Source Title
- Processed: `raw/path/file.pdf`
- Pages created: [[new-page]]
- Pages updated: [[existing-page]]
- Summary: [Brief description]

## [YYYY-MM-DD] query | Question Asked
- Question: "..."
- Answer filed as: [[new-page]] (if applicable)

## [YYYY-MM-DD] lint | Health Check
- Orphan pages found: [[page]]
- Missing links identified: [concept]
- Contradictions: [description]
```

## Operations

### 1. Ingest (Add New Source)

When instructed to ingest a new source:

1. **Read** the source file from `raw/`
2. **Discuss** key takeaways with the user
3. **Create** a source summary in `wiki/sources/`
4. **Update or create** relevant wiki pages:
   - Anatomy pages for new structures
   - Pathology pages for conditions
   - Classification pages for grading systems
5. **Add wiki links** to connect related pages
6. **Update** `index.md` with new pages
7. **Log** the operation in `log.md`

Example command: `"Ingest raw/textbooks/shoulder-mri-chapter3.pdf"`

### 2. Query (Ask Questions)

When answering questions:

1. **Read** `index.md` to find relevant pages
2. **Read** the relevant wiki pages
3. **Synthesize** an answer with citations to wiki pages
4. **Offer** to file the answer as a new page if valuable
5. **Respond in Chinese** while keeping medical terms in English

Example: `"What are the MRI findings of SLAP lesion?"`

### 3. Lint (Health Check)

When instructed to lint:

1. **Check** for orphan pages (no inbound links)
2. **Identify** mentioned concepts without their own page
3. **Find** contradictions between pages
4. **Suggest** missing cross-references
5. **Recommend** new sources to fill gaps
6. **Report** findings and offer to fix issues

Example command: `"Lint the wiki"` or `"Health check"`

## Writing Style Guidelines

### Language
- **Wiki content**: English
- **Explanations to user**: Chinese (Traditional)
- **Medical terminology**: Always English, even in Chinese explanations

### Formatting
- Use tables for classifications and comparisons
- Use bullet points for lists
- Bold **key terms** on first mention
- Keep paragraphs short (2-4 sentences)

### Citations
- Always include original references
- Format: `Author et al. Journal. Year;Volume:Pages.`
- Link to wiki pages when citing internal knowledge

### Accuracy
- Preserve exact percentages and measurements from sources
- Note when data conflicts between sources
- Mark uncertain information with [?] or "reportedly"

## qmd Integration

For searching across 250+ files, use qmd:

```bash
# Search the wiki
qmd search "SLAP lesion MRI"
qmd query "rotator cuff tear classification"

# Get specific document
qmd get "wiki/pathology/shoulder/slap-lesion.md"
```

## Git Workflow

```bash
# After major changes
git add .
git commit -m "ingest: [source name]" 
# or "update: [pages changed]"
# or "lint: [fixes made]"
git push
```

## Quick Reference

| Task | Command |
|------|---------|
| Add new source | "Ingest raw/path/file.pdf" |
| Ask question | Just ask in Chinese |
| Find information | "Search for [topic]" |
| Health check | "Lint the wiki" |
| Update index | "Rebuild index" |
| View status | "Wiki status" |
