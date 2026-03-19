# Naive RAG Demo Guide

Use this file as a step-by-step tutorial for the `Naive` implementation. For the full explanation, see [README.md](README.md).

## 1. Check The Data Shape

- Open [src/utils.py](src/utils.py) and check that only `document_id`, `source_file`, and `title` are derived.
- Open [src/chunker.py](src/chunker.py) and check that chunk records contain text and identifiers only.

## 2. Check The Retrieval Logic

- Open [src/retrieval.py](src/retrieval.py) and check that retrieval uses `$vectorSearch` only.
- Check that there are no metadata filters.
- Check that there is no version-selection logic.

What this means:

- retrieval is based only on semantic similarity
- relevant text can be returned even when it is not authoritative

## 3. Version Drift Flow (v2 Then v3)

Follow this sequence to reproduce the version-selection issue.

Step A: ingest without v3

- Run `python3 scripts/load_to_atlas.py --exclude-source-file password_policy_v3_EU_active.md`
- Run `python3 scripts/run_demo.py`
- Observe that the answer is usually consistent because only the v2 policy is present.
- Observe in retrieved chunks that evidence comes from `password_policy_v2_EU.md`.

Step B: ingest again with all files (including v3)

- Run `python3 scripts/load_to_atlas.py`
- Run `python3 scripts/run_demo.py`
- Observe that both policy versions are now available in the vector index.
- Observe that retrieval can return chunks from v2 and v3 without a rule to select the authoritative one.
- Now you can see that similarity-only retrieval does not guarantee version-correct answers.

What to conclude:

- the main issue is retrieval governance, not fluent text generation
- without structured constraints, the system cannot reliably pick the correct policy version

## 4. Compare With Structured

Now compare this behavior with the `Structured` approach:

- `Naive`: text + embeddings + similarity search
- `Structured`: text + embeddings + business metadata + similarity search + metadata filters + version selection
- Observe that `Structured` adds explicit constraints that prevent cross-version ambiguity.

## Summary

`Naive` RAG retrieves what looks similar.
It does not reliably retrieve what is authoritative.
`Structured` is the continuation that addresses this exact gap.
