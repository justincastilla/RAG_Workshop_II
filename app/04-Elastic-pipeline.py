from client import es, pp

endpoint_name = "text-inference-endpoint"
pipeline_id = "text-embedding-pipeline"
index = "text-index"


# create an ingest pipeline for text embedding with text-inference-endpoint for the index text-index
def create_ingest_pipeline(pipeline_name, endpoint_name):
    resp = es.ingest.put_pipeline(
        id=pipeline_name,
        body={
            "description": "Embed text using inference endpoint",
            "processors": [
                {
                    "inference": {
                        "model_id": endpoint_name,
                        "input_output": {
                            "input_field": "text",
                            "output_field": "text_embedding",
                        },
                    }
                }
            ],
        },
    )
    return resp


# simulate the pipeline to see how it processes a sample document
def simulate_pipeline(pipeline_name, index_name):
    resp = es.ingest.simulate(
        id=pipeline_name,
        docs=[
            {
                "_index": index_name,
                "_source": {
                    "text": "This is a sample text for embedding.",
                    "filename": "sample.txt",
                },
            }
        ],
    )
    return resp


# set the pipeline for the index text-index
try:
    # Check if the pipeline already exists
    es.ingest.get_pipeline(id=pipeline_id)
    print(f"Pipeline '{pipeline_id}' already exists, skipping creation.")
except Exception as e:
    print(f"Pipeline '{pipeline_id}' does not exist, creating it...")
    # create the pipeline if it does not exist
    new_pipeline = create_ingest_pipeline(pipeline_id, endpoint_name)
    print("Pipeline creation response:\n")
    pp.pprint(new_pipeline.body)

# Run a simulation of the pipeline to see how it processes a sample document
test = simulate_pipeline(pipeline_id, index)
print("Simulated response from the pipeline:\n")
pp.pprint(test.body)


# Set the new pipeline as default for the index text-index
default_set = es.indices.put_settings(
    index="text-index", settings={"default_pipeline": pipeline_id}
)["acknowledged"]

print(f"\nIndex set with default pipeline '{pipeline_id}': {default_set}")

# Create 5 sample documents, each containign a filename and some text about a random product for sale
documents = [
    {
        "filename": "product1.txt",
        "text": "This is a great product for your needs. I was able to save time and money with this object.",
    },
    {
        "filename": "product2.txt",
        "text": "This product is perfect for everyday use. I even bought one for my boat and RV.",
    },
    {
        "filename": "product3.txt",
        "text": "Experience the best quality with this product.",
    },
    {
        "filename": "product4.txt",
        "text": "Affordable and reliable, this product won't disappoint.",
    },
    {
        "filename": "product5.txt",
        "text": "Get the best value for your money with this amazing product.",
    },
]

# add documents to the index using the pipeline
for doc in documents:
    added_index = es.index(index=index, document=doc)
    print(f"Document added with ID: {added_index['_id']}")

