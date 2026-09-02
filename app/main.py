from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.lib.preprocessor import preprocess
from app.lib.ocr import extract
from app.lib.llm_postprocess import process_by_llm

app = FastAPI(title="Land Document Processor API")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def is_valid_image(file: UploadFile) -> bool:
    if file.content_type and file.content_type.startswith("image/"):
        return True

    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            return True

    return False

@app.get("/")
async def root():
    return {"message": "Welcome to the Land Document Processor API. Use the /upload endpoint to process images."}

@app.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided in upload."
            )

        if not is_valid_image(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '{file.content_type}'. Only image files ({', '.join(ALLOWED_IMAGE_EXTENSIONS)}) are allowed."
            )

        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty."
            )

        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decode image. Please ensure the file is a valid uncorrupted image."
            )

        processed_image_path = preprocess(image)

        if not processed_image_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to preprocess the image."
            )

        response = extract(processed_image_path)

        if response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract data from the image."
            )

        extracted_data = process_by_llm(
            response,
            processed_image_path
        )

        if not extracted_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process the extracted data."
            )

        return {
            "message": "Image processed successfully.",
            "document_type": extracted_data.get("document_type"),
            "language": extracted_data.get("language"),
            "fields": extracted_data.get("fields", []),
        }


    except HTTPException:
        raise

    except Exception as e:
        print(f"Upload processing error: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the image."
        )