import re
from typing import Literal, Optional

# Strong generate signals (weighted 2)
GENERATE_STRONG = [
    r"\bgenerate\b", r"\bcreate\b", r"\bmake me\b", r"\bprepare\b",
    r"\bbuild\b", r"\bproduce\b", r"\bnew quiz\b", r"\bnew mid\b",
    r"\bnew final\b", r"\bmock\b", r"\bpractice exam\b", r"\bsample exam\b",
]

GENERATE_WEAK = [
    r"\bwrite\b", r"\bcompose\b", r"\bi need a quiz\b", r"\bi need a mid\b",
    r"\bi need a final\b", r"\bcan you make\b", r"\bcan you create\b",
]

RETRIEVE_STRONG = [
    r"\bgive me\b", r"\bshow me\b", r"\bfind\b", r"\bfetch\b",
    r"\bget me\b", r"\bdo you have\b", r"\bwhere is\b", r"\blook up\b",
    r"\bsearch\b", r"\bpast\b", r"\bprevious\b", r"\bold\b",
    r"\b20\d{2}\b", 
]

RETRIEVE_WEAK = [
    r"\bgive\b", r"\bshow\b", r"\bget\b", r"\bquiz \d+\b",
    r"\bmid \d+\b", r"\bfinal \d+\b",
]

DOC_TYPE_PATTERNS = {
    "quiz":       r"\bquiz(?:zes)?\b",
    "mid":        r"\bmid(?:term)?s?\b",
    "final":      r"\bfinal(?:s|exam)?\b",
    "notes":      r"\bnotes?\b|\blectures?\b|\bslides?\b",
    "assignment": r"\bassignment\b|\blab\b|\bhomework\b|\bhw\b",
}


def detect_intent(message: str) -> Literal["retrieve", "generate", "clarify"]:
    lower = message.lower()

    gen_score = (
        sum(2 for p in GENERATE_STRONG if re.search(p, lower))
        + sum(1 for p in GENERATE_WEAK if re.search(p, lower))
    )
    ret_score = (
        sum(2 for p in RETRIEVE_STRONG if re.search(p, lower))
        + sum(1 for p in RETRIEVE_WEAK if re.search(p, lower))
    )

    if gen_score == 0 and ret_score == 0:
        return "clarify"
    if gen_score > ret_score:
        return "generate"
    if ret_score > gen_score:
        return "retrieve"
    # Tied — lean retrieve (safer: finding something > accidentally generating)
    return "retrieve"


def extract_doc_type(message: str) -> Optional[str]:
    lower = message.lower()
    for doc_type, pattern in DOC_TYPE_PATTERNS.items():
        if re.search(pattern, lower):
            return doc_type
    return None


STOPWORDS = {"and", "the", "for", "of", "in", "to", "with", "an", "a"}

def extract_course_hint(message: str, known_courses: list[str]) -> Optional[str]:
    if not known_courses:
        return None

    lower = message.lower()
    lower_no_space = lower.replace(" ", "")

    # Sort longest first to avoid short names shadowing longer ones
    sorted_courses = sorted(known_courses, key=lambda c: len(c), reverse=True)

    # 1. Full substring match
    for course in sorted_courses:
        if course.lower() in lower:
            return course.lower()

    # 2. Collapsed match
    for course in sorted_courses:
        if course.lower().replace(" ", "") in lower_no_space:
            return course.lower()

    # 3. Acronym match — only for multi-word courses
    for course in sorted_courses:
        words = [w for w in course.split() if len(w) > 2 and w.lower() not in STOPWORDS]
        if len(words) < 2:
            continue
        acronym = "".join(w[0].upper() for w in words)

        # Escape acronym in case it has special regex characters
        pattern = r"\b" + re.escape(acronym) + r"\b"

        if re.search(pattern, message.upper()):
            return course.lower()

    return None