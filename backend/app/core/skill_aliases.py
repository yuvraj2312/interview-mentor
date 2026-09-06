"""Curated alias table for common skill abbreviation/full-name pairs.

Cosine similarity on bare skill tokens can't reliably separate true
synonyms (e.g. "JS"/"JavaScript", cosine ~0.87) from closely-related-but-
distinct skills (e.g. "Java"/"JavaScript", cosine ~0.83) - the score
ranges overlap, so no single threshold is both safe and useful. This
table resolves the well-known cases deterministically, right after the
exact-string pass; embedding similarity (skill_gap_service._semantic_match)
is a conservative fallback for skill phrasings not covered here.

Keys and values are already normalized (stripped/lowercased) to match how
skill_gap_service builds its lookups.
"""

SKILL_ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "psql": "postgresql",
    "node": "node.js",
    "nodejs": "node.js",
    "mongo": "mongodb",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "ai": "artificial intelligence",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "reactjs": "react",
    "vuejs": "vue",
    "golang": "go",
    "py": "python",
    "csharp": "c#",
    "dotnet": ".net",
}


def canonicalize(normalized_skill: str) -> str:
    """Map a normalized skill string to its canonical form, if aliased."""
    return SKILL_ALIASES.get(normalized_skill, normalized_skill)
