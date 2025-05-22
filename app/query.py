def get_elasticsearch_results(query, index="rag-pdfs"):

    response = es.search(
        index=index,
        query={
            "knn": {
                "field": "embedding",
                "num_candidates": 100,
                "query_vector_builder": {
                    "text_embedding": {
                        "model_id": ".multilingual-e5-small",
                        "model_text": query,
                    }
                },
                "k": 10,
            }
        },
    )

    return response["hits"]["hits"]


def create_prompt_from_results(results):
    context = ""
    for i, hit in enumerate(results, start=1):
        chunk = hit["_source"].get("text", "")
        filename = hit["_source"].get("filename", "")
        page_number = hit["_source"].get("page_number", "")
        context += f"[{i}] {filename} (Page {page_number}):\n"
        context += f"{chunk.strip()}\n\n"

    prompt = f"""You are an assistant helping with document-based question answering.

    Answer the question using only the context below. Cite sources as [1], [2], etc. based on the order provided.
    Provide a list of sources at the end of your answer including the file and page number at the end. Inlcude line numbers for specific text references, if applicable.

    Context:
    {context}
    """
    return prompt


def get_openai_completion(prompt, question):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    from elasticsearch import Elasticsearch
    import openai
    from dotenv import load_dotenv
    import os

    endpoint = os.environ.get("ELASTIC_ENDPOINT")
    api_key = os.environ.get("ELASTIC_API_KEY")

    # Set up Elstic client
    es = Elasticsearch(
        hosts=endpoint,
        api_key=api_key,
    )

    openai.api_key = os.environ["OPENAI_API_KEY"]

    question = input("💬 Ask a question: ")

    results = get_elasticsearch_results(question)
    context_prompt = create_prompt_from_results(results)
    answer = get_openai_completion(context_prompt, question)

    print("\n🧠 Answer:\n", answer)
