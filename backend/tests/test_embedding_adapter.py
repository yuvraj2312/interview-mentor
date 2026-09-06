from app.core.config import settings
from app.embedding_adapter import get_embedding_adapter
from app.services.skill_gap_service import _cosine_similarity

adapter = get_embedding_adapter()


def test_embed_returns_one_vector_per_text_in_order():
    vectors = adapter.embed(["JavaScript", "PostgreSQL"])

    assert len(vectors) == 2
    assert len(vectors[0]) == settings.embedding_dimension
    assert len(vectors[1]) == settings.embedding_dimension


def test_documented_synonyms_clear_the_fallback_threshold():
    # JS/JavaScript and Postgres/PostgreSQL happen to clear the 0.85
    # fallback threshold on their own (0.87 and 0.93), but production
    # matching resolves them via the alias table (skill_aliases.py), not
    # this path - see test_skill_gap.py::test_compute_matches_via_alias_table_not_just_embeddings
    # for a documented pair that only the alias table catches.
    js, js_synonym = adapter.embed(["JavaScript", "JS"])
    postgres, postgres_synonym = adapter.embed(["PostgreSQL", "Postgres"])

    assert _cosine_similarity(js, js_synonym) >= settings.skill_match_similarity_threshold
    assert _cosine_similarity(postgres, postgres_synonym) >= settings.skill_match_similarity_threshold


def test_unrelated_skills_are_not_similar():
    python, kubernetes = adapter.embed(["Python", "Kubernetes"])

    assert _cosine_similarity(python, kubernetes) < settings.skill_match_similarity_threshold


def test_false_friend_java_javascript_stays_below_threshold():
    # The reason matching isn't pure-embedding: "Java"/"JavaScript" scores
    # ~0.83 - higher than several legitimate synonym pairs (e.g.
    # "K8s"/"Kubernetes" ~0.67) - so no single threshold both accepts real
    # synonyms and rejects this. 0.85 was picked to stay safely above this
    # and other false friends found during calibration (max observed: 0.84
    # for "MySQL"/"PostgreSQL"), accepting lower recall in exchange -
    # that's what the alias table compensates for.
    java, javascript = adapter.embed(["Java", "JavaScript"])

    assert _cosine_similarity(java, javascript) < settings.skill_match_similarity_threshold
