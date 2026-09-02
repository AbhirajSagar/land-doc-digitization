def create_prompt(ocr_output: str):
    return f"""
        You are an intelligent document information extraction system.

        Analyze the provided document image together with the OCR output.

        Your task is to identify and extract ALL MEANINGFUL structured information
        present in the document.

        The documents may have completely different structures and fields.
        Do NOT assume that every document contains the same fields.

        Rules:
        - Extract only information that is actually present in the document.
        - Do not invent, infer, or hallucinate missing information.
        - Create descriptive, normalized English field names.
        - Preserve the original value as written in the document whenever possible.
        - Use the document image to verify or correct OCR mistakes when possible.
        - Use the OCR bounding boxes and spatial relationships to understand labels
        and their corresponding values.
        - Ignore obvious OCR noise, stamps, decorative text, and irrelevant text.
        - If a value is uncertain, still extract it but lower its confidence.
        - Do not create fields for information that is not present.
        - Return ONLY valid JSON.

        OCR OUTPUT:
        {ocr_output}
        """