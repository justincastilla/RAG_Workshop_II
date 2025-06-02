from client import es, pp

index = "pdf-index"
question = "Who can prescribe medication in an inpatient health care facility?"


# search for a document in the index text-index with a given phrase using knn search
def knn_search(index_name, query_text, k=5):
    resp = es.search(
        index=index_name,
        fields=["filename", "content"],
        knn={
            "field": "text_embedding",
            "query_vector_builder": {
                "text_embedding": {
                    "model_id": "text-inference-endpoint",
                    "model_text": query_text,
                }
            },
            "k": k,
            "num_candidates": 100,
        },
    )
    return resp


# Run a semantic search using the knn_search function
results = knn_search(index, question, k=1)
results = results["hits"]["hits"]

print(f"Question: {question}\n")
# Show the results in a readable format
for result in results:
    print(f"Score: {result['_score']}\n")
    for field_name, field_value in result["fields"].items():
        print(f"{field_name}: {field_value[0]}")
    print("-" * 50)
