"""
Course advisor: recommends tracks from a short questionnaire plus free text.

Runs entirely on our server (no paid AI service): each answer adds weighted points
to the tracks it fits, words the visitor types are matched against each track's own
content (tagline, description, tools, career paths), and the best matches come back
with the reasons that produced them. Tracks added later in the admin are still
considered through the text matching, even without a hand-written profile.
"""

import re

from .models import Track

INTERESTS = {
    "protect": "protecting systems and stopping hackers",
    "data": "working with numbers and finding insights",
    "build": "building websites and apps",
    "design": "visual design and creativity",
    "people": "understanding users and solving their problems",
    "marketing": "writing, social media and growing brands",
    "business": "running your own business or freelancing",
    "logic": "logic, puzzles and how things work behind the scenes",
}

GOALS = {
    "job": "land a tech job",
    "freelance": "earn as a freelancer or remote worker",
    "business": "grow your own business",
    "switch": "switch into tech from another field",
    "explore": "explore what tech has to offer",
}

EXPERIENCE = {"none": "complete beginner", "some": "some basics", "tech": "already working in tech"}

# Hand-tuned weights for the academy's tracks, keyed by slug.
PROFILES = {
    "cybersecurity": {
        "interests": {"protect": 3, "logic": 2, "data": 1},
        "goals": {"job": 1.5, "switch": 0.5},
        "keywords": ["security", "hack", "hacker", "hacking", "cyber", "network", "protect", "defend",
                     "ethical", "privacy", "threat", "linux", "soc", "penetration", "forensic"],
    },
    "data-analysis": {
        "interests": {"data": 3, "logic": 2, "business": 1},
        "goals": {"job": 1.5, "switch": 1, "business": 0.5},
        "keywords": ["data", "number", "numbers", "excel", "spreadsheet", "analysis", "analyst", "math",
                     "statistics", "report", "chart", "dashboard", "insight", "sql", "power bi", "finance"],
    },
    "digital-marketing": {
        "interests": {"marketing": 3, "business": 2, "people": 1, "design": 0.5},
        "goals": {"business": 2, "freelance": 1, "switch": 0.5},
        "keywords": ["marketing", "social media", "instagram", "tiktok", "brand", "content", "seo", "ads",
                     "advert", "sell", "sales", "write", "writing", "copywriting", "influencer", "audience"],
    },
    "digital-services": {
        "interests": {"business": 3, "marketing": 1, "build": 1},
        "goals": {"freelance": 2, "business": 2},
        "keywords": ["freelance", "freelancing", "client", "clients", "agency", "business", "no-code",
                     "automation", "consult", "remote", "upwork", "fiverr", "side hustle", "income"],
    },
    "frontend-development": {
        "interests": {"build": 3, "design": 2, "logic": 1},
        "goals": {"job": 1, "freelance": 1},
        "keywords": ["website", "websites", "web", "html", "css", "javascript", "react", "frontend",
                     "front-end", "coding", "code", "programming", "developer", "interface", "app"],
    },
    "backend-development": {
        "interests": {"build": 2, "logic": 3, "data": 1, "protect": 0.5},
        "goals": {"job": 1.5},
        "keywords": ["backend", "back-end", "server", "api", "database", "python", "django", "node",
                     "programming", "code", "coding", "software", "engineer", "logic", "system"],
    },
    "product-design": {
        "interests": {"people": 3, "design": 2, "build": 1},
        "goals": {"job": 1, "switch": 0.5, "freelance": 0.5},
        "keywords": ["ux", "ui", "user", "users", "product", "figma", "prototype", "research",
                     "experience", "app design", "wireframe", "usability", "empathy"],
    },
    "graphics-design": {
        "interests": {"design": 3, "marketing": 1.5},
        "goals": {"freelance": 1.5, "business": 0.5},
        "keywords": ["design", "graphic", "graphics", "logo", "flyer", "poster", "canva", "photoshop",
                     "illustrator", "art", "draw", "drawing", "creative", "brand", "visual", "colour", "color"],
    },
}

BEGINNER_FRIENDLY = {"digital-marketing", "graphics-design", "data-analysis", "digital-services"}
NEEDS_EXPERIENCE = {"backend-development"}

WORD_RE = re.compile(r"[a-z0-9+#.-]+")


def _clean_choice(value, allowed):
    return value if value in allowed else None


def _lines(text):
    return [line.strip().lower() for line in (text or "").splitlines() if line.strip()]


def _track_vocabulary(track):
    """Words that describe a track, taken from its own content in the database."""
    text = " ".join([track.title, track.tagline, track.short_description, track.tools, track.career_paths])
    return set(WORD_RE.findall(text.lower())) - STOPWORDS, _lines(track.tools)


STOPWORDS = {
    "a", "an", "and", "the", "to", "of", "in", "on", "for", "with", "i", "my", "me", "is", "it", "be",
    "want", "like", "love", "enjoy", "am", "are", "do", "can", "how", "that", "this", "you", "your",
    "from", "at", "as", "or", "but", "so", "get", "into", "about", "have", "has", "will", "would",
    "learn", "become", "make", "good", "really", "things", "thing", "some", "more", "also", "work",
}


def recommend(interests=None, goal=None, experience=None, laptop=True, about="", limit=3):
    interests = [i for i in (interests or []) if i in INTERESTS][:3]
    goal = _clean_choice(goal, GOALS)
    experience = _clean_choice(experience, EXPERIENCE)
    about = (about or "")[:600]
    about_lower = about.lower()
    about_words = set(WORD_RE.findall(about_lower)) - STOPWORDS

    results = []
    for track in Track.objects.filter(is_published=True):
        profile = PROFILES.get(track.slug, {})
        score, reasons = 0.0, []

        # 1. Interests
        matched = [i for i in interests if profile.get("interests", {}).get(i)]
        for i in matched:
            score += profile["interests"][i]
        if matched:
            reasons.append("It fits your interest in " + " and ".join(INTERESTS[i] for i in matched) + ".")

        # 2. Goal
        if goal and profile.get("goals", {}).get(goal):
            score += profile["goals"][goal]
            reasons.append(f"It's a strong route if you want to {GOALS[goal]}.")

        # 3. Experience
        if experience == "none":
            if track.slug in BEGINNER_FRIENDLY:
                score += 0.75
                reasons.append("It's very beginner-friendly.")
            elif track.slug in NEEDS_EXPERIENCE:
                score -= 1
        elif experience == "tech" and track.slug in NEEDS_EXPERIENCE | {"cybersecurity"}:
            score += 1
            reasons.append("Your existing tech experience gives you a head start.")

        # 4. Device
        if not laptop:
            if track.slug == "digital-marketing":
                score += 1.5
                reasons.append("You can start it with just a smartphone.")
            else:
                score -= 0.5

        # 5. Their own words, matched against hand-picked keywords and the track's own content
        vocabulary, tools = _track_vocabulary(track)
        hits = [k for k in profile.get("keywords", []) if (k in about_lower if " " in k else k in about_words)]
        hits += [t for t in tools if t and t in about_lower and t not in hits]
        hits += sorted((about_words & vocabulary) - set(hits))[:3]
        if hits:
            score += min(4.0, 1.25 * len(hits))
            reasons.append("You mentioned " + ", ".join(f"“{h}”" for h in hits[:3]) + ".")

        if score > 0:
            results.append({"track": track, "score": score, "reasons": reasons})

    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[:limit]
    top = results[0]["score"] if results else 1
    return [{
        "title": r["track"].title,
        "slug": r["track"].slug,
        "icon": r["track"].icon,
        "tagline": r["track"].tagline,
        "duration": r["track"].duration,
        "level": r["track"].get_level_display(),
        "match": max(40, round(100 * r["score"] / top)) if i else 100,
        "reasons": r["reasons"][:3],
        "url": r["track"].get_absolute_url(),
    } for i, r in enumerate(results)]


def summary(interests, goal, experience):
    parts = []
    if experience in EXPERIENCE:
        parts.append(f"As a {EXPERIENCE[experience]}")
    if goal in GOALS:
        parts.append(f"who wants to {GOALS[goal]}")
    lead = " ".join(parts)
    return (lead + ", here's" if lead else "Here's") + " where I'd start:"
