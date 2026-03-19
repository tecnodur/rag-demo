# MongoDB Atlas RAG Demo: Knowledge Architecture Before the Model

This project turns the markdown files in `data/source_docs` into a single Atlas-backed knowledge base for a presentation demo. The data source is the same in both modes. The difference is retrieval discipline:

- Naive RAG uses vector search only and passes only chunk text to generation.
- Structured RAG uses vector search plus metadata filters and a transparent version preference rule.

The intended demo question is:

`What is our password policy for the EU?`

With the provided source documents, naive retrieval can surface the deprecated EU password policy, the active EU password policy, or nearby EU password-related documents. The markdown bodies are intentionally written so that policy currency is carried mainly by metadata, not by obvious prose in the body text. Structured retrieval constrains the search to `region=EU`, `status=Active`, and `doc_type=policy`, then prefers the newest matching version. That should make `password_policy_v3_EU_active.md` the clear winner.

## Project Layout

```text
src/config.py
src/chunker.py
src/embedder.py
src/ingest.py
src/retrieval.py
src/generator.py
src/utils.py
scripts/load_to_atlas.py
scripts/run_demo.py
atlas/knowledge_chunks_vector_index.json
```

## Setup

1. Create a virtual environment and install dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in real values.

```bash
cp .env.example .env
```

Required environment variables:

- `MONGODB_URI`: your Atlas connection string.
- `MONGODB_DB`: defaults to `genai_knowledge_demo`.
- `MONGODB_KNOWLEDGE_ITEMS_COLLECTION`: defaults to `knowledge_items`.
- `MONGODB_KNOWLEDGE_CHUNKS_COLLECTION`: defaults to `knowledge_chunks`.
- `GEMINI_API_KEY`: API key for Gemini.
- `GEMINI_MODEL`: generation model, for example `gemini-2.5-flash`.
- `GEMINI_EMBEDDING_MODEL`: embedding model, for example `gemini-embedding-001`.
- `VECTOR_INDEX_NAME`: Atlas Vector Search index name, defaults to `knowledge_chunks_vector_index`.

## Ingest the Markdown Documents

Run the ingestion script:

```bash
python3 scripts/load_to_atlas.py
```

What it does:

- Loads all markdown files from `data/source_docs`.
- Loads plain markdown files from `data/source_docs`.
- Derives document IDs from file names and titles from the first markdown heading.
- Validates that markdown metadata matches the manifest exactly.
- Stores one source document per file in the `knowledge_items` collection.
- Normalizes the markdown body into plain text.
- Creates deterministic overlapping chunks from the normalized body.
- Generates Gemini embeddings for each chunk.
- Stores chunk embeddings and inherited metadata in `knowledge_chunks`.
- Rewrites [atlas/knowledge_chunks_vector_index.json]( /atlas/knowledge_chunks_vector_index.json) with the actual embedding dimensions detected from the first generated embedding.

## Atlas Vector Index

The vector index definition file is:

[atlas/knowledge_chunks_vector_index.json]( /atlas/knowledge_chunks_vector_index.json)

The ingestion script updates `numDimensions` in that file after embeddings are generated. Apply the index in Atlas manually:

1. Open your Atlas cluster.
2. Go to the database named by `MONGODB_DB`.
3. Open the collection named by `MONGODB_KNOWLEDGE_CHUNKS_COLLECTION`.
4. Open the Search or Atlas Search tab.
5. Create a new Vector Search index.
6. Use JSON editor mode.
7. Paste the contents of [atlas/knowledge_chunks_vector_index.json]( /atlas/knowledge_chunks_vector_index.json).
8. Save the index using the name in `VECTOR_INDEX_NAME`.

Manual Atlas step is required because Atlas Search index creation is operationally sensitive and varies by cluster permissions and Atlas version.

## Run the Demo

Run the naive demo:

```bash
python3 scripts/run_demo.py
```

This uses the default question:

`What is our password policy for the EU?`

It prints:

- Retrieved chunks for naive retrieval.
- The score and chunk preview for each hit.
- Gemini's final answer from the naive retrieval path.
- No metadata is provided to generation, so it can answer from semantically similar but outdated content.

You can also override the question or retrieval limit:

```bash
python3 scripts/run_demo.py --question "What is our password policy for the EU?"
python3 scripts/run_demo.py --limit 8
```

## Expected Demo Outcome

Naive mode:

- Searches the same `knowledge_chunks` collection.
- Uses vector similarity only.
- Passes only chunk text into generation, with no title, version, status, or region metadata.
- Can retrieve semantically similar chunks from both policy versions.
- May also pull in related chunks from onboarding, VPN, or password reset content.
- Can return the 12-character and 90-day-rotation policy if retrieval lands on the deprecated document, because the model cannot tell that it is deprecated.

## Demo Design Note

The EU password policy bodies are intentionally similar. The deprecated and active policy documents differ in the policy rules themselves, but not in prominent prose that says "old" versus "current." That keeps the demo focused on knowledge architecture:

- If retrieval does not use metadata, the system can select the wrong policy text and answer incorrectly.
- This demo intentionally does not use metadata during retrieval or generation.

## Retrieval Logic

Naive retrieval:

- Embeds the user question.
- Runs Atlas `$vectorSearch` with no metadata filters.

This is the demo point: same data and model family, but a metadata-blind knowledge architecture can select the wrong source text.

## Troubleshooting

If ingestion fails:

- Check that each source file is valid markdown.
- Check that each source file has a top-level `#` heading so a stable title can be derived.

If Gemini embedding calls fail:

- Verify `GEMINI_API_KEY`.
- Confirm the embedding model in `GEMINI_EMBEDDING_MODEL` is enabled for your account.
- Make sure outbound network access is available from your environment.

If Atlas vector search returns no results:

- Confirm the vector index has been created on the chunk collection.
- Confirm `VECTOR_INDEX_NAME` matches the Atlas index name exactly.
- Confirm the `numDimensions` value in the Atlas index matches the embedding size written by ingestion.
- Wait for the Atlas index to finish building before running the demo.

If Atlas connection fails:

- Verify `MONGODB_URI`.
- Confirm your IP is allowed in Atlas network access settings.
- Confirm the Atlas user has read and write access to the target database.

If the demo returns unexpected policies:

- Inspect the printed retrieved chunks.
- Re-run ingestion if you changed the source documents.
