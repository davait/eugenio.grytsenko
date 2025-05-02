# RAG Scorecard Project
Author: Eugenio Grytsenko <yevgry@gmail.com>

This repository implements a Retrieval-Augmented Generation (RAG) pipeline using FAISS for vector storage and either Google Gemini or HuggingFace embeddings. It includes:

* **Ingestion**: Splitting documents into chunks, embedding, and indexing.
* **Evaluation**: Measuring retrieval quality against a question set.
* **Chat App**: FastAPI + React.js front-end, backed by the RAG engine.

---

## 1. Clone the repository

```bash
git clone git@github.com:davait/eugenio.grytsenko.git
cd eugenio.grytsenko/rag_scorecard_project
```

---

## 2. Create and activate a virtual environment

We recommend using Python 3.11 for consistency with tested dependencies.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

* This will create an isolated environment in the `.venv` folder.
* Activating it ensures all packages are installed locally.

---

## 3. Upgrade `pip`

Before installing dependencies, make sure that `pip` is up to date:

```bash
pip install --upgrade pip
```

---

## 4. Install dependencies

Install all required packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

This will pull in:

* Core ML libraries (`torch`, `transformers`, `accelerate`, `sentence-transformers`, `faiss-cpu`)
* RAG orchestration (`llama-index`, `langchain`, `fastapi`, `uvicorn`, etc.)
* Embedding clients (`google-genai`)
* Evaluation tools (`ragas`, `deepeval`, `pandas`, `jsonlines`, `rank-bm25`, `tqdm`)

---

## 5. Ingest documents

Run the ingestion script to:

1. Read all files under a directory
2. Split into 256-token chunks (with 96-token overlap)
3. Embed chunks and build a FAISS index
4. Persist the index and a pickle of raw nodes for BM25

```bash
python ingest.py \
  --input_dir data/sample_docs \
  --index_path data/index.faiss
```

* `--input_dir`: Path to the folder containing your documents.
* `--index_path`: File path where the FAISS index will be written (e.g. `data/index.faiss`).

After completion, you should see:

* `data/index.faiss` and `data/storage/` directory for the llama-index storage context.
* `data/nodes.pkl` containing raw nodes for evaluation.

---

## 6. Evaluate retrieval quality

Given a JSONL of questions, measure how many of the top‑k retrieved chunks contain overlapping tokens with the question.

```bash
python eval/evaluate.py \
  --storage_dir data/storage \
  --nodes_pickle data/nodes.pkl \
  --questions eval/eval_dataset.jsonl \
  --out eval/eval_report.jsonl \
  --top_k 5
```

* `--storage_dir`: The `storage/` directory created by `ingest.py`.
* `--nodes_pickle`: The `nodes.pkl` file from the same run.
* `--questions`: A `.jsonl` file where each line is a JSON object containing a `user_input`, `question`, or `query` field.
* `--out`: Path to write the output JSONL report, with retrieved contexts and precision metrics.
* `--top_k`: (Optional, default 5) number of contexts to retrieve per question.

---

## 7. Launch the chat application

Start the FastAPI service (serves React UI on `/` and RAG chat API on `/chat`):

```bash
uvicorn app:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

Environment variables:

* `GEMINI_API_KEY`: (Optional) your Google Gemini API key. If unset or if `USE_HF_EMBEDDINGS=1`, the app will fall back to HuggingFace embeddings.
* `RAG_TOP_K`: (Optional) number of chunks to retrieve (default 5).
* `USE_HF_EMBEDDINGS`: set to `1` to force offline HuggingFace embeddings.
* `LLM_TEMPERATURE`: (Optional) sampling temperature for the model (default `0.1`).

Then open your browser at [http://localhost:8000](http://localhost:8000).

---

### Notes

* **GPU Usage**: Both ingestion and inference will use GPU if available for FAISS and HuggingFace models. If no GPU, they will fall back to CPU.
* **Embeddings Quota**: If your Google Gemini quota is exhausted, the ingest and app will automatically switch to HuggingFace embeddings.

---

Happy RAG’ing! 🎉
