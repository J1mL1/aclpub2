#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------
# Created By Rodrigo Wilkens
# Last update 02/April/2022
# version ='1.0'
# ---------------------------------------------------------------------------

import argparse
import getpass
import os
import sys

import openreview
import openreview.api
import yaml
from tqdm import tqdm
from util import (
    collect_author_fallbacks,
    collect_author_ids,
    get_content_from,
    get_decision_label,
    get_user,
)


def _resolve_authors(submission, client, log_fh):
    """Build author list: prefer profiles via IDs, else structured authors[] fallback."""
    authorsids = collect_author_ids(submission)
    authors = []
    for authorsid in authorsids:
        author, error = get_user(authorsid, client)
        if error:
            log_fh.write(
                "Error at "
                + str(authorsid)
                + " from (#"
                + str(submission.number)
                + "; openreview ID: "
                + submission.id
                + ") "
                + str(get_content_from(submission, "title"))
                + "\n"
            )
        if author:
            # Align with common aclpub2 examples.
            if "emails" in author and "email" not in author and author["emails"]:
                author["email"] = author["emails"]
            if "username" in author and "openreview" not in author:
                author["openreview"] = author["username"]
            authors.append(author)

    if authors:
        return authors

    fallbacks = collect_author_fallbacks(submission)
    if fallbacks:
        # If we have usernames in fallbacks, try profiles once more.
        resolved = []
        for fb in fallbacks:
            uid = fb.get("username") or fb.get("openreview")
            if uid and str(uid).startswith("~"):
                author, error = get_user(uid, client)
                if not error and author:
                    if "emails" in author and "email" not in author and author["emails"]:
                        author["email"] = author["emails"]
                    if "username" in author and "openreview" not in author:
                        author["openreview"] = author["username"]
                    resolved.append(author)
                    continue
            resolved.append(fb)
        msg = (
            f"Paper #{submission.number} ({submission.id}): "
            f"used authors[] fallback (authorids missing/hidden or profile lookup failed).\n"
        )
        print(msg.strip())
        log_fh.write(msg)
        return resolved

    return []


def main(username, password, venue, download_all, download_pdfs):
    try:
        client_acl_v2 = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net", username=username, password=password
        )
    except Exception as e:
        print(f"OpenReview connection refused\n{e}")
        sys.exit(1)

    try:
        client_acl_v2.get_group(venue)
    except Exception as e:
        print(f"Unable to get group for: {venue}\nSee below for the OpenReview API error")
        print(f"Exception: {e}")
        sys.exit(1)

    if not download_all or not download_pdfs:
        print("The output of this run cannot be used at ACLPUB2 (pass --all --pdfs).")

    attachment_types = {"software": "software", "data": "data", "copyright_PDF": "copyright"}

    papers_folder = "papers"
    attachments_folder = "attachments"
    if not os.path.exists(papers_folder):
        os.mkdir(papers_folder)
    if not os.path.exists(attachments_folder):
        os.mkdir(attachments_folder)

    submissions = client_acl_v2.get_all_notes(content={"venueid": venue}, details="replies")
    if len(submissions) <= 0:
        print(
            "No submissions found. Please double check your venue ID and/or permissions "
            "to view the submissions (Accepted Submission Release may not have run yet)."
        )
        sys.exit(1)

    ## Publication chairs do not have access to the forum replies - use venueid instead
    if not submissions[0].details or len(submissions[0].details.get("replies") or []) <= 0:
        decision_by_forum = {
            s.forum: s
            for s in submissions
            if s.content.get("venueid", {}).get("value") == venue
        }
    else:
        decision_by_forum = {
            r["forum"]: r
            for s in submissions
            for r in s.details["replies"]
            if any(i.endswith("Decision") for i in r["invitations"])
            if "accept" in r["content"]["decision"]["value"].lower()
        }

    papers = []
    abstract_flag, paper_type_flag, track_flag = False, False, False
    small_log = open("papers.log", "w")
    for submission in tqdm(submissions):
        if submission.id not in decision_by_forum:
            continue

        authors = _resolve_authors(submission, client_acl_v2, small_log)
        if len(authors) == 0:
            raise AssertionError(
                f"Paper #{submission.number} ({submission.id}) "
                f"'{get_content_from(submission, 'title')}' has no readable "
                f"authorids/authors. Release author identities in "
                f"Accepted Submission Release, or fill authors manually."
            )

        if "abstract" in submission.content:
            abstract = get_content_from(submission, "abstract")
        else:
            abstract = ""
            if not abstract_flag:
                abstract_flag = True
                print(
                    f"Paper {submission.id} abstract field is not present. "
                    f"Contact info@openreview.net if you need this information migrated from ARR"
                )

        decision_note = decision_by_forum.get(submission.id)
        # When decision_by_forum stores the submission itself (no replies), skip note parsing.
        if decision_note is submission:
            decision_note = None

        pdf_path = get_content_from(submission, "pdf") or ""
        paper = {
            "id": submission.number,
            "title": get_content_from(submission, "title"),
            "authors": authors,
            "abstract": abstract,
            "file": str(submission.number) + ".pdf",
            "pdf_file": str(pdf_path).split("/")[-1] if pdf_path else "",
            "decision": get_decision_label(submission, decision_note),
            "openreview_id": submission.id,
        }

        submitted_area = get_content_from(submission, "track")
        if "track" not in submission.content and not track_flag:
            track_flag = True
            print(
                f"Paper {submission.id} track field is not present. "
                f"Contact info@openreview.net if you need this information migrated from ARR"
            )

        if "paper_type" in submission.content:
            paper_type = " ".join(get_content_from(submission, "paper_type").split()[:2]).lower()
        else:
            paper_type = "N/A"
            if not paper_type_flag:
                paper_type_flag = True
                print(
                    "paper_type field (long or short) is not present. "
                    "Contact info@openreview.net if you need this information migrated from ARR"
                )
        presentation_type = "N/A"
        paper["attributes"] = {
            "submitted_area": submitted_area,
            "paper_type": paper_type,
            "presentation_type": presentation_type,
        }
        attachments = []

        attachments_count = 0
        suffix = ""

        for att_type in attachment_types:
            if att_type in submission.content and submission.content[att_type]:
                if attachments_count == 0:
                    suffix = ""
                else:
                    suffix = "_" + str(attachments_count)

                attachments.append(
                    {
                        "type": attachment_types[att_type],
                        "file": str(paper["id"])
                        + suffix
                        + "."
                        + str(get_content_from(submission, att_type).split(".")[-1]),
                        "open_review_id": str(get_content_from(submission, att_type)),
                    }
                )
                if download_all:
                    file_tye = get_content_from(submission, att_type).split(".")[-1]
                    f = client_acl_v2.get_attachment(submission.id, att_type)
                    with open(
                        os.path.join(
                            attachments_folder, str(paper["id"]) + suffix + "." + file_tye
                        ),
                        "wb",
                    ) as op:
                        op.write(f)
                attachments_count = attachments_count + 1
        if download_pdfs:
            try:
                f = client_acl_v2.get_pdf(id=paper["openreview_id"])
                with open(
                    os.path.join(papers_folder, str(paper["id"]) + ".pdf"), "wb"
                ) as op:
                    op.write(f)
            except Exception:
                print(f"Unable to download PDF for {paper['openreview_id']}")

        if len(attachments) > 0:
            paper["attachments"] = attachments

        papers.append(paper)

    small_log.close()

    papers.sort(key=lambda p: p["id"])
    with open("papers.yml", "w", encoding="utf-8") as out:
        yaml.dump(papers, out, allow_unicode=True)
    print(f"Wrote {len(papers)} papers to papers.yml")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch papers from an OpenReview venue. Password is always read via getpass."
    )
    parser.add_argument(
        "-u",
        "--username",
        help="OpenReview email (prompted if omitted).",
    )
    parser.add_argument(
        "-v",
        "--venue",
        help="OpenReview venue ID, found in https://openreview.net/group?id=<VENUE ID>",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="If set, downloads all attachments in the OpenReview venue.",
    )
    parser.add_argument(
        "--pdfs",
        action="store_true",
        help="If set, downloads PDFs.",
    )
    args = parser.parse_args()

    username = (args.username or input("OpenReview email: ")).strip()
    password = getpass.getpass("OpenReview password: ")
    venue = (args.venue or input("Venue ID: ")).strip()
    if not venue:
        print("Venue ID is required.", file=sys.stderr)
        sys.exit(1)

    main(username, password, venue, args.all, args.pdfs)
