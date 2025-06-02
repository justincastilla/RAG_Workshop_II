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


question = "Who can prescribe medication in an inpatient health care facility?"

results = get_openai_completion("You are a helpful assistant.", question)
pp.pprint(results)
