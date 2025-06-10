from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError

import openai
import os
from dotenv import load_dotenv
import pprint

load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]

# set up pretty printing for better readability of output
pp = pprint.PrettyPrinter(compact=True, width=80)

# Connect to Elasticsearch instance
es = Elasticsearch(
    hosts=os.environ.get("ELASTIC_ENDPOINT"),
    api_key=os.environ.get("ELASTIC_API_KEY"),
)
