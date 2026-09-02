from typing import List, Optional
from pydantic import BaseModel, Field

class ExtractedField(BaseModel):
    key: str = Field(
        description="Normalized descriptive English field name (e.g. 'owner_name', 'father_name', 'khata_number', 'khasra_number', 'plot_area', 'village', 'tehsil', 'district')."
    )
    value: str = Field(
        description="Extracted value preserved from the document text."
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
        description="List of extracted key-value fields."
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
                        }
                    },
                    "required": [
                        "key",
                        "value"
                    ]
                }
            }
        },
        "required": [
            "fields"
        ]
    }
