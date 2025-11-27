"""
Prerequisites:

- python (tested in Python 3.11)
- pip install openai

Usage:
- paste this into a new file called example.py
- LLM_API_KEY=<your key here> python example.py
"""

import os

import openai

# Parameters
API_KEY = os.getenv("sk-4UJCbpRTNTx-lvO_4bxNdQ")  # or temporarily hardcode it here
stream = True
model = "claude-3-7-sonnet-20250219-v1-birthright"  # For more options, see: https://ai-incubator-depot.pnnl.gov/#available-models
embedding_model = "text-embedding-3-small-birthright"

# Constants
BASE_URL = "https://ai-incubator-api.pnnl.gov"

# You can use any model here - every Depot model is OpenAI-compatible
client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)


def main():
    print("Fetching model response.")
    user_message = (
        "My friend demands that lights are actually dark sinks,"
        " not light sources. How do I demonstrate they are wrong?"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": user_message,
            }
        ],
        stream=stream,
        stream_options=dict(include_usage=False),
    )

    print("\n\nModel response:")
    if stream:
        for chunk in response:
            print(chunk.choices[0].delta.content, end="")
    else:
        print(response.choices[0].message.content)

    print("\n\nEmbedding of the user message:")
    embedding_response = client.embeddings.create(input=user_message, model=embedding_model)
    print(embedding_response.data[0].embedding)


if __name__ == "__main__":
    main()
