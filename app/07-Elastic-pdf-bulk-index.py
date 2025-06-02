from client import es, pp
import base64
import os
import datetime


pdf_dir = "../pdfs"
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]

pdf_index = "pdf-index"

actions = []

# remove all docs from the index
es.delete_by_query(
    index=pdf_index,
    body={"query": {"match_all": {}}},
    refresh=True,  # Refresh the index after deletion
)


for pdf_file in pdf_files:
    with open("../pdfs/" + pdf_file, "rb") as f:

        encoded = base64.b64encode(f.read()).decode("utf-8")
        print("Encoding PDF:", pdf_file)
        actions.append({"index": {"_index": pdf_index}})
        actions.append(
            {
                "data": encoded,
                "filename": pdf_file,
                "date_created": datetime.datetime.now(),
            }
        )

doc_chunk = 5
chunk_count = 0

for i in range(
    0, len(actions), doc_chunk * 2
):  # 2 actions per doc (index + data), so 10 docs = 20 actions
    chunk = actions[i : i + doc_chunk * 2]
    chunk_count += 1
    resp = es.options(request_timeout=60 * 3).bulk(
        body=chunk,
        refresh=True,
        pipeline="pdf_processor",
    )

    print(
        f'{len(resp["items"])} documents indexed in {pdf_index} (chunk {chunk_count})'
    )

print(f'{len(resp["items"])} total documents indexed in {pdf_index}')
