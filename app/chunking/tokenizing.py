import json
from urllib.request import urlopen

from tabulate import tabulate
from transformers import AutoTokenizer, BertTokenizer

bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
e5_tokenizer = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-base")


def whitespace_tokenize(text):
    return text.split()


url = "https://raw.githubusercontent.com/elastic/elasticsearch-labs/main/notebooks/search/movies.json"
response = urlopen(url)
movies = json.load(response)


def count_tokens(text):
    whitespace_tokens = len(whitespace_tokenize(text))
    bert_tokens = len(bert_tokenizer.encode(text))
    e5_tokens = len(e5_tokenizer.encode(text))
    return [whitespace_tokens, bert_tokens, e5_tokens, f"{text[:80]}..."]


counts = [count_tokens(movie["plot"]) for movie in movies]

# print(tabulate(sorted(counts), ["whitespace", "BERT", "E5", "text"]))

example_movie = movies[0]["plot"]
print(example_movie)
print()

movie_tokens = bert_tokenizer.encode(example_movie)
print(str([bert_tokenizer.decode([t]) for t in movie_tokens]))
