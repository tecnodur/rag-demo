# Naive RAG Demo Guide

Use this file as a quick follow-along for the `Naive` demo. For the full explanation of the approach, see [README.md](/home/rud/Documents/Naive/README.md).

## 1. Check The Data Shape

- Open [src/utils.py](/home/rud/Documents/Naive/src/utils.py) and check that only `document_id`, `source_file`, and `title` are derived.
- Open [src/chunker.py](/home/rud/Documents/Naive/src/chunker.py) and check that chunk records contain text and identifiers only.

What this means:

- chunks do not carry structured business metadata
- retrieval cannot filter by `region`, `status`, `version`, or `doc_type`

## 2. Check The Retrieval Logic

- Open [src/retrieval.py](/home/rud/Documents/Naive/src/retrieval.py) and check that retrieval uses `$vectorSearch` only.
- Check that there are no metadata filters.
- Check that there is no version-selection logic.

What this means:

- retrieval is based only on semantic similarity
- relevant text can be returned even when it is not authoritative

## 3. Run The Ingestion

- Run `python3 scripts/load_to_atlas.py`
- Check that the pipeline loads the documents, creates chunks, generates embeddings, and uploads them to MongoDB Atlas.

## 4. Run The Demo

- Run `python3 scripts/run_demo.py`
- Check the retrieved chunks first.
- Check the generated answer next.

What to look for:

- the system may retrieve an outdated or less authoritative chunk
- the answer may still sound fluent and confident

## 5. Final Check

- Reopen [src/retrieval.py](/home/rud/Documents/Naive/src/retrieval.py).
- Confirm that the solution relies on vector similarity only.

## Summary

`Naive` RAG retrieves what looks similar.
It does not reliably retrieve what is authoritative.
