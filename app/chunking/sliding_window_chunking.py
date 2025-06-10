import json
from urllib.request import urlopen

from tabulate import tabulate
from transformers import AutoTokenizer, BertTokenizer

bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
e5_tokenizer = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-base")


SEMANTIC_SEARCH_TOKEN_LIMIT = 510  # 512 minus space for the 2 special tokens
ELSER_TOKEN_OVERLAP = 0.5  # 50% token overlap between chunks is recommended for ELSER


def chunk(
    text, chunk_size=SEMANTIC_SEARCH_TOKEN_LIMIT, overlap_ratio=ELSER_TOKEN_OVERLAP
):
    step_size = round(chunk_size * (1 - overlap_ratio))

    tokens = bert_tokenizer.encode(text)
    tokens = tokens[1:-1]  # remove special beginning and end tokens

    result = []
    for i in range(0, len(tokens), step_size):
        end = i + chunk_size
        chunk = tokens[i:end]
        result.append(bert_tokenizer.decode(chunk))
        if end >= len(tokens):
            break
    return result


def display_chunks(chunks):
    for piece in chunks:
        print("-" * 80)
        print(f"Chunk length: {len(bert_tokenizer.encode(piece))}")
        print(piece[0:100] + "...\n")  # Print first 100 characters of each chunk


def sample_chunk():
    url = "https://raw.githubusercontent.com/elastic/elasticsearch-labs/main/datasets/book_summaries_1000_chunked.json"
    response = urlopen(url)
    book_summaries = json.load(response)

    long_text = book_summaries[0]["synopsis"]

    chunks = chunk(long_text)
    display_chunks(chunks)


# display_chunks(chunks)
