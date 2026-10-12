#!/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Created By Rodrigo Wilkens
# Last update 27/March/2022
# version ='1.0'
# ---------------------------------------------------------------------------

def join_institution(institution):
    if len(institution)==0:
        return None
    if len(institution)==1:
        return institution[0]
    res = ", ".join(institution[:-1])
    res += " and " + institution[-1]
    return res


def _resolve_profile(or_id, client_acl):
    """Resolve a ~id or email to an OpenReview Profile.

    Note: api2 recently rejects profiles/search POSTs that only send ``emails``
    (MissingRequiredError on ``ids``). Prefer get_profile / term / ids search.
    Returns None if no real profile can be resolved (no email stub profiles).
    """
    or_id = str(or_id).strip()
    if not or_id:
        return None

    # Preferred: tilde profile id
    if or_id.startswith("~"):
        try:
            return client_acl.get_profile(or_id)
        except Exception:
            try:
                profiles = client_acl.search_profiles(ids=[or_id])
                if profiles:
                    return profiles[0]
            except Exception:
                pass
            return None

    # Committee groups often store members as emails, not ~ids.
    if "@" in or_id:
        email = or_id.lower()
        # GET /profiles?email=...
        try:
            return client_acl.get_profile(email)
        except Exception:
            pass
        # GET /profiles/search?term=...
        try:
            profiles = client_acl.search_profiles(term=email)
            if profiles:
                return profiles[0]
        except Exception:
            pass
        # Do NOT call search_profiles(emails=...) — current api2 requires ids.
        # Do NOT invent stub profiles from the email address.
        return None

    try:
        return client_acl.get_profile(or_id)
    except Exception:
        return None


def get_user(or_id,client_acl, force_institution=False):
    c = _resolve_profile(or_id, client_acl)
    if c is None:
        print("\nERROR: or_id not found", or_id)
        return {"first_name":or_id, "last_name":or_id,"name":or_id, "username":or_id, "emails":or_id, "institution":"NA"}, True
    # Best-effort email string for aclpub2 (may be masked as ****@domain by OpenReview).
    email_str = str(or_id) if "@" in str(or_id) else ""
    try:
        content0 = getattr(c, "content", None) or {}
        if "preferredEmail" in content0:
            email_str = content0["preferredEmail"]
        elif content0.get("emails"):
            email_str = content0["emails"][0]
        profile_id = getattr(c, "id", None)
        if (not email_str or "****" in str(email_str)) and profile_id and str(profile_id).startswith("~"):
            email_profiles = client_acl.search_profiles(ids=[profile_id])
            if email_profiles:
                content0 = email_profiles[0].content
                if "preferredEmail" in content0:
                    email_str = content0["preferredEmail"]
                elif content0.get("emails"):
                    email_str = content0["emails"][0]
    except Exception:
        pass
    if not email_str:
        email_str = str(or_id)
    email_str = str(email_str).replace("_", "\\_")

    profile_id = getattr(c, "id", None) or or_id
    c = c.content
    namePrefered = None
    for name in c.get("names") or []:
        if namePrefered is None or ("preferred" in name and name["preferred"]):
            namePrefered = name
    if namePrefered is None:
        print("\nERROR: profile has no names", or_id)
        return {
            "first_name": or_id,
            "last_name": or_id,
            "name": or_id,
            "username": or_id,
            "emails": email_str,
            "email": email_str,
            "institution": "NA",
        }, True
    if "first" in namePrefered:
        name = " ".join(
            filter(
                None,
                [
                    namePrefered.get("first", ""),
                    namePrefered.get("middle", ""),
                    namePrefered.get("last", ""),
                ],
            )
        ).replace("  ", " ")
        first_name = namePrefered.get("first", "")
        middle_name = namePrefered.get("middle", "")
        if middle_name is None:
            middle_name = ""
        last_name = namePrefered.get("last", "")
    else:  ## first/middle/last may be absent; OpenReview may only provide fullname
        name = namePrefered["fullname"]
        try:
            assert "@" not in name, name
        except AssertionError:
            print("\nERROR: name looks like email address:", name, "for OR user", or_id)

        # if full name has no spaces, try to insert some based on capitalization/periods
        if " " not in name:
            name2 = ""
            for ch in name:
                if ch.isupper() and name2 and (name2[-1].islower() or name2[-1] == "."):
                    name2 += " "  # insert a space
                name2 += ch
            name = name2
        first_name = name.split(" ")[0] if " " in name else ""
        if name.count(" ") > 1 and name.split(" ")[-1].lower() in ("ii", "iii", "iv", "jr", "jr."):
            last_name = " ".join(name.split(" ")[-2:])
            middle_name = " ".join(name.split(" ")[1:-2])
        else:
            last_name = name.split(" ")[-1]
            middle_name = " ".join(name.split(" ")[1:-1])

        # move common surname prefixes from the middle name to the last name
        if middle_name.lower() in (
            "al",
            "da",
            "de",
            "de la",
            "del",
            "dela",
            "della",
            "dos",
            "di",
            "el",
            "van",
            "van den",
            "van der",
            "von",
            "von der",
        ):
            last_name = middle_name + " " + last_name
            middle_name = ""
        elif middle_name.lower().endswith((" van den", " van der", " von der")):
            last_name = middle_name[-7:] + " " + last_name
            middle_name = middle_name[:-8]
        elif middle_name.lower().endswith((" de la", " della")):
            last_name = middle_name[-5:] + " " + last_name
            middle_name = middle_name[:-6]
        elif middle_name.lower().endswith((" dela",)):
            last_name = middle_name[-4:] + " " + last_name
            middle_name = middle_name[:-5]
        elif middle_name.lower().endswith((" del", " dos", " van", " von")):
            last_name = middle_name[-3:] + " " + last_name
            middle_name = middle_name[:-4]
        elif middle_name.lower().endswith((" al", " da", " de", " di", " el")):
            last_name = middle_name[-2:] + " " + last_name
            middle_name = middle_name[:-3]

    username = namePrefered.get("username") or profile_id or or_id
    if isinstance(username, str):
        username = username.strip()
    else:
        username = str(or_id)

    # Normalize capitalization when a token is all-upper or all-lower
    if len(first_name) > 2:
        first_name = " ".join(
            [n.title() if (n == n.upper() or n == n.lower()) else n for n in first_name.split(" ")]
        )
    if len(middle_name) > 2:
        middle_name = " ".join(
            [n.title() if (n == n.upper() or n == n.lower()) else n for n in middle_name.split(" ")]
        )
    if len(last_name) > 2:
        if all(n.isupper() or n.islower() for n in last_name.split(" ")):
            last_name = last_name.title()

    institution = []
    if "history" in c:
        for h in c["history"]:
            if "end" not in h or h["end"] is None:
                institution.append(h["institution"]["name"])
    ret = {
        "first_name": first_name,
        "last_name": last_name,
        "name": name,
        "username": username,
        "emails": email_str,
        "email": email_str,
        "openreview": username,
    }
    institution = join_institution(institution)
    if institution:
        ret["institution"] = institution
    else:
        if force_institution:
            ret["institution"] = "NA"
    if len(middle_name) > 0:
        ret["middle_name"] = middle_name
    if "gscholar" in c:
        ret["google_scholar_id"] = c["gscholar"]
    if "dblp" in c:
        ret["dblp_id"] = c["dblp"]
    if "homepage" in c:
        ret["homepage"] = c["homepage"]
    if "orcid" in c:
        ret["orcid"] = c["orcid"]
    if "semanticScholar" in c:
        ret["semantic_scholar_id"] = c["semanticScholar"]
    return ret, False

def get_content_from (submission, content_field):
    # Given a paper from OpenReview (either openreview.Note or openreview.api.Note) and a field,
    # get its value or None if value does not exist 
    try:
        if isinstance(submission, dict):
            content = submission['content']
        else:
            content = submission.content
    except:
        raise Exception(f"submission must either be a dict, openreview.Note or openreview.api.Note, got type={type(submission)}")
    ret = content.get(content_field, '')
    if isinstance(ret, dict):
        return ret['value']
    else:
        return ret

def get_decision_from_venueid (submission):
    # Legacy helper: last token of venue string (often wrong for modern venues).
    venue = submission.content.get('venue', {})
    if isinstance(venue, dict):
        venue = venue.get('value', '')
    parts = str(venue).split()
    return parts[-1] if parts else ''


def get_decision_label(submission, decision_note=None):
    """Best-effort Accept/Reject label for aclpub2 papers.yml."""
    if decision_note:
        content = decision_note.get("content", {}) if isinstance(decision_note, dict) else {}
        decision = content.get("decision", {})
        if isinstance(decision, dict):
            decision = decision.get("value")
        if decision:
            return str(decision)

    venue = submission.content.get("venue", {})
    if isinstance(venue, dict):
        venue = venue.get("value", "")
    venue = str(venue or "")
    for token in venue.replace(",", " ").split():
        low = token.lower()
        if low.startswith("accept") or low.startswith("reject"):
            return token

    venueid = submission.content.get("venueid", {})
    if isinstance(venueid, dict):
        venueid = venueid.get("value", "")
    venueid = str(venueid or "")
    if venueid.endswith("/Rejected_Submission"):
        return "Reject"
    if venueid and not venueid.endswith("/Submission"):
        # Released accepted papers usually have venueid == venue group id.
        return "Accept"
    return venue or "Accept"


def _split_fullname(full_name):
    parts = str(full_name).strip().split()
    if not parts:
        return None
    entry = {
        "first_name": parts[0],
        "last_name": parts[-1] if len(parts) > 1 else parts[0],
        "name": full_name,
    }
    if len(parts) > 2:
        entry["middle_name"] = " ".join(parts[1:-1])
    return entry


def author_entry_from_obj(obj):
    """Build a minimal author dict from an OpenReview authors[] element."""
    if isinstance(obj, dict):
        full_name = obj.get("fullname") or obj.get("name") or ""
        username = obj.get("username") or obj.get("id") or ""
        entry = _split_fullname(full_name) if full_name else {
            "first_name": username or "Unknown",
            "last_name": username or "Unknown",
            "name": full_name or username or "Unknown",
        }
        if username:
            entry["username"] = username
            entry["openreview"] = username
        institutions = obj.get("institutions") or []
        if institutions and isinstance(institutions, list):
            names = []
            for inst in institutions:
                if isinstance(inst, dict) and inst.get("name"):
                    names.append(inst["name"])
                elif isinstance(inst, str):
                    names.append(inst)
            if names:
                entry["institution"] = join_institution(names)
        return entry
    if isinstance(obj, str) and obj.strip():
        entry = _split_fullname(obj.strip())
        if obj.strip().startswith("~"):
            entry["username"] = obj.strip()
            entry["openreview"] = obj.strip()
        return entry
    return None


def collect_author_ids(submission):
    """Return profile IDs / emails for authors, preferring authorids then authors[].username."""
    authorsids = get_content_from(submission, "authorids")
    if isinstance(authorsids, str) and authorsids:
        authorsids = [authorsids]
    if authorsids:
        return list(authorsids)

    authors = get_content_from(submission, "authors")
    if isinstance(authors, str) and authors:
        authors = [authors]
    if not authors:
        return []

    ids = []
    for item in authors:
        if isinstance(item, dict):
            uid = item.get("username") or item.get("id")
            if uid:
                ids.append(uid)
        elif isinstance(item, str) and item.startswith("~"):
            ids.append(item)
    return ids


def collect_author_fallbacks(submission):
    """Structured fallbacks from the authors field when profiles cannot be fetched."""
    authors = get_content_from(submission, "authors")
    if isinstance(authors, str) and authors:
        authors = [authors]
    if not authors:
        return []
    out = []
    for item in authors:
        entry = author_entry_from_obj(item)
        if entry:
            out.append(entry)
    return out
