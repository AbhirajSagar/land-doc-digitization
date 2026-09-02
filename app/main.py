import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import uuid

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.lib.preprocessor import preprocess
from app.lib.ocr import extract
from app.lib.llm_postprocess import process_by_llm

DOCUMENTS_DIR = Path("uploads/documents")
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Land Document Processor API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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


@app.post("/documents", status_code=status.HTTP_201_CREATED)
async def save_document(
    request: Request,
    file: UploadFile = File(..., description="Document image file"),
    json_data: str = Form(..., description="JSON string containing document data"),
):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided for image upload."
            )

        if not is_valid_image(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '{file.content_type}'. Only image files ({', '.join(ALLOWED_IMAGE_EXTENSIONS)}) are allowed."
            )

        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded image file is empty."
            )

        try:
            parsed_json = json.loads(json_data)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON string in 'json_data' field: {exc.msg}"
            )

        doc_id = str(uuid.uuid4())
        doc_folder = DOCUMENTS_DIR / doc_id
        doc_folder.mkdir(parents=True, exist_ok=True)

        safe_filename = Path(file.filename).name
        ext = Path(file.filename).suffix.lower()
        if not ext or ext not in ALLOWED_IMAGE_EXTENSIONS:
            ext = ".png"

        stored_image_filename = f"image{ext}"
        image_path = doc_folder / stored_image_filename
        with open(image_path, "wb") as f:
            f.write(image_bytes)

        created_at = datetime.now(timezone.utc).isoformat()
        content_type = file.content_type or mimetypes.guess_type(safe_filename)[0] or "image/png"

        record = {
            "id": doc_id,
            "original_filename": safe_filename,
            "stored_image_filename": stored_image_filename,
            "content_type": content_type,
            "created_at": created_at,
            "json_data": parsed_json,
        }

        metadata_file_path = doc_folder / "metadata.json"
        with open(metadata_file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        base_url = str(request.base_url).rstrip("/")
        image_url = f"{base_url}/documents/{doc_id}/image"

        return {
            "message": "Document image and JSON saved successfully.",
            "id": doc_id,
            "filename": safe_filename,
            "image_url": image_url,
            "created_at": created_at,
            "json_data": parsed_json,
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Save document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while saving the document."
        )


@app.get("/documents")
async def list_documents(request: Request):
    try:
        base_url = str(request.base_url).rstrip("/")
        documents = []

        if DOCUMENTS_DIR.exists():
            for doc_folder in DOCUMENTS_DIR.iterdir():
                if not doc_folder.is_dir():
                    continue

                doc_id = doc_folder.name
                metadata_path = doc_folder / "metadata.json"
                image_url = f"{base_url}/documents/{doc_id}/image"

                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)

                        documents.append({
                            "id": meta.get("id", doc_id),
                            "filename": meta.get("original_filename", ""),
                            "image_url": image_url,
                            "created_at": meta.get("created_at", ""),
                            "json_data": meta.get("json_data") if "json_data" in meta else meta.get("data", {}),
                        })
                    except Exception as e:
                        print(f"Failed to load metadata for document {doc_id}: {e}")
                        documents.append({
                            "id": doc_id,
                            "filename": "",
                            "image_url": image_url,
                            "created_at": "",
                            "json_data": {},
                        })
                else:
                    image_files = [f for f in doc_folder.iterdir() if f.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS]
                    filename = image_files[0].name if image_files else ""
                    documents.append({
                        "id": doc_id,
                        "filename": filename,
                        "image_url": image_url,
                        "created_at": "",
                        "json_data": {},
                    })

        documents.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return {
            "total": len(documents),
            "documents": documents,
        }

    except Exception as e:
        print(f"List documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving documents."
        )


@app.get("/documents/{document_id}")
async def get_document(document_id: str, request: Request):
    doc_folder = DOCUMENTS_DIR / document_id
    if not doc_folder.exists() or not doc_folder.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    metadata_path = doc_folder / "metadata.json"
    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/documents/{document_id}/image"

    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            return {
                "id": meta.get("id", document_id),
                "filename": meta.get("original_filename", ""),
                "image_url": image_url,
                "created_at": meta.get("created_at", ""),
                "json_data": meta.get("json_data") if "json_data" in meta else meta.get("data", {}),
            }
        except Exception as e:
            print(f"Error reading metadata for {document_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read document metadata."
            )

    return {
        "id": document_id,
        "filename": "",
        "image_url": image_url,
        "created_at": "",
        "json_data": {},
    }


@app.get("/documents/{document_id}/image")
async def get_document_image(document_id: str):
    doc_folder = DOCUMENTS_DIR / document_id
    if not doc_folder.exists() or not doc_folder.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    metadata_path = doc_folder / "metadata.json"
    image_filename = None
    media_type = None
    download_filename = None

    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                image_filename = meta.get("stored_image_filename")
                media_type = meta.get("content_type")
                download_filename = meta.get("original_filename")
        except Exception as e:
            print(f"Error reading metadata for image of {document_id}: {e}")

    if image_filename:
        image_path = doc_folder / image_filename
    else:
        image_files = [f for f in doc_folder.iterdir() if f.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS]
        if not image_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image file not found for this document."
            )
        image_path = image_files[0]

    if not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found."
        )

    if not media_type:
        media_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"

    return FileResponse(
        path=str(image_path),
        media_type=media_type,
        filename=download_filename or image_path.name
    )