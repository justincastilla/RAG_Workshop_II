from client import es, pp
from sliding_window_chunking import chunk, display_chunks
from chunking_pdfs import convert_pdf_to_text
from PyPDF2 import PdfReader
import os
from elasticsearch.helpers import bulk
from elasticsearch.helpers import BulkIndexError

import datetime

pdf_dir = "../../pdfs"
pdf_index = "chunked-pdf-index"


def create_chunked_pdf_index():
    if es.indices.exists(index=pdf_index):
        es.indices.delete(index=pdf_index)

    resp = es.indices.create(
        index=pdf_index,
        body={
            "mappings": {
                "properties": {
                    "filename": {"type": "keyword"},
                    "content": {"type": "text"},
                    "text_embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            }
        },
    )
    print(f'pdf-index created: {resp["acknowledged"]}')


def create_inference_endpoint():
    resp = es.inference.put(
        task_type="text_embedding",
        inference_id="pdf_inference_endpoint",
        inference_config={
            "service": "elasticsearch",
            "service_settings": {
                "model_id": ".multilingual-e5-small",
                "num_allocations": 1,
                "num_threads": 1,
            },
        },
    )
    print(f'Inference endpoint created: {resp["acknowledged"]}')

    return resp


def create_embedding_pipeline():
    resp = es.ingest.put_pipeline(
        id="pdf_embedding_pipeline",
        body={
            "description": "Embed PDF chunks using inference endpoint",
            "processors": [
                {
                    "inference": {
                        "model_id": "pdf_inference_endpoint",
                        "input_output": {
                            "input_field": "content",
                            "output_field": "text_embedding",
                        },
                    }
                }
            ],
        },
    )
    print(f'Embedding pipeline created: {resp["acknowledged"]}')
    return resp


def ingest_chunked_pdfs():

    actions = []
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(pdf_dir, filename)
            text = convert_pdf_to_text(filepath)
            chunks = chunk(text)
            for i, chunk_text in enumerate(chunks):
                actions.append(
                    {
                        "_index": pdf_index,
                        "_source": {
                            "filename": filename,
                            "content": chunk_text,
                            "date_created": datetime.datetime.now(),
                        },
                    }
                )

    try:
        bulk(
            es,
            actions,
            pipeline="pdf_embedding_pipeline",
            max_retries=3,
            request_timeout=60 * 3,
        )
    except BulkIndexError as e:
        print("Bulk indexing failed.")
        for error in e.errors:
            print(error)


# create_chunked_pdf_index()
# create_inference_endpoint()
# create_embedding_pipeline()

es.delete_by_query(index=pdf_index, body={"query": {"match_all": {}}}, refresh=True)
print(f"Emptied all documents from index: {pdf_index}")

ingest_chunked_pdfs()
