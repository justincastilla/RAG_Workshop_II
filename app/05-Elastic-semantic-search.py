from client import es, pp

endpoint_name = "text-inference-endpoint"
pipeline_id = "text-embedding-pipeline"
index = "text-index"


# search for a document in the index text-index with a given phrase using knn search
def knn_search(index_name, query_text, k=5):
    resp = es.search(
        index=index_name,
        fields=["filename", "text"],
        knn={
            "field": "text_embedding",
            "query_vector_builder": {
                "text_embedding": {
                    "model_id": endpoint_name,
                    "model_text": query_text,
                }
            },
            "k": k,
            "num_candidates": 100,
        },
    )
    return resp


# Run a semantic search using the knn_search function
results = knn_search(index, "Great for campers or cars")
results = results["hits"]["hits"]

# Show the results in a readable format
for result in results:
    print(f"Score: {result['_score']}")
    for field_name, field_value in result["fields"].items():
        print(f"{field_name}: {field_value[0]}")
    print("-" * 50)
