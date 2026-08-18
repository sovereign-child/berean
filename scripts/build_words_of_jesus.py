#!/usr/bin/env python3
"""
Berean — "The Words of Jesus" builder.

Compiles every passage spoken by Jesus into one book, in canonical order, from
the Berean Standard Bible (CC0). No external red-letter dataset is used or
needed: the BSB's own quotation marks already encode where each speech starts
and stops, so the result is reproducible from a public-domain text we host.

Method — deliberately conservative, and disclosed in the output file:

  * BSB reserves the curly double quotes  “ ”  for the OUTERMOST level of
    speech and nests with single quotes  ‘ ’ . So speech is a boolean state,
    not a depth counter: a “ met while already speaking is the English
    multi-paragraph convention (each paragraph re-opens, only the last closes),
    never a new quotation.
  * Speeches run across chapter boundaries — the Sermon on the Mount is one
    quotation from Matthew 5:3 to 7:27 — so each book is scanned as one stream.
  * Each speech is attributed from the NARRATOR'S OWN CLAUSE, and only from
    that: all quoted material is stripped out of the context first, so words
    spoken by someone else can never be mistaken for the narrator naming a
    speaker.
  * A trailing clause is read as this speech's attribution ("...," said Jesus)
    only when it is not the clause introducing the next speaker's quotation.
  * The Father's voice — the baptism, the transfiguration, John 12:28 — is kept
    as a SEPARATE voice, not folded in. Red-letter editions disagree about it;
    Berean labels it and does not decide for you.
  * Speech the narrator does not attribute is LEFT OUT rather than guessed. A
    short curated list (below) restores passages where the text names the
    speaker inside the speech itself ("I am Jesus, whom you are persecuting"),
    which no attribution rule can see. Those are marked "curated" in the data.

Output: library/words-of-jesus.json — character offsets into the BSB corpus, never
a copy of the text, so the compiled book can never drift out of sync with it.

Run from the repo root:
    python3 scripts/build_words_of_jesus.py
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import berean_lib as lib   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BSB = os.path.join(ROOT, "library", "corpus", "BSB.json")
OUT = os.path.join(ROOT, "library", "words-of-jesus.json")

OPEN, CLOSE = "“", "”"

# Books scanned. All are narrative or vision, where a narrator names the speaker.
# The epistles are NOT scanned: "says the Lord" there is nearly always an Old
# Testament citation, and the handful of real sayings Paul quotes are curated
# below instead of guessed at.
BOOKS = ["Matthew", "Mark", "Luke", "John", "Acts"]

SPEECH = (r"(?:said|say|says|saying|answered|answering|answer|replied|reply|replying|told|telling|"
          r"asked|asking|declared|declaring|declares|responded|cried out|crying out|called out|"
          r"calling out|calls|taught|teaching|teach|spoke|speaking|speaks|instructed|commanded|"
          r"commanding|warned|warning|rebuked|rebuking|prayed|praying|explained|continued|"
          r"went on to say|exclaimed|shouted|shouting|urged|charged|proclaimed|proclaiming|preach|"
          r"preached|preaching|announced|added|grumbled|murmured|objected|protested|insisted|"
          r"testified|promised|swore|began to)")
SPEECH_RE = re.compile(SPEECH, re.I)

# Only an outright naming counts. Titles that others use ABOUT Jesus ("the Christ",
# "Rabbi", "the Son of Man") appear all over crowd speech and narration, so they
# are not evidence about who is speaking.
JESUS_NAME = re.compile(r"\bJesus\b(?![’'`]s?\b)")   # not the possessive "Jesus’ mother"
JESUS_LORD = re.compile(r"\bthe Lord\b")          # in Acts/Revelation this is Jesus
# BSB capitalizes pronouns referring to deity — a strong signal, though shared
# with the Father, so it only decides inside a Gospel narrative following Jesus.
# The lookbehind keeps an ordinary sentence-initial "He" from counting.
DIVINE_PRONOUN = re.compile(r"(?<![.!?”—]\s)(?<!^)\b(?:He|Him|His)\b")
FATHER = re.compile(r"(?:a voice (?:from|out of|came from|spoke|said)|the voice (?:from|out of)|"
                    r"voice came from heaven|from the cloud|the Father|God said|God replied|"
                    r"(?:the One|He who was) seated on the throne|the Lord God)", re.I)
# Anyone else who might be holding the floor. Case-insensitive: a clause can
# begin "The tempter came to Him and said".
NOT_JESUS = re.compile(
    r"\b(?:pilate|peter|simon|judas|john|paul|herod|caiaphas|barnabas|silas|"
    r"the devil|satan|the tempter|the angel|an angel|angels|the crowd|the crowds|the people|"
    r"the pharisees|the scribes|the disciples|his disciples|the chief priests|the elders|"
    r"the jews|the sadducees|the servant|the centurion|the soldiers|the woman|the man|the men|"
    r"moses|elijah|isaiah|david|the prophet|the prophets|the scripture|gabriel|mary|martha|"
    r"philip|andrew|thomas|nathanael|nicodemus|stephen|ananias|agrippa|festus|felix|gamaliel|"
    r"the spirit|the holy spirit|a demon|the demons|the evil spirit|the rich man|abraham|"
    r"mother|brothers|sisters|the twelve|the seventy-two|the tax collector|the guards|saul|"
    r"they|one of them|someone|a leper|the father of|the king|the master|the owner)\b", re.I)
NOT_JESUS_CS = re.compile(r"\bthe LORD\b")        # small caps = YHWH in an OT citation
PASSIVE = re.compile(r"\b(?:was|were)\s+(?:told|asked|informed|shown|warned|instructed)\b", re.I)
CITATION = re.compile(r"(?:it is written|the Scripture|Scripture says|the prophet|prophesied|"
                      r"fulfill(?:ed)? what|spoken (?:of )?through|as .* says)", re.I)


def load_bsb():
    with open(BSB, encoding="utf-8") as f:
        return json.load(f)


def verses(book):
    """Flatten a book into a (chapter, verse, text) stream — speeches cross
    chapter boundaries, so a book is scanned as one continuous text."""
    return [(ci + 1, vi + 1, text)
            for ci, ch in enumerate(book["chapters"])
            for vi, text in enumerate(ch)]


def flatten(vs):
    """One string for the whole book, with a map from each character back to the
    verse it came from."""
    buf, pos = [], []
    for i, (_, _, text) in enumerate(vs):
        for o, ch in enumerate(text):
            buf.append(ch)
            pos.append((i, o))
        buf.append(" ")
        pos.append((i, len(text)))
    return "".join(buf), pos


def scan(flat):
    """Every outermost quotation, plus a mask marking which characters are
    inside one. `speaking` is boolean: a “ met while already speaking is a
    paragraph continuation, because BSB nests with ‘ ’ instead."""
    spans, mask, speaking, start = [], bytearray(len(flat)), False, 0
    for i, ch in enumerate(flat):
        if ch == OPEN and not speaking:
            speaking, start = True, i + 1
        elif ch == CLOSE and speaking:
            speaking = False
            spans.append((start, i))
        if speaking:
            mask[i] = 1
    if speaking:
        spans.append((start, len(flat)))
    return spans, mask


def narrative(flat, mask, lo, hi):
    """The narrator's own words in flat[lo:hi] — every quotation removed, so an
    attribution clause is never read out of someone's speech. Each removed
    quotation leaves a ¶ behind: a quotation is a sentence-sized unit, and the
    sentence-ending punctuation that would have separated the narrator's clauses
    sits inside it ("…glorify Your name!” Then a voice came from heaven:")."""
    out, dropped = [], False
    for i in range(lo, min(hi, len(flat))):
        if mask[i] or flat[i] in (OPEN, CLOSE):
            dropped = True
            continue
        if dropped:
            out.append(" ¶ ")
            dropped = False
        out.append(flat[i])
    if dropped:
        out.append(" ¶ ")
    return "".join(out)


SUBJECT_SPLIT = re.compile(r"[,;:—]")


def subject_seg(pre):
    """What stands between the last punctuation break and the speech verb — the
    phrase that actually governs it. Keeps a name that is only an object or a
    possessor from being read as the speaker: "an angel of the Lord … saying",
    "began to proclaim Jesus in the synagogues, declaring", "Jesus’ mother said"."""
    return SUBJECT_SPLIT.split(pre)[-1][-60:]


def subject_windows(pre):
    """Where to look for the speaker, nearest first. When the verb follows a
    comma directly (", saying:") the subject is back at the head of the clause it
    continues — "and He began to teach them, saying:"."""
    segs = SUBJECT_SPLIT.split(pre)
    yield segs[-1][-60:]
    if len(segs) > 1 and not segs[-1].strip():
        yield segs[-2][:32]


def classify(window, book):
    """Who does the narrator's clause say is speaking?"""
    if PASSIVE.search(window):
        return None                # "He was told," — that names who was spoken TO
    if NOT_JESUS_CS.search(window):
        return None
    if JESUS_NAME.search(window):
        return "jesus"
    if FATHER.search(window):
        return "father"
    if NOT_JESUS.search(window):
        return None
    if book == "Acts" and JESUS_LORD.search(window):
        return "jesus"
    # BSB capitalizes pronouns for deity, and in a Gospel the narrative subject
    # is Jesus. In Acts and Revelation it is not, so a bare pronoun decides
    # nothing there — those speeches are named or left out.
    if book in ("Matthew", "Mark", "Luke", "John") and DIVINE_PRONOUN.search(window):
        return "jesus"
    return None


def speaker_before(clause, m, book):
    """Speaker of a verb whose subject precedes it: "Then Jesus said to them,"."""
    for window in subject_windows(clause[: m.start()]):
        who = classify(window, book)
        if who:
            return who
        if NOT_JESUS.search(window):
            return None
    return None


INVERTED = re.compile(r"^[\s,]*(?:Jesus|He|the Lord)\b")


def speaker_of(clause, m, book):
    """Speaker of a verb, either order: "Then Jesus said," or the inverted form
    BSB also uses — “…,” said Jesus, “and…”. The inverted subject only counts
    when the slot before the verb is empty and the name follows it immediately;
    otherwise the name belongs to something else in the sentence."""
    who = speaker_before(clause, m, book)
    if who:
        return who
    if subject_seg(clause[: m.start()]).strip(" ¶"):
        return None
    trail = clause[m.end(): m.end() + 30]
    return classify(trail[:20], book) if INVERTED.match(trail) else None


def attribute(flat, mask, span, book):
    """Read the narrator's clause after the quote, then before it.

    A clause AFTER the quote is ours only when it is not introducing the next
    speaker. The two cases look alike —

        “The time is fulfilled,” He said, “and the kingdom…”        (ours)
        “…become bread.” But Jesus answered, “It is written…”       (the next speaker's)

    — apart from two signals: a quotation broken off with a comma is still ours,
    and a clause with a fresh quotation right behind it belongs to that one."""
    s, e = span
    tail_raw = flat[e + 1: e + 220]
    after = narrative(flat, mask, e + 1, e + 220)
    m = SPEECH_RE.search(after[:70])
    if m:
        interrupted = flat[:e].rstrip().endswith(",")
        nxt = tail_raw.find(OPEN)
        # After a quotation that ended in a full stop, a trailing attribution is
        # a short clause of its own ("Jesus asked."). A long one is the narrative
        # moving on ("And He instructed the crowd to sit down on the ground.").
        sentence = re.split(r"(?<=[.!?])\s|\s¶", after.strip())[0]
        if not interrupted and len(sentence) > 35:
            m = None
    if m:
        if interrupted or nxt < 0 or nxt > len(after[:m.end()]) + 50:
            who = speaker_of(after[: m.end() + 60], m, book)
            if who:
                return who, "after"

    before = narrative(flat, mask, max(0, s - 900), s - 1)
    clauses = [c.strip() for c in re.split(r"(?<=[.!?])\s+|\s*¶\s*", before) if c.strip()]
    lead = clauses[-1] if clauses else ""
    # A clause INTRODUCING a quotation runs into it, so it ends with a comma or a
    # colon. One ending in a full stop is a finished sentence — the attribution of
    # the PREVIOUS quotation ("…?” Jesus asked.  “Seven,” they replied"), and
    # reading it here is what would put the disciples' answer in Jesus' mouth.
    if not lead.endswith((",", ":", ";", "—")):
        return None, None
    if CITATION.search(lead):
        return None, None                          # "…to fulfill what Isaiah the prophet said:"
    ms = list(SPEECH_RE.finditer(lead))
    if ms:
        who = speaker_of(lead, ms[-1], book)
        return (who, "before") if who else (None, None)
    if FATHER.search(lead):                        # "Then a voice came from heaven:"
        return "father", "lead"
    if len(clauses) > 1 and not CITATION.search(clauses[-2]):
        ms = list(SPEECH_RE.finditer(clauses[-2]))
        if ms:
            who = speaker_before(clauses[-2], ms[-1], book)
            if who:
                return who, "before"
    return None, None


def merge(passages, flat, mask):
    """Join consecutive speeches by the same voice when only a short attribution
    clause separates them, so a discourse reads as one passage. `idx` counts the
    book's quotations including the ones we dropped, so another speaker's turn
    always breaks the join."""
    out = []
    for p in passages:
        if out:
            q = out[-1]
            if q["voice"] == p["voice"] and p["idx"] == q["idx"] + 1:
                gap = narrative(flat, mask, q["span"][1], p["span"][0]).strip()
                if len(gap) <= 120 and not NOT_JESUS.search(gap):
                    q["span"] = (q["span"][0], p["span"][1])
                    q["idx"] = p["idx"]
                    q["parts"].append(p["span"])
                    continue
        p["parts"] = [p["span"]]
        out.append(p)
    return out


# Sayings the narrator never attributes in a clause of his own — the speaker is
# named inside the speech, or by a later verse. Restored by hand, marked in the
# data, and each one checked against the BSB text by scripts/check_words_of_jesus.py.
CURATED = [
    ("Acts", 9, 4, 9, 6, "jesus", "“I am Jesus, whom you are persecuting” (v5) names the speaker"),
    ("1 Corinthians", 11, 24, 11, 25, "jesus", "the words at the Supper, quoted by Paul (v23)"),
    # Revelation is curated whole. In a vision the speaker changes with no clause
    # from a narrator at all — 22:12 continues the angel's quotation typographically
    # but is Jesus, who names Himself four verses later. No rule can read that; a
    # reference can, so these are listed openly instead of guessed at.
    ("Revelation", 1, 11, 1, 11, "jesus", "the voice like a trumpet; identified in v12–18"),
    ("Revelation", 1, 17, 3, 22, "jesus", "the risen Christ to the seven churches; “I am the First and the Last” (1:17)"),
    ("Revelation", 16, 15, 16, 15, "jesus", "“Behold, I am coming like a thief” — an aside in the vision"),
    ("Revelation", 22, 7, 22, 7, "jesus", "“Behold, I am coming soon”"),
    ("Revelation", 22, 12, 22, 16, "jesus", "“I, Jesus, have sent My angel” (v16) names the speaker"),
    ("Revelation", 22, 20, 22, 20, "jesus", "“Yes, I am coming soon” — He who testifies to these things"),
    ("Revelation", 1, 8, 1, 8, "father", "“says the Lord God, who is and was and is to come”"),
    ("Revelation", 21, 5, 21, 8, "father", "the One seated on the throne"),
]


def curated_parts(book, bname, lo, hi):
    """The quotations lying inside a curated range — so a hand-listed passage
    quotes exactly what is in quotation marks, never the narrator's frame
    ("…,” says the Lord God, who is and was") and never another speaker who
    answers inside it ("Who are You, Lord?" — Saul, in Acts 9:5).

    A range may also sit INSIDE a larger quotation rather than contain one:
    Revelation 22:12 opens a paragraph that typographically continues the angel's
    speech but is Jesus. Such a span is clipped to the range instead of skipped."""
    vs = verses(book)
    flat, pos = flatten(vs)
    spans, mask = scan(flat)
    bounds = {}
    for i, (c, v, _) in enumerate(vs):
        idx = [k for k in range(len(pos)) if pos[k][0] == i]
        bounds[(c, v)] = (idx[0], idx[-1])
    lo_i, hi_i = bounds[lo][0], bounds[hi][1]

    parts = []
    for a, b in spans:
        if b <= lo_i or a >= hi_i:
            continue
        a, b = max(a, lo_i), min(b, hi_i)
        # Only a clause that actually introduces THIS quotation can veto it. Empty
        # means the quotation follows another with no narration between, and a
        # clause ending in a full stop attributed the one before it.
        lead = re.split(r"(?<=[.!?])\s+|\s*¶\s*",
                        narrative(flat, mask, max(0, a - 300), a - 1))[-1].strip()
        trail = re.split(r"(?<=[.!?])\s|\s¶", narrative(flat, mask, b, b + 120).strip())[0][:35]
        # Veto only on the SUBJECT of a real attribution clause. Anything looser
        # rejects "I heard a loud voice … saying," because the Spirit is named a
        # line earlier, or Revelation 22:7 because John names himself next.
        vetoed = False
        if lead.endswith((",", ":", ";", "—")):
            ms = list(SPEECH_RE.finditer(lead))
            if ms and any(NOT_JESUS.search(w) for w in subject_windows(lead[: ms[-1].start()])):
                vetoed = True
        mt = SPEECH_RE.search(trail)
        if mt and NOT_JESUS.search(trail):
            vetoed = True                     # “Who are You, Lord?” Saul asked.
        if vetoed:
            continue
        vi, off = pos[a]
        vj, offj = pos[min(b - 1, len(pos) - 1)]
        parts.append({"from": [vs[vi][0], vs[vi][1], off],
                      "to": [vs[vj][0], vs[vj][1], offj + 1]})
    return parts


def build():
    bsb = load_bsb()
    by_name = {b["name"]: b for b in bsb["books"]}
    books_out, counts = [], {"jesus": 0, "father": 0, "skipped": 0}

    for name in BOOKS:
        book = by_name.get(name)
        if not book:
            continue
        vs = verses(book)
        flat, pos = flatten(vs)
        spans, mask = scan(flat)

        kept = []
        for idx, span in enumerate(spans):
            voice, where = attribute(flat, mask, span, name)
            if voice is None:
                counts["skipped"] += 1
                continue
            kept.append({"span": span, "voice": voice, "src": where, "idx": idx})

        passages = []
        for p in merge(kept, flat, mask):
            def ref_at(i):
                vi, off = pos[min(i, len(pos) - 1)]
                return vs[vi][0], vs[vi][1], off
            sc, sv, _ = ref_at(p["span"][0])
            ec, ev, _ = ref_at(p["span"][1] - 1)
            ref = (f"{name} {sc}:{sv}" if (sc, sv) == (ec, ev)
                   else f"{name} {sc}:{sv}–{ev}" if sc == ec
                   else f"{name} {sc}:{sv}–{ec}:{ev}")
            parts = []
            for a, b in p["parts"]:
                c1, v1, o1 = ref_at(a)
                c2, v2, o2 = ref_at(b - 1)
                parts.append({"from": [c1, v1, o1], "to": [c2, v2, o2 + 1]})
            passages.append({"voice": p["voice"], "ref": ref, "src": p["src"],
                             "from": [sc, sv], "to": [ec, ev], "parts": parts})
            counts[p["voice"]] += 1
        if passages:
            books_out.append({"code": lib.code_for(name), "book": name, "passages": passages})

    # curated restorations, inserted in canonical order
    order = {b["name"]: i for i, b in enumerate(bsb["books"])}
    by_out = {b["book"]: b for b in books_out}
    for bname, c1, v1, c2, v2, voice, why in CURATED:
        book = by_name[bname]
        entry = by_out.get(bname)
        if entry is None:
            entry = {"code": lib.code_for(bname), "book": bname, "passages": []}
            by_out[bname] = entry
            books_out.append(entry)
        # never duplicate what the parser already found
        if any(not (tuple(p["to"]) < (c1, v1) or tuple(p["from"]) > (c2, v2))
               for p in entry["passages"]):
            continue
        ref = (f"{bname} {c1}:{v1}" if (c1, v1) == (c2, v2)
               else f"{bname} {c1}:{v1}–{v2}" if c1 == c2
               else f"{bname} {c1}:{v1}–{c2}:{v2}")
        parts = curated_parts(book, bname, (c1, v1), (c2, v2))
        if not parts:
            continue
        entry["passages"].append({
            "voice": voice, "ref": ref, "src": "curated", "why": why,
            "from": [c1, v1], "to": [c2, v2], "parts": parts,
        })
        counts[voice] += 1
        entry["passages"].sort(key=lambda p: (p["from"][0], p["from"][1]))
    books_out.sort(key=lambda b: order[b["book"]])

    spoken = set()
    for b in books_out:
        for p in b["passages"]:
            if p["voice"] != "jesus":
                continue
            for part in p["parts"]:
                (c1, v1, _), (c2, v2, _) = part["from"], part["to"]
                for c in range(c1, c2 + 1):
                    lo = v1 if c == c1 else 1
                    hi = v2 if c == c2 else len(by_name[b["book"]]["chapters"][c - 1])
                    for v in range(lo, hi + 1):
                        spoken.add((b["book"], c, v))

    data = {
        "id": "WOJ",
        "title": "The Words of Jesus",
        "subtitle": "every passage He speaks, gathered in canonical order",
        "version": "BSB",
        "license": "CC0-1.0",
        "attribution": bsb["attribution"],
        "note": ("Compiled from the Berean Standard Bible's own quotation marks — the punctuation of a "
                 "public-domain translation, not a judgment about who is speaking. Each passage is "
                 "attributed from the narrator's clause (“…,” Jesus said), reading only his words and "
                 "never anyone else's. Speech the narrator leaves unattributed is left out rather than "
                 "guessed; a few sayings that name their speaker from inside (“I am Jesus, whom you are "
                 "persecuting”) are restored by hand and marked. The Father's voice is kept separate and "
                 "labeled — red-letter editions disagree about it, and Berean does not decide for you. "
                 "Open any passage to read it in its own chapter."),
        "voices": {"jesus": "Spoken by Jesus",
                   "father": "The Father's voice — labeled separately, not folded in"},
        "stats": {"passages": counts["jesus"], "fatherPassages": counts["father"],
                  "verses": len(spoken), "unattributed": counts["skipped"]},
        "books": books_out,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {os.path.relpath(OUT, ROOT)} — {counts['jesus']} passages of Jesus "
          f"({len(spoken)} verses), {counts['father']} of the Father, "
          f"{counts['skipped']} quotations left unattributed")


if __name__ == "__main__":
    build()
