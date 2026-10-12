#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------
# Created By Rodrigo Wilkens
# Last update 02/April/2022
# version ='1.0'
# ---------------------------------------------------------------------------

import argparse
import getpass
import sys

import openreview
import openreview.api
import yaml
from util import get_user

use_tracks = True


def sort_role(t):
    return t["role"]


def sort_user(t):
    return t["last_name"]


def extract_or_data(client_acl, all_groups, acl_name, role="Senior_Area_Chairs", or2acl=None):
    or2acl = or2acl or {}
    lst = []
    ## Groups will either look like venue_id/role or venue_id/track/role
    # Match exact role segment only (skip .../Reviewers/Invited, Declined, etc.).
    matched = []
    for g in all_groups:
        parts = g.id.split("/")
        if role not in parts:
            continue
        # Role must be the last path segment of the committee group.
        if parts[-1] != role:
            continue
        matched.append(g)

    for group in matched:
        track = group.id.replace(acl_name, "").replace(role, "").strip("/")
        if len(track) > 0:
            or_track_name = f"{track}_{role}"
        else:
            or_track_name = role
        if or_track_name in or2acl:
            or_track_name = or2acl[or_track_name]
        t = {"role": or_track_name.replace("_", " "), "entries": []}

        lst.append(t)
        for member in group.members:
            user, error = get_user(member, client_acl)
            if error:
                print(
                    f"Warning: skip {member} in {group.id} "
                    f"(no resolvable OpenReview profile; fix membership to ~id or edit yml manually)"
                )
                continue
            t["entries"].append(user)
        t["entries"].sort(key=sort_user)
    lst.sort(key=sort_role)
    return lst


def get_committee(client_acl, acl_name):
    if acl_name[-1] != "/":
        acl_name += "/"
    committees = []
    for group in openreview.tools.iterget_groups(client_acl, regex=acl_name):
        if acl_name + "Paper" in group.id or "Program_Chairs" in group.id or "Conflicts" in group.id:
            continue
        name = group.id.replace(acl_name, "")
        if name.startswith("Authors"):
            continue
        if len(name.split("/")) > 1:
            continue
        committees.append(group.id)
    return committees


def main(username, password, acl_name):
    try:
        client_acl = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net",
            username=username,
            password=password,
        )
    except Exception as e:
        print(f"OpenReview connection refused\n{e}")
        sys.exit(1)

    acl_name = acl_name.strip("/")

    try:
        venue_group = client_acl.get_group(acl_name)
        in_v2 = venue_group.domain is not None and venue_group.domain == venue_group.id
    except Exception:
        print(f"{acl_name} not found")
        sys.exit(1)

    # Fetch all groups and filter out the paper/submission groups
    all_groups = client_acl.get_all_groups(prefix=f"{acl_name}/.*")
    if not in_v2:
        all_groups = [g for g in all_groups if "Paper" not in g.id]
    else:
        all_groups = [g for g in all_groups if "Submission" not in g.id]

    or2acl = {}
    program_committee = []
    program_committee.extend(extract_or_data(client_acl, all_groups, acl_name, role="Program_Chairs"))
    program_committee.extend(
        extract_or_data(client_acl, all_groups, acl_name, role="Senior_Area_Chairs", or2acl=or2acl)
    )
    program_committee.extend(
        extract_or_data(client_acl, all_groups, acl_name, role="Area_Chairs", or2acl=or2acl)
    )
    program_committee.extend(
        extract_or_data(client_acl, all_groups, acl_name, role="Reviewers", or2acl=or2acl)
    )

    # Drop empty roles (common for flat workshop setups).
    program_committee = [r for r in program_committee if r.get("entries")]

    # Match aclpub2 examples/sigdial/program_committee.yml field set and shape.
    keep = ("first_name", "middle_name", "last_name", "institution")

    def clean_entry(entry):
        return {k: entry[k] for k in keep if entry.get(k) not in (None, "")}

    cleaned = []
    for block in program_committee:
        entries = [clean_entry(e) for e in block["entries"]]
        entries = [e for e in entries if "first_name" in e and "last_name" in e]
        entries.sort(
            key=lambda e: (e.get("last_name", "").lower(), e.get("first_name", "").lower())
        )
        if not entries:
            continue
        # sigdial order: entries then role
        cleaned.append({"entries": entries, "role": block["role"]})

    with open("program_committee.yml", "w", encoding="utf-8") as out:
        yaml.dump(cleaned, out, allow_unicode=True, sort_keys=False)
    print(f"Wrote {len(cleaned)} role block(s) to program_committee.yml")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch program committee from an OpenReview venue."
    )
    parser.add_argument(
        "-u",
        "--username",
        help="OpenReview email (prompted if omitted).",
    )
    parser.add_argument(
        "-v",
        "--venue",
        help="OpenReview venue ID (prompted if omitted).",
    )
    args = parser.parse_args()

    username = (args.username or input("OpenReview email: ")).strip()
    password = getpass.getpass("OpenReview password: ")
    venue = (args.venue or input("Venue ID: ")).strip()
    if not venue:
        print("Venue ID is required.", file=sys.stderr)
        sys.exit(1)

    main(username, password, venue)
