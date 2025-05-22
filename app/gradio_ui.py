import gradio as gr
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import openai
import os

load_dotenv()

endpoint = os.environ.get("ELASTIC_ENDPOINT")
api_key = os.environ.get("ELASTIC_API_KEY")

# Set up Elstic client
es = Elasticsearch(
    hosts=endpoint,
    api_key=api_key,
)

openai.api_key = os.environ["OPENAI_API_KEY"]


# --- Elasticsearch RAG search ---
def get_elasticsearch_results(query, index="rag-pdfs"):
    print("get_elasticsearch_results")
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
                "k": 5,
            }
        },
    )
    return response["hits"]["hits"]


# --- Prompt construction ---
def create_prompt_from_results(results):
    context = ""
    for i, hit in enumerate(results, start=1):
        chunk = hit["_source"].get("text", "")
        filename = hit["_source"].get("filename", "")
        page_number = hit["_source"].get("page_number", "")
        chunk = chunk.strip()
        if len(chunk) > 1000:
            chunk = chunk[:1000] + "..."
        context += f"[{i}] {filename} (Page {page_number}):\n{chunk}\n\n"
    prompt = f"""You are an assistant helping with document-based question answering.

Answer the question using only the context below. Cite sources as [1], [2], etc. based on the order provided.
Provide a list of sources at the end of your answer including the file and page number at the end. Inlcude line numbers for specific text references, if applicable.

Context:
{context}
"""
    return prompt, context


# --- OpenAI call ---
def get_openai_completion(prompt, question):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


# --- Combined interface function ---
def answer_question(question):

    results = get_elasticsearch_results(question)
    prompt, context = create_prompt_from_results(results)
    answer = get_openai_completion(prompt, question)
    return answer, context


# --- Gradio UI ---
iface = gr.Interface(
    fn=answer_question,
    inputs=gr.Textbox(
        label="Ask a question", placeholder="Who can prescribe controlled substances?"
    ),
    outputs=[gr.Textbox(label="🧠 Answer"), gr.Textbox(label="📚 Retrieved Context")],
    title="📄 Regulation Assistant (RAG-powered)",
    description="Ask questions based on indexed PDF documents. The assistant retrieves relevant content and answers using OpenAI.",
)

if __name__ == "__main__":
    iface.launch(share=True)
