---
name: check-proceedings
description: Review an aclpub2 conference or workshop submission folder before delivery. Check YAML, paper PDFs and metadata, committees, prefaces, invited talks, schedules, and attachment references; report specific errors and distinguish generation blockers from publication and delivery issues.
---

# Check proceedings before submission

Review the organizer's input folder and produce an actionable report. This skill uses ordinary file reading, YAML parsing, PDF inspection, and optional local compilation; it does not require a particular agent harness, connector, or proprietary tool. It can be followed by Codex, Claude Code, Cursor, or another coding assistant that can read the files.

## Scope and source of truth

- Use the folder named by the organizer. If several versions exist, identify the intended submission before making a readiness judgment. Report the reviewed path and, when available, repository revision.
- Review without changing submission files unless the user asks for repairs. Do not commit, push, upload, or contact authors as part of a review.
- Read the repository's [README](../../README.md), [AACL example guide](../../aacl-example/README.md), and relevant example YAML. Use the organizer's explicit requirements and current venue instructions for publication requirements; use the checked-out loader, generator, and templates for actual software behavior. If these disagree, explain the discrepancy instead of silently imposing one interpretation.
- If this skill was copied without the repository, locate the corresponding aclpub2 checkout or supplied documentation. Explain any checks that cannot be verified without it.
- Treat the designated final PDFs as the comparison reference for paper titles, author order, spelling, and displayed affiliations. Follow any explicit organizer decision about metadata precedence. Report disagreements; do not infer a person's surname or current affiliation from their name or email, and do not silently rewrite metadata.
- Inspect only relevant submission material. Do not reproduce credentials, tokens, or unrelated personal data in the report.

## Review the input package

Continue independent checks after a failure so that one malformed file does not conceal other issues. Keep unavailable or unreadable files separate from files confirmed absent; cloud placeholders and read timeouts are not proof of missing content.

### 1. YAML and conference information

- Check that the expected conference details, paper records, preface, and committee materials are present for the venue. Distinguish a submission requirement from a file the generator technically requires. Sponsors, invited talks, panels, and a proceedings schedule are optional when not applicable. A full handbook has different requirements.
- Decode YAML as UTF-8 and parse it safely, with duplicate-key detection. Report the exact file and line/column for syntax errors. If decoding fails, report the byte location and any diagnostically supported encoding; do not discard undecodable characters or claim that parsing the alternative encoding fixes the original file.
- Validate collection shapes, required fields, and value types against the local code and examples. Check empty required values as well as missing keys. Examples of consequential errors include an unquoted colon followed by a space in a title, a quoted `"false"` used for `archival`, and string dates where the generator expects date/datetime objects.
- Check conference name, acronym, dates, location, publisher, editors, and volume information for internal consistency and unreplaced sample content. Do not assume every workshop uses the example date or location.
- For AACL materials, an ISBN awaiting assignment may remain blank as allowed by the example guide; report it as pending, not as an unconditional submission blocker. If supplied, check its syntax and checksum. A valid checksum does not verify official assignment. Never invent an ISBN.

### 2. Paper records and PDFs

- Count all records, archival records, and non-archival records separately. In this generator, omitted `archival` means true; `archival: false` excludes the paper from the proceedings text and author index and does not require a PDF. Do not equate the number of accepted presentations with the number of included PDFs.
- Check unique paper IDs across merged submission sources, consistent ID types in references, and file references relative to `papers/`. Original OpenReview or ARR numbers can repeat across sources; the merged paper IDs must be unique. IDs need not be consecutive, and filenames need not equal IDs if explicit references resolve correctly.
- Check every referenced archival PDF for existence, readability, nonzero pages, and encryption or corruption that prevents processing. Identify unreferenced PDFs and shared file references for review; do not delete them automatically.
- Compare every archival PDF's first-page title and author list against metadata, preserving author order, diacritics, and meaningful punctuation. Compare affiliations where supplied and identify missing metadata affiliations separately from contradictory ones. Ignore extraction-only whitespace, line wrapping, and ligature artifacts. Visually inspect uncertain cases before reporting them as confirmed errors.
- Report a potential first-name/last-name inversion with both values and evidence; cultural name conventions alone do not establish an error. Do not alphabetize paper authors. Preserve the organizer's paper order unless another ordering is explicitly requested.
- Look for anonymous submission text, review line numbers, obvious draft placeholders, and page size or layout problems. Use the venue's actual camera-ready requirements for page limits and formatting. Text extraction alone cannot establish margin or visual compliance. Run ACLPUBCHECK when available and relevant, and distinguish its findings from manual inspection. State when layout checking was not performed.

### 3. Preface, committees, and optional front matter

- Resolve preface file references relative to `prefaces/`. Preface, invited-talk abstract, and biography `.tex` files should be body fragments, without their own document class or document environment.
- Reconcile preface counts and names with the records: accepted versus archival papers, submission categories, committee members, and invited speakers. State which claims, such as total submissions received, lack an independent source rather than calling them false.
- Check organizing committee `members` and program committee `entries` against the local schema. Report missing names or affiliations, accidental duplication within a role, and inconsistent spelling. Membership in both OC and PC is not inherently an error. Do not invent affiliations or impose alphabetical ordering unless required.
- If invited talks are provided, check speaker names, titles, institutions, and all declared abstract, biography, and photo paths relative to `invited_talks/`. Verify dates, times, and locations against any matching schedule entries. An invited-talk record does not automatically create a program session. Omitted optional photos or talks are not missing required material.
- Resolve sponsor logos relative to `sponsor_logos/`; inspect panels and additional pages only when present or required. Derive their path conventions from the current templates.
- Trace special characters through the actual loader and templates before suggesting escaping. Some fields are escaped automatically and others are inserted directly into LaTeX. Do not blindly replace every `&` with `\&` or strip Unicode. Attribute a loader or template defect to the software, with evidence, rather than presenting it as incorrect organizer content.

### 4. Schedule, when provided

- Check parseable date/time values, start before end, conference dates, parent/subsession boundaries, and paper references. Flag unintended same-track overlaps; parallel sessions are not necessarily errors.
- Verify that referenced IDs exist with matching types. In the current proceedings template, paper links use proceedings page numbers. Non-archival presentations have no such page numbers and should use standalone session entries as demonstrated in the example, unless the local implementation supports another form.
- Report discrepancies between scheduled talk information and `invited_talks.yml`. Do not require a schedule for an AACL workshop that does not provide one.

### 5. Attachments and delivery

- Resolve every attachment `file` relative to `attachments/`, retaining subdirectories and filename case. For example, `file: source files/2.zip` refers to `attachments/source files/2.zip`. If source and supplementary ZIPs have the same basename in different directories, preserve that distinction.
- Check referenced files and ZIP integrity when feasible. Inspect archive listings without executing bundled code or compiling paper sources. Source ZIPs are not needed to merge the supplied camera-ready PDFs.
- **Attachments are copied separately into the output package; they are not compiled or appended to `proceedings.pdf`, including attachments that are PDFs.** An appendix already inside a paper PDF is included with that paper.
- A broken attachment reference is a delivery/association issue, not by itself a proceedings PDF compilation blocker in the current generator. Distinguish an existing file with a wrong reference from a genuinely missing file. Verify software behavior before claiming a different impact in another version.

## Optional generation check

Use static checks first. If a generation check is useful and dependencies are available, follow the checked-out CLI instructions in an isolated temporary working directory with an isolated output path. The generator can delete existing build/output directories; never run it against the organizer's existing output as a casual check. Avoid interactive prompts hanging the review.

Use the submitted inputs unchanged for a definitive build result. A diagnostic build from a repaired temporary copy only establishes what happens after those stated corrections. Inspect the log and output, not just the command exit code, because subprocess failures may not propagate reliably. Check the front matter, contents, paper order, page ranges, author index, and watermarks in any generated PDF. Do not claim compilation or full visual validation if it was not performed. Missing local dependencies are an environment limitation, not an organizer file error.

## Report concrete findings

Start with separate judgments about **PDF generation** and **submission-package readiness**, limited to the checks actually performed. Use these impact categories, omitting empty ones:

- **Generation blocker:** a demonstrated parse, file-loading, rendering, or compilation failure. Identify whether it comes from the input or the local toolchain.
- **Publication/content correction:** incorrect or conflicting published information, such as author names, ordering, affiliations, or counts; it may compile successfully.
- **Delivery/reference issue:** broken attachment associations or incomplete handoff materials that do not prevent PDF compilation.
- **Needs confirmation / optional improvement:** unresolved source conflicts, pending information, or recommendations that are not established requirements.

For each finding provide the relative file path and line number when available, paper ID or person, exact observed value, comparison evidence, practical consequence, and a specific proposed correction. Use PDF page numbers for PDF evidence. Group repeated issues, but enumerate affected IDs or filenames so organizers can fix every occurrence. Show a minimal corrected YAML snippet when useful, without presenting invented publication facts as final values.

Close with a short coverage statement: records and PDFs checked, attachments checked, what passed, and checks skipped or blocked. Clearly separate a suspected issue from a verified error. Do not label the package fully ready based solely on successful YAML parsing or the presence of PDFs. If repairs were requested, apply only supported changes, synchronize directly affected references, and rerun the affected checks.
