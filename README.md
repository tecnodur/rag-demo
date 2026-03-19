# MongoDB Atlas RAG Demo Repository

This repository contains two small RAG implementations built for presentation and comparison.

Both solutions use the same general flow:

1. Load a small set of source documents.
2. Convert the documents into plain text.
3. Split the text into overlapping chunks.
4. Generate embeddings for those chunks.
5. Store chunk records and embeddings in MongoDB Atlas.
6. Ask a question and retrieve relevant chunks.
7. Use Gemini to generate an answer from the retrieved evidence.

The purpose of the repository is not to compare models.
It is to show that knowledge architecture changes answer quality even when the overall pipeline is similar.

## Repository Structure

- [Naive](/home/rud/Documents/Naive): a metadata-blind RAG pipeline
- [Structured](/home/rud/Documents/Structured): a metadata-aware RAG pipeline

Each folder contains:

- source code for ingestion, chunking, retrieval, and generation
- a demo script
- an Atlas vector index definition
- a presentation-oriented demo guide

## What The Two Approaches Show

### Naive

The `Naive` version stores text chunks and embeddings, but does not store structured business metadata on the chunks.

Retrieval is based only on vector similarity.

That means it can find text that is relevant, but it cannot reliably determine:

- which document is active
- which version is current
- which region a rule belongs to
- whether a document is a policy, FAQ, checklist, or procedure

This version is useful to show the limitations of metadata-blind retrieval.

### Structured

The `Structured` version stores metadata with the chunks and allows retrieval to use that metadata.

This enables:

- metadata validation during ingestion
- metadata-based filtering during retrieval
- deterministic preference for the latest valid version
- better grounding for generation

This version is useful to show that better knowledge architecture often matters more than changing the model.

## Main Message

The key point of the repository is:

semantic similarity alone is not enough for enterprise knowledge retrieval.

For high-value questions such as policy, compliance, or operational guidance, the system must also understand business context such as:

- status
- version
- region
- document type

That context usually comes from structured metadata and retrieval rules, not from the LLM guessing correctly.

## How To Run The Demos

Run each implementation independently from its own folder.

### Naive

```bash
cd Naive
python3 scripts/load_to_atlas.py
python3 scripts/run_demo.py
```

Presentation notes:

- [Naive/DEMO_GUIDE.md](/home/rud/Documents/Naive/DEMO_GUIDE.md)
- [Naive/README.md](/home/rud/Documents/Naive/README.md)

### Structured

```bash
cd Structured
python3 scripts/load_to_atlas.py
python3 scripts/run_demo.py --region EU --status Active --doc-type policy
```

Presentation notes:

- [Structured/DEMO_GUIDE.md](/home/rud/Documents/Structured/DEMO_GUIDE.md)
- [Structured/README.md](/home/rud/Documents/Structured/README.md)

## Suggested Presentation Flow

1. Start with the `Naive` guide and explain the basic RAG pipeline.
2. Run the naive ingestion and retrieval flow.
3. Show that semantic retrieval alone can select the wrong evidence.
4. Move to the `Structured` guide and explain the metadata layer.
5. Run the structured ingestion and retrieval flow.
6. Show that the improvement comes from knowledge architecture, not from changing the model family.

## Notes On Metadata Design

The `Structured` example currently demonstrates a dual-validation approach:

- metadata exists inside the source markdown
- metadata also exists in `metadata_manifest.json`
- ingestion validates that they match

That is useful for a demo because it makes the metadata layer visible.

In many enterprise environments, especially PDF-heavy ones, a manifest-only approach is often more practical.
The important design point is not where metadata lives.
The important design point is that metadata is governed and available at retrieval time.
