"""
Standalone embedding helper for testing and scripts.
The knowledge_vault package has its own internal copy.
"""

import os
import openai

_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def embed(text: str) -> list[float]:
    """Return a 1536-dim vector for text using text-embedding-3-small."""
    response = _client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding
