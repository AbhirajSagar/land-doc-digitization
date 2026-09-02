def get_response_schema():
    return {
        "type": "OBJECT",
        "properties": {
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