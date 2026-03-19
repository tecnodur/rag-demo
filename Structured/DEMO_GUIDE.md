# Structured RAG Demo Guide

Use this file as a quick follow-along for the `Structured` demo. For the full explanation of the approach, see [README.md](README.md).

## 1. Check The Metadata Layer

- Open [data/source_docs/metadata_manifest.json](data/source_docs/metadata_manifest.json).
- Check fields such as `region`, `status`, `version`, `effective_date`, and `doc_type`.
- Open [password_policy_v3_EU_active.md](data/source_docs/password_policy_v3_EU_active.md) and check the metadata block at the top.

What this means:

- the knowledge base includes explicit business metadata
- the system does not need to infer those attributes from raw text alone

## 2. Check Validation And Chunking

- Open [src/utils.py](src/utils.py) and check that metadata is parsed and validated.
- Open [src/chunker.py](src/chunker.py) and check that chunk records inherit metadata fields.
- Open [src/ingest.py](src/ingest.py) and check that the vector index definition includes filter fields.

What this means:

- metadata becomes part of the chunk schema
- retrieval can use both semantics and business constraints

## 3. Check The Retrieval Logic

- Open [src/retrieval.py](src/retrieval.py).
- Check the metadata filter construction.
- Check the logic that prefers the latest valid version.

What this means:

- retrieval is constrained before generation
- the system can narrow to the right policy space before the model answers

## 4. Run The Ingestion

- Run `python3 scripts/load_to_atlas.py`
- Check that the pipeline uploads chunks, embeddings, and metadata to MongoDB Atlas.

## 5. Run The Demo

- Run `python3 scripts/run_demo.py --region EU --status Active --doc-type policy`
- Check the retrieved chunks first.
- Check the generated answer next.

What to look for:

- the retrieved evidence should stay inside the correct business context
- the final answer should be better grounded and more reliable

## 6. Final Check

- Reopen [src/retrieval.py](src/retrieval.py).
- Confirm that the solution combines vector similarity with metadata-aware retrieval.

## Summary

`Structured` RAG retrieves what is similar and authoritative.
That improvement comes from the knowledge architecture.
