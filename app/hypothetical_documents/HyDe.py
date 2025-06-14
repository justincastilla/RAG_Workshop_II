from client import es, bulk, BulkIndexError, pp, openai
import csv
import json


index_name = "hyde_index"


def get_ai_completion(prompt):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return completion


def generate_prompt(row):
    prompt = f'Create a detailed query profile written from a customers perspective describing what they are looking for when shopping for this exact item. Include key characteristics like type, features, use cases, quality aspects, materials, specific price range, an appropriate age for the user, and target user. Focus on aspects a shopper would naturally mention in their search query. \nFormat: descriptive text without bullet points or sections. \nExample: "Looking for a high-end lightweight carbon fiber road bike for competitive racing with electronic gear shifting and aerodynamic frame design suitable for experienced cyclists who value performance and speed." Describe this product in natural language that matches how real customers would search for it. Make sure to mention the target age and a close approximation of the price to a whole number in the output text somewhere. Here are the product details: \nProduct Name: {row["product_name"]} \nAbout Product: {row["product_description"]} \nPrice: {row["price"]} \nTarget Age: {row["target_age"]}'

    return prompt


def export_toys_to_json():
    # Path to the CSV file
    csv_file_path = "./toys.csv"
    updated_toys = []
    # Open the CSV file and iterate through each row
    with open(csv_file_path, mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            price = row["price"]
            product_name = row["product_name"]
            product_description = row["product_description"]
            target_age = row["target_age"]

            prompt = generate_prompt(row)

            ai_response = get_ai_completion(prompt)
            raw_query_profile = ai_response.choices[0].message.content
            row["raw_query_profile"] = raw_query_profile
            updated_toys.append(row)

        # Write the updated toys list to a JSON file
        with open("toys.json", "w") as f:
            json.dump(updated_toys, f, indent=2)


def create_index():
    mappings = {
        "mappings": {
            "properties": {
                "product_name": {"type": "text"},
                "product_description": {"type": "text"},
                "price": {"type": "float"},
                "target_age": {"type": "integer"},
                "query_profile": {"type": "sparse_vector"},
                "raw_query_profile": {"type": "text"},
            }
        }
    }

    # Check if the index already exists
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=mappings)
        print(f"Index '{index_name}' created successfully.")
    else:
        print(f"Index '{index_name}' already exists.")


def create_ingest_pipeline():
    resp = es.ingest.put_pipeline(
        id="hyde_pipeline",
        body={
            "description": "Embed hyde using inference endpoint",
            "processors": [
                {
                    "inference": {
                        "model_id": "elser_model_2_endpoint",
                        "input_output": {
                            "input_field": "raw_query_profile",
                            "output_field": "query_profile",
                        },
                    }
                }
            ],
        },
    )
    print(f'Embedding pipeline created: {resp["acknowledged"]}')
    return resp


def create_inference_endpoint():
    resp = es.inference.put(
        task_type="sparse_embedding",
        inference_id="elser_model_2_endpoint",
        inference_config={
            "service": "elser",
            "service_settings": {"num_allocations": 1, "num_threads": 1},
        },
    )
    print(resp)


def load_index():
    # Load and index the toys data
    with open("toys.json", "r") as f:
        toys_data = json.load(f)

    def generate_actions():
        for toy in toys_data:
            yield {
                "_index": index_name,
                "_source": toy,
                "pipeline": "elser-v2",
            }

    try:
        success, failed = bulk(
            es,
            generate_actions(),
            max_retries=3,
            request_timeout=60 * 3,
        )
        print(f"Successfully indexed {success} documents")
        if failed:
            print(f"Failed to index {len(failed)} documents")
    except BulkIndexError as e:
        print(f"Error during bulk indexing: {e}")


def find_a_toy(query_string):
    # Search the toys index using the ELSER embedding model
    # Limit results to 3
    resp = es.search(
        index=index_name,
        body={
            "size": 3,
            "query": {
                "sparse_vector": {
                    "field": "query_profile",
                    "inference_id": "elser_model_2_endpoint",
                    "query": query_string,
                }
            },
            "fields": ["product_name", "product_description", "price", "target_age"],
        },
    )
    print("Search results:")
    for hit in resp["hits"]["hits"]:
        print(f"Product Name: {hit['_source']['product_name']}")
        print(f"Description: {hit['_source']['product_description']}")
        print(f"Price: ${hit['_source']['price']}")
        print(f"Target Age: {hit['_source']['target_age']}")
        print("-" * 40)


def add_one_toy(toy):
    prompt = generate_prompt(toy)
    ai_response = get_ai_completion(prompt)
    print("AI Response:", ai_response.choices[0].message.content)
    toy["raw_query_profile"] = ai_response.choices[0].message.content

    try:
        resp = es.index(index=index_name, body=toy, pipeline="elser-v2")
        print(resp)
    except IndexError as e:
        print(e)


def delete_index():
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"Index '{index_name}' deleted successfully")
    else:
        print(f"Index '{index_name}' does not exist")


export_toys_to_json()
# delete_index()
# create_inference_endpoint()
# create_ingest_pipeline()
# create_index()
# load_index()

he_man = {
    "product_name": "Battle Armor He-Man",
    "product_type": "Action Figure",
    "franchise": "Masters of the Universe",
    "year_released": 1983,
    "condition": "excellent",
    "price": 132.99,
    "original_packaging": False,
    "complete_set": False,
    "target_age": 7,
    "product_description": "This Battle Armor He-Man figure is an icon from the original Masters of the Universe line, showcasing the hero in his legendary battle gear. The rotating chest plate reveals different levels of damage, making every skirmish more intense. It’s a nostalgic piece that captures He-Man’s indomitable spirit and looks amazing on display.",
    "included_accessories": [
        "Battle Axe",
        "Battle Sword",
        "Weapon Sheath",
        "Battle-Damage Chest Piece",
    ],
}

add_one_toy(he_man)

toy_query = "I'm looking for the classic He-man action figure toy from the 80s with a muscular build and a sword. He had a neat trick where his chest would get battle damage if it was pressed down upon. I'm willing to pay around $100 to $150 dollars. It's uhh... for my 7 year old's birthday. Sure. That's it."
query_response = find_a_toy(toy_query)
