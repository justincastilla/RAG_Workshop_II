from client import es, pp
import base64
import datetime


sample_pdf = "../pdfs/WAC_246_-337_-001.pdf"
pdf_index = "pdf-index"
endpoint_name = "text-inference-endpoint"
pdf_pipeline = "pdf_processor"


def create_pdf_index():
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


def pdf_processing_pipeline():
    resp = es.ingest.put_pipeline(
        id="pdf_processor",
        description="Extract attachment information from PDF and embed text",
        processors=[
            # handle the PDF attachment and convert to text
            {
                "attachment": {
                    "field": "data",
                    # send the PDF extracted data to attachment
                    "target_field": "attachment",
                    "indexed_chars": -1,
                    "remove_binary": False,
                }
            },
            # move the content from attachment.content to content field
            {"rename": {"field": "attachment.content", "target_field": "content"}},
            # remove unnecessary fields from the attachment
            {
                "remove": {
                    "field": [
                        "data",
                        "attachment.content_type",
                        "attachment.modified",
                        "attachment.creator_tool",
                        "attachment.format",
                        "attachment.metadata_date",
                    ]
                }
            },
            # embed the content using the inference endpoint
            {
                "inference": {
                    "model_id": endpoint_name,
                    "input_output": {
                        "input_field": "content",
                        "output_field": "text_embedding",
                    },
                }
            },
        ],
    )
    print(f'pdf_processing_pipeline created: {resp["acknowledged"]}')


def simulate_pdf_pipeline(doc):
    # Simulate the pipeline to see how it processes a sample PDF document

    resp = es.ingest.simulate(
        id=pdf_pipeline,
        docs=[{"_index": pdf_index, "_source": doc}],
    )
    pp.pprint(resp.body)


# read the sample PDF file and encode it in base64 for testing and embedding
with open(sample_pdf, "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")

doc = {
    "data": encoded,
    "filename": sample_pdf.split("/")[-1],
    "date_created": datetime.datetime.now(),
}

create_pdf_index()
pdf_processing_pipeline()
simulate_pdf_pipeline(doc)

# Uncomment the following lines to set the pipeline as default for the index
# Set the new pipeline as default for the index pdf-index
default_set = es.indices.put_settings(
    index=pdf_index, settings={"default_pipeline": pdf_pipeline}
)["acknowledged"]

print(f"\nIndex set with default pipeline '{pdf_pipeline}': {default_set}")

# Index the document using the pipeline
embedded_pdf = es.index(index=pdf_index, document=doc)

print(f"document status: {embedded_pdf.body['result']}")
