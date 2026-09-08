"""Hand-written starter set for the learning_resources vector collection.

No curated content library exists yet, so this is a small, reviewable seed
covering the topics that have actually come up in testing so far, rather
than an auto-generated or scraped library. Each entry's "id" is a stable
hand-picked slug (not a random uuid) so re-running
app/scripts/seed_learning_resources.py upserts in place instead of
duplicating.

Adding more resources later needs no schema change: append a dict here
(any extra keys just ride along in the Qdrant payload) and re-run the seed
script - there is no Postgres migration involved, since RoadmapItem stores
a denormalized snapshot of whatever a search returns, not a foreign key
into this list.
"""

LEARNING_RESOURCES = [
    {
        "id": "distributed-systems-designing-data-intensive-apps",
        "topic_key": "distributed systems",
        "title": "Designing Data-Intensive Applications (ch. 5-9: Replication, Partitioning, Consistency)",
        "url": "https://dataintensive.net/",
        "resource_type": "book",
        "description": (
            "Distributed systems fundamentals: replication strategies, partitioning/sharding, consensus, "
            "and the consistency/availability tradeoffs behind CAP and PACELC."
        ),
    },
    {
        "id": "distributed-systems-mit-6-824",
        "topic_key": "distributed systems",
        "title": "MIT 6.824: Distributed Systems (lecture series)",
        "url": "https://pdos.csail.mit.edu/6.824/",
        "resource_type": "course",
        "description": (
            "Graduate-level distributed systems course covering Raft consensus, replicated state machines, "
            "fault tolerance, and distributed transactions, with hands-on Go labs."
        ),
    },
    {
        "id": "rest-apis-microsoft-rest-guidelines",
        "topic_key": "rest apis",
        "title": "Microsoft REST API Guidelines",
        "url": "https://github.com/microsoft/api-guidelines",
        "resource_type": "article",
        "description": (
            "Practical REST API design guidance: resource modeling, HTTP verb/status code semantics, "
            "versioning, pagination, and idempotency for HTTP APIs."
        ),
    },
    {
        "id": "rest-apis-restful-web-apis-richardson",
        "topic_key": "rest apis",
        "title": "RESTful Web APIs (Richardson & Amundsen)",
        "url": "https://www.oreilly.com/library/view/restful-web-apis/9781449359713/",
        "resource_type": "book",
        "description": (
            "REST architectural constraints, hypermedia (HATEOAS), resource design, and the Richardson "
            "maturity model for evaluating how RESTful an API actually is."
        ),
    },
    {
        "id": "caching-scaling-memcache-at-facebook",
        "topic_key": "caching",
        "title": "Scaling Memcache at Facebook (paper)",
        "url": "https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf",
        "resource_type": "article",
        "description": (
            "Cache invalidation strategies, cache-aside vs. write-through patterns, thundering herd "
            "mitigation, and consistency tradeoffs at large scale."
        ),
    },
    {
        "id": "caching-redis-university",
        "topic_key": "caching",
        "title": "Redis University: RU101 - Introduction to Redis Data Structures",
        "url": "https://university.redis.com/courses/ru101/",
        "resource_type": "course",
        "description": (
            "Practical caching with Redis: eviction policies (LRU/LFU/TTL), data structure choice for cache "
            "keys, and common caching patterns."
        ),
    },
    {
        "id": "cicd-continuous-delivery-humble-farley",
        "topic_key": "ci/cd",
        "title": "Continuous Delivery (Humble & Farley)",
        "url": "https://continuousdelivery.com/",
        "resource_type": "book",
        "description": (
            "The deployment pipeline model: build/test/release stages, trunk-based development, feature "
            "flags, and reducing deployment risk through automation."
        ),
    },
    {
        "id": "cicd-github-actions-docs",
        "topic_key": "ci/cd",
        "title": "GitHub Actions documentation: Building and testing workflows",
        "url": "https://docs.github.com/en/actions",
        "resource_type": "doc",
        "description": (
            "Hands-on CI/CD pipeline construction: workflow triggers, job dependencies, caching build "
            "artifacts, and deployment gating."
        ),
    },
    {
        "id": "cloud-platforms-aws-well-architected",
        "topic_key": "cloud platforms",
        "title": "AWS Well-Architected Framework",
        "url": "https://aws.amazon.com/architecture/well-architected/",
        "resource_type": "doc",
        "description": (
            "Cloud architecture pillars - reliability, cost optimization, performance efficiency, security - "
            "applicable across major cloud providers, not just AWS-specific services."
        ),
    },
    {
        "id": "cloud-platforms-google-cloud-architecture-center",
        "topic_key": "cloud platforms",
        "title": "Google Cloud Architecture Center",
        "url": "https://cloud.google.com/architecture",
        "resource_type": "doc",
        "description": (
            "Reference architectures for common cloud patterns: autoscaling, managed load balancing, "
            "multi-region deployment, and infrastructure-as-code."
        ),
    },
]
