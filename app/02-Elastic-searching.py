from client import es, pp


# search for documents in the "text-index" index that contain the word "value" in the text field
resp = es.search(
    index="text-index",
    query={"match": {"text": "value"}},
)
print("\n\nRaw response from Elasticsearch:")
pp.pprint(resp.body)


print("\n\nSearch results:")
for hit in resp["hits"]["hits"]:
    pp.pprint(
        f"Filename: {hit['_source']['filename']}, Text: {hit['_source']['text']}"
    )  # Print first 100 characters of text
