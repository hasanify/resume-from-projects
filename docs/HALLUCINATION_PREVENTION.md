# Zero-Hallucination Evidence Contract

Most AI resume builders create fictional numbers out of thin air:
> *"Spearheaded modern cloud architecture resulting in 43% latency reduction and $120k cost savings."*

When an interviewer or technical client asks: **"How did you measure that 43% reduction?"**, the candidate has no answer because the AI invented it.

`resume-from-projects` replaces generative hallucination with **verifiable repository evidence**.

---

## The Contract

Every bullet point generated on a resume must satisfy the **Evidence Contract**:

```
[Bullet Point Text]
   └── [Evidence Citation]: specific file, route decorator count, commit hash, or test fixture
```

### Example Comparison

| Unassisted AI Output (Hallucinated) | `resume-from-projects` Output (Grounded) |
|---|---|
| *"Spearheaded scalable backend microservices, increasing user engagement by 35%."* | **"Built a REST API with 24 endpoints in FastAPI backed by PostgreSQL."**<br>*Evidence: Counted `@app.get/@app.post` route decorators in `app/routes/`.* |
| *"Optimized payment flows achieving 99.99% fault tolerance."* | **"Integrated Stripe webhook handling with idempotency keys and automated pytest suites."**<br>*Evidence: `app/payments/webhook.py` idempotency check and `tests/test_payments.py`.* |
| *"Revolutionized team productivity through state-of-the-art CI/CD."* | **"Configured GitHub Actions workflow running automated linting and unit test matrix on push."**<br>*Evidence: `.github/workflows/ci.yml` in repository.* |

---

## The Audit Trail

Before building the final `.docx` and `.pdf`, the skill emits `resume.json`. 

Each project entry contains an explicit `evidence` array:

```json
{
  "name": "logsift",
  "description": "High-throughput log indexing engine written in Go.",
  "stack": ["Go", "gRPC", "RocksDB"],
  "bullets": [
    "Engineered a log streaming ingest pipeline handling gRPC streams with RocksDB persistence",
    "Implemented 32 unit and benchmark tests with automated race condition detection"
  ],
  "evidence": [
    "gRPC & RocksDB: imported in internal/engine/storage.go",
    "32 tests + race check: counted in engine_test.go, 'go test -race' flag in Makefile"
  ]
}
```

The linter (`check_writing.py`) checks every number that appears in `bullets`. If a number appears in a bullet without an explanation in `evidence`, compilation fails with `ERROR`.
