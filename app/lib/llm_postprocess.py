import json
import logging
import mimetypes
import os
from typing import Any, Dict, Union

from google import genai
from google.genai.types import (
    AutomaticFunctionCallingConfig,
    GenerateContentConfig,
    HttpOptions,
    Part,
)

from app.lib.credentials import get_credentials
from app.lib.prompt import SYSTEM_INSTRUCTION, create_prompt
from app.lib.schema import LandRecordResponse

logger = logging.getLogger(__name__)

_genai_client = None


def get_genai_client() -> genai.Client:
    """Lazily initialize and return the Google GenAI Client."""
    global _genai_client
    if _genai_client is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "land-record-507214")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        _genai_client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
            credentials=get_credentials(),
            http_options=HttpOptions(api_version="v1"),
        )
    return _genai_client


def get_image_mime_type(img_path: str) -> str:
    """Guess the MIME type of the given image file path with fallback."""
    mime_type, _ = mimetypes.guess_type(img_path)
    if not mime_type or not mime_type.startswith("image/"):
        if img_path.lower().endswith(".png"):
            return "image/png"
        elif img_path.lower().endswith((".jpg", ".jpeg")):
            return "image/jpeg"
        elif img_path.lower().endswith(".webp"):
            return "image/webp"
        return "image/png"
    return mime_type


def process_by_llm(ocr_data: Union[str, Dict[str, Any]], img_path: str) -> Dict[str, Any]:
    """
    Extract structured land record information using multimodal Gemini.

    Args:
        ocr_data: Extracted OCR text or dictionary containing blocks and text.
        img_path: Path to the preprocessed document image.

    Returns:
        Structured dictionary containing extracted fields and document metadata.
    """
    client = get_genai_client()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Read image binary
    with open(img_path, "rb") as f:
        image_data = f.read()

    mime_type = get_image_mime_type(img_path)
    image_part = Part.from_bytes(data=image_data, mime_type=mime_type)
    prompt_text = create_prompt(ocr_data)

    config = GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=LandRecordResponse,
        temperature=0.1,
        automatic_function_calling=AutomaticFunctionCallingConfig(disable=True),
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[image_part, prompt_text],
            config=config,
        )

        # 1. Check if parsed Pydantic object is available
        if hasattr(response, "parsed") and response.parsed is not None:
            if isinstance(response.parsed, LandRecordResponse):
                return response.parsed.model_dump()
            elif hasattr(response.parsed, "model_dump"):
                return response.parsed.model_dump()

        # 2. Fallback to parsing response.text
        if response.text:
            text = response.text.strip()
            # Strip markdown fences if present
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())

        raise ValueError("Empty response received from LLM.")

    except Exception as e:
        logger.error(f"LLM post-processing extraction failed: {e}", exc_info=True)
        raise