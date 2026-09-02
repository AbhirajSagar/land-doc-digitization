from google import genai
from google.genai.types import HttpOptions, Part, GenerateContentConfig
import json

from app.lib.credentials import get_credentials
from app.lib.prompt import create_prompt
from app.lib.schema import get_response_schema

client = genai.Client(vertexai=True, project="land-record-507214", location="global", credentials=get_credentials(), http_options=HttpOptions(api_version="v1"))

def process_by_llm(text: str, img_path: str):
    with open(img_path, "rb") as f:
        image_data = f.read()

    chat = client.chats.create(
        model="gemini-3.5-flash",
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=get_response_schema()
        )
    )

    response = chat.send_message([
        Part.from_bytes(data=image_data,mime_type="image/jpeg"),
        create_prompt(text)
    ])

    return json.loads(response.text)