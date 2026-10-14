# AACL Workshop Materials Example

Use this directory to organize your conference information, preface, committee lists, invited talks, and papers, then commit them to a Git repository and share it with us. See the [Notion How-to](https://lateral-option-e4c.notion.site/AACL-Workshop-Proceedings-3f7ae63d82b280a2b8bcd1dc9dbe6d8c?source=copy_link) for material requirements and submission instructions.

All conference names, people, papers, and schedules here are examples. The two PDFs demonstrate how files correspond to paper records. Prepare your final PDFs using the camera-ready formatting requirements for your workshop.

```text
aacl-example/
├── conference_details.yml       # Conference information
├── organizing_committee.yml     # Organizing committee, using members
├── program_committee.yml        # Program committee and reviewers, using entries
├── prefaces.yml                 # Preface file index
├── prefaces/
│   └── introduction.tex         # Preface text
├── invited_talks.yml            # Invited speaker and talk details, optional
├── invited_talks/
│   ├── dana_chen_abstract.tex    # Talk abstract, body text only
│   └── dana_chen_bio.tex         # Speaker biography, body text only
├── papers.yml                  # Paper metadata
├── papers/
│   ├── 1.pdf
│   ├── 1.tex                   # Sample PDF source; remove before submission
│   ├── 20.pdf
│   └── 20.tex                  # Sample PDF source; remove before submission
├── program.yml                 # Schedule, optional
├── sponsors.yml                # Sponsor tiers and logo filenames, optional
└── sponsor_logos/
    └── rasa.jpg                # Example sponsor logo
```

In `papers.yml`, ID 1 is an example of a regular submission, and ID 20 is an example of a paper from another source that has been renumbered. When merging exports from different venues, update the IDs, PDF filenames, and schedule references together. ID 3 is marked `archival: false`: its full text is excluded from the proceedings, and no PDF is required.

The invited talk example includes a fictional speaker in `invited_talks.yml`, an abstract and biography in `invited_talks/`, and a matching standalone session in `program.yml`. Replace the speaker name, institution, talk title, date, time, location, and both `.tex` files. Abstracts and biographies should contain body text only, without `\documentclass`, `\begin{document}`, or `\end{document}`. Paths in `abstract_file`, `bio_file`, and the optional `photo` field are relative to `invited_talks/`. To include a photo, place the image in that directory and set `photo` to its filename. Add one YAML entry per talk, with separate files for each speaker. `custom_prefix: Invited Talk` sets the heading on the talk page. Keep any matching `program.yml` session consistent; it is not created automatically from `invited_talks.yml`. For a workshop without invited talks, set `invited_talks.yml` to `[]` or omit it, remove `invited_talks/`, and remove the sample invited talk session from `program.yml`.

The sponsor example includes a Gold tier in `sponsors.yml` and a JPG logo at `sponsor_logos/rasa.jpg`. Replace the example tier and logo with your workshop's sponsors, keeping the filenames in `logos` consistent with the files in `sponsor_logos/`. For a workshop without sponsors, set `sponsors.yml` to `[]` or omit it, and remove `sponsor_logos/`.

Copy this directory, rename it with your workshop acronym, and replace the example content with your own information and final PDFs. Leave the ISBN blank if it has not yet been assigned. Omit the schedule file if it does not apply. If you have attachments, create an `attachments/` directory and reference them in the paper records. Finally, check the materials against the How-to, commit and push the complete workshop folder, and share the repository URL with us. Identify the branch and workshop folder to use, and grant access if the repository is private.
