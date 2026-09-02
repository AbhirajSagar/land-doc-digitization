import json
import mimetypes
import os
from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1

from app.lib.credentials import get_credentials


project_id = "land-record-507214"
processor_id = "5d275134eb6f9c0a"
location = "asia-south1"

opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
client = documentai_v1.DocumentProcessorServiceClient(client_options=opts, credentials=get_credentials())
processor_name = client.processor_path(project_id, location, processor_id)

def extract(image_path: str):
    try:
        with open(image_path, "rb") as image:
            image_content = image.read()

        mime_type, _ = mimetypes.guess_type(image_path)
        raw_document = documentai_v1.RawDocument(content=image_content,mime_type=mime_type)
        request = documentai_v1.ProcessRequest(name=processor_name,raw_document=raw_document)
        result = client.process_document(request=request)
        document = result.document

        extracted = []

        for page in document.pages:
            for block in page.blocks:
                layout = block.layout

                text = ""
                if layout.text_anchor.text_segments:
                    for segment in layout.text_anchor.text_segments:
                        start = int(segment.start_index)
                        end = int(segment.end_index)
                        text += document.text[start:end]

                vertices = []

                if layout.bounding_poly.normalized_vertices:
                    for vertex in layout.bounding_poly.normalized_vertices:
                        vertices.append({"x": vertex.x,"y": vertex.y})

                extracted.append({
                    "text": text.strip(),
                    "bounding_box": vertices
                })

        return {
            "text": document.text,
            "blocks": extracted
        }

    except Exception as e:
        print(f"Document AI extraction error: {e}")
        return None