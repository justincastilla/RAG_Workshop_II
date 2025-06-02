from client import es

# Delete index if it exists
es.indices.delete(index="text-index", ignore=[400, 404])
# create an index named "text-index"
indices_created = es.options(ignore_status=400).indices.create(
    index="text-index",
    mappings={
        "properties": {
            "text": {"type": "text"},
            "filename": {"type": "keyword"},
        }
    },
)

print(indices_created)  # Print the response from index creation

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

# add documents to the index
for doc in documents:
    added_index = es.index(index="text-index", document=doc)
    print(added_index["_id"])
