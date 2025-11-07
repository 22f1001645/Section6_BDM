# SECTION_6_MASTER_FOLDER — Results & Findings

This folder mirrors the Section 5 master structure and serves as the authoritative, organized hub for all Section 6 assets. It maintains parity in directory structure, naming conventions, organization logic, and backup discipline.

## Structure
- `1_DATA_SOURCES/` — Raw and derived CSVs powering Section 6 analyses.
- `2_SCRIPTS/` — All generation and export scripts (charting, PDF, packaging).
- `3_VISUALS/` — Final charts and image assets for Section 6.
- `4_TEMPLATES_AND_GUIDES/` — Style guides, section guides, and integration aids.
- `5_RELATED_SECTIONS/` — Cross-references to adjacent sections (e.g., Section 5).
- `6_WORKING_DRAFTS/` — Drafts, execution maps, and kits used during production.
- `7_QA_AND_VERIFICATION/` — QA checklists, verification tables, and test artifacts.
- `8_EXPORTS_AND_OUTPUTS/` — Final HTML/PDF outputs and deliverable packages.
- `INDEX.md` — Entry point index with asset map and versioning.

## Naming Convention
- Folders are numbered and UPPER_SNAKE_CASE, mirroring Section 5.
- Files use `Section6_*` or `Figure_6_*` prefixes with descriptive suffixes.
- Data files retain original names and locations captured in `INDEX.md` manifest.

## Version & Metadata
- Maintained in `INDEX.md` (version tag, generation timestamp, script provenance).
- Packaging zip backups created under `dist/` with timestamped names.

## Permissions & Backup
- Folders inherit workspace read/write permissions; parity with Section 5.
- A compressed backup zip of this master folder is created in `dist/`.

## Contact
For any changes, update `INDEX.md` and re-run packaging to keep parity.