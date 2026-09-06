from app.core.skill_aliases import canonicalize


def test_canonicalizes_known_aliases_to_the_same_form():
    assert canonicalize("js") == canonicalize("javascript")
    assert canonicalize("postgres") == canonicalize("postgresql")
    assert canonicalize("k8s") == canonicalize("kubernetes")


def test_leaves_unknown_skills_unchanged():
    assert canonicalize("python") == "python"
    assert canonicalize("kubernetes") == "kubernetes"
