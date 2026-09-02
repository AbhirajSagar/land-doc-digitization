from typing import List, Optional
from pydantic import BaseModel, Field

class ExtractedField(BaseModel):
    key: str = Field(
        description="Normalized descriptive English field name (e.g. 'owner_name', 'father_name', 'khata_number', 'khasra_number', 'plot_area', 'village', 'tehsil', 'district')."
    )
    value: str = Field(
        description="Extracted value preserved from the document text."
    )
    confidence: float = Field(
        ge=0.0,
        le=100.0,
        description="Confidence score between 0.0 and 100.0 based on OCR clarity and document legibility."
    )


class LandRecordResponse(BaseModel):
    document_type: Optional[str] = Field(
        default=None,
        description="Type of document if identifiable (e.g. 'Khatoni', 'Jamabandi', '7/12 Extract', 'Sale Deed', 'Land Tax Receipt')."
    )
    language: Optional[str] = Field(
        default=None,
        description="Primary language(s) detected in the document (e.g. 'Hindi', 'Marathi', 'English')."
    )
    fields: List[ExtractedField] = Field(
        description="List of extracted key-value fields with confidence scores."
    )


def get_response_schema():
    """Return JSON schema dict for backward compatibility."""
    return {
        "type": "OBJECT",
        "properties": {
            "document_type": {
                "type": "STRING"
            },
            "language": {
                "type": "STRING"
            },
            "fields": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "key": {
                            "type": "STRING"
                        },
                        "value": {
                            "type": "STRING"
                        },
                        "confidence": {
                            "type": "NUMBER"
                        }
                    },
                    "required": [
                        "key",
                        "value",
                        "confidence"
                    ]
                }
            }
        },
        "required": [
            "fields"
        ]
    }
