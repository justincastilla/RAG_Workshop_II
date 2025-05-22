import os
from dotenv import load_dotenv

import glob
import pdfplumber
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "pdfs")
PDF_DIR = os.path.abspath(PDF_DIR)

RAG_INDEX = "rag-pdfs"

endpoint = os.environ.get("ELASTIC_ENDPOINT")
api_key = os.environ.get("ELASTIC_API_KEY")

# Set up Elstic client
es = Elasticsearch(
    hosts=endpoint,
    api_key=api_key,
)

MODEL_ID = ".multilingual-e5-small"
PIPELINE_ID = "e5-ingest-pipeline"


def ensure_e5_model_started():
    try:
        model_stats = es.ml.get_trained_models_stats(model_id=MODEL_ID)
        deployment_state = (
            model_stats["trained_model_stats"][0]
            .get("deployment_stats", {})
            .get("deployment_state", "")
        )

        if deployment_state == "started":
            print("✅ E5 model is already started.")
        else:
            print("🚀 Starting E5 model...")
            es.options(
                ignore_status=[400, 404], request_timeout=60 * 3
            ).ml.start_trained_model_deployment(model_id=MODEL_ID)
            print("⏳ Waiting for model to start...")
            import time

            for _ in range(10):
                time.sleep(2)
                model_stats = es.ml.get_trained_models_stats(model_id=MODEL_ID)
                state = model_stats["trained_model_stats"][0]["deployment_stats"][
                    "state"
                ]

                if state == "started":
                    print("✅ E5 model is now running.")
                    return
            print("⚠️ Timed out waiting for E5 model to start.")
    except Exception as e:
        print(f"❌ Error checking or starting E5 model: {e}")


def create_pipeline_if_needed():
    if not es.options(ignore_status=404).ingest.get_pipeline(id=PIPELINE_ID):
        es.ingest.put_pipeline(
            id=PIPELINE_ID,
            body={
                "processors": [
                    {
                        "inference": {
                            "model_id": MODEL_ID,
                            "input_output": [
                                {"input_field": "text", "output_field": "embedding"},
                            ],
                        }
                    }
                ]
            },
        )


def create_index_if_not_exists():
    print(f"Checking for index {RAG_INDEX}...")
    if not es.indices.exists(index=RAG_INDEX):
        print(f"Index {RAG_INDEX} not found. Creating...")
        resp = es.indices.create(
            index=RAG_INDEX,
            body={
                "mappings": {
                    "properties": {
                        "text": {"type": "text"},
                        "filename": {"type": "keyword"},
                        "page_number": {"type": "integer"},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 384,
                            "index": True,
                            "similarity": "cosine",
                        },
                    }
                }
            },
        )
        print(resp)
    print(f"Index {RAG_INDEX} is ready.")


def load_pdf_pages(pdf_dir):
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    print(f"📂 Found {len(pdf_files)} PDF(s)")
    pages = []
    for path in pdf_files:
        try:
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages):
                    print(f"📄 Reading {path}...")
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append(
                            {
                                "filename": os.path.basename(path),
                                "page_number": i + 1,
                                "text": text.strip(),
                            }
                        )
        except Exception as e:
            print(f"⚠️ Error reading {path}: {e}")
    return pages


def bulk_index_pages(pages):
    actions = []
    for page in pages:
        actions.append({"index": {"_index": RAG_INDEX, "pipeline": PIPELINE_ID}})
        actions.append(page)
    resp = es.options(request_timeout=60 * 3, max_retries=3).bulk(body=actions)
    if resp["errors"]:
        print("⚠️ Some documents failed to index.")
        print(resp)
    else:
        print(f"✅ Successfully indexed {len(pages)} pages.")


def main():
    print("📥 Ingesting PDF pages and generating embeddings with E5...")
    # create_index_if_not_exists()
    # ensure_e5_model_started()
    # create_pipeline_if_needed()
    pages = load_pdf_pages(PDF_DIR)
    if pages:
        bulk_index_pages(pages)
    else:
        print("❌ No valid pages found.")


if __name__ == "__main__":
    main()
