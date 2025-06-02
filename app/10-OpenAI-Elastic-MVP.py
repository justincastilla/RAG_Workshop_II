from client import es, pp
import os
import dotenv
import openai

dotenv.load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

index = "pdf-index"


# --- OpenAI call ---
def get_openai_completion(prompt, question):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "developer", "content": prompt},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


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


user_query = "Who can prescribe medication in an inpatient health care facility?"

# Run a semantic search using the knn_search function
search_results = knn_search(index, user_query, k=1)
results = search_results["hits"]["hits"]

# Show the results in a readable format
for result in results:
    context = ""
    for field_name, field_value in result["fields"].items():
        context += f"{field_name}: {field_value[0]}\n"

prompt = f"You are a helpful assistant. Here is some information that might be helpful to answer this question: {context}"

results = get_openai_completion(prompt, user_query)
print(user_query)
pp.pprint(results)
