# Radiology Wiki - Claude Code Schema

This document defines the structure, conventions, and workflows for maintaining a personal radiology knowledge base using LLM assistance.

## Overview

This wiki follows the **LLM Wiki pattern**: raw sources remain immutable, while the LLM incrementally builds and maintains a structured, interlinked collection of markdown files. The human curates sources and asks questions; the LLM handles summarizing, cross-referencing, and maintenance.

## Directory Structure

```
radiology-wiki/
│
├── raw/                              # Immutable source materials
│   ├── textbooks/                    # PDF textbooks
│   ├── papers/                       # Research papers
│   ├── lectures/                     # Lecture PDFs (converted from slides)
│   └── notes/                        # Existing notes to be processed
│
├── wiki/                             # LLM-maintained knowledge base
│   ├── index.md                      # Master index of all pages
│   ├── log.md                        # Chronological operation log
│   │
│   ├── anatomy/                      # Anatomical structures
│   │   ├── shoulder/
│   │   ├── wrist/
│   │   ├── elbow/
│   │   ├── knee/
│   │   ├── ankle/
│   │   ├── hip/
│   │   └── spine/
│   │
│   ├── pathology/                    # Diseases and conditions
│   │   ├── shoulder/
│   │   ├── wrist/
│   │   ├── elbow/
│   │   ├── knee/
│   │   ├── ankle/
│   │   ├── hip/
│   │   └── spine/
│   │
│   ├── classification/               # Classification systems
│   │
│   ├── syndrome/                     # Clinical syndromes
│   │
│   ├── imaging/                      # Imaging protocols and techniques
│   │
│   ├── differential/                 # Differential diagnosis lists
│   │
│   └── sources/                      # Source summaries
│
├── exports/                          # Generated HTML/PDF outputs
│
└── CLAUDE.md                         # This file
```

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

### Pathology Page (`wiki/pathology/`)

```markdown
# [Condition Name]

## Definition
[Brief definition]

## Mechanism / Etiology
- [Cause 1]
- [Cause 2]

## Classification
[If applicable, or link to classification page]
| Type | Description |
|------|-------------|
| I    | ...         |
| II   | ...         |

## MRI Findings
- [Finding 1]
- [Finding 2]

## Associated Conditions
- [[condition-1]] (percentage if known)
- [[condition-2]]

## Differential Diagnosis
- [[ddx-1]]
- [[ddx-2]]

## Pitfalls
- [Common mistake 1]
- [Normal variant that mimics this]

## Key Points
- [Most important takeaway 1]
- [Most important takeaway 2]

## References
- Author et al. Journal. Year;Volume:Pages.
```

### Classification Page (`wiki/classification/`)

```markdown
# [Classification Name]

## Overview
[What it classifies, why it matters]

## Original Reference
Author et al. Journal. Year;Volume:Pages.

## Classification Table

| Grade/Type | Criteria | Clinical Significance |
|------------|----------|----------------------|
| 0 / I      | ...      | ...                  |
| 1 / II     | ...      | ...                  |

## MRI Criteria
[Specific imaging criteria for each grade]

## Clinical Application
- [When to use this classification]
- [Treatment implications]

## Pitfalls
- [Common grading errors]

## Related Classifications
- [[related-classification]]

## References
- Original paper
- Validation studies
```

### Anatomy Page (`wiki/anatomy/`)

```markdown
# [Structure Name]

## Anatomy
- **Origin**: 
- **Insertion**: 
- **Innervation**: 
- **Blood supply**: 

## Function
[Biomechanical role]

## MRI Appearance
- **T1**: 
- **T2/PD FS**: 
- **Best plane**: 

## Normal Variants
- [Variant 1]
- [Variant 2]

## Common Pathology
- [[pathology-1]]
- [[pathology-2]]

## Imaging Pitfalls
- [Structure that mimics pathology]
- [Magic angle effect, etc.]

## References
```

### Syndrome Page (`wiki/syndrome/`)

```markdown
# [Syndrome Name]

## Definition
[What defines this syndrome]

## Pathophysiology
[Mechanism, biomechanics]

## Components
1. [[component-1]]
2. [[component-2]]
3. [[component-3]]

## Clinical Presentation
- [Symptom 1]
- [Symptom 2]

## MRI Findings
| Structure | Finding |
|-----------|---------|
| ...       | ...     |

## Phases / Stages
[If applicable]

## Treatment Implications
[Brief overview]

## References
```

### Imaging Protocol Page (`wiki/imaging/`)

```markdown
# [Body Part] MRI Protocol

## Coil
- [Coil type]

## Patient Position
- [Position details]

## Sequences

### Conventional MRI
| Sequence | Plane | Purpose |
|----------|-------|---------|
| T1       | ...   | ...     |
| T2 FS    | ...   | ...     |

### MR Arthrography
| Sequence | Plane | Purpose |
|----------|-------|---------|
| T1 FS    | ...   | ...     |

## Key Structures to Evaluate
- [ ] Structure 1
- [ ] Structure 2

## Common Pitfalls
- [Pitfall 1]

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
