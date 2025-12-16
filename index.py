from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
import cv2
import numpy as np
from PIL import Image
import os
import uuid
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes

app = FastAPI()

# Render cần bind host 0.0.0.0
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://prepress-tooling.vercel.app",
        "http://localhost:5173"  # nếu dev bằng Vite
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = "/tmp/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================
# XỬ LÝ ẢNH
# ==========================

def pdf_to_image(upload: UploadFile):
    pdf_bytes = upload.file.read()
    images = convert_from_bytes(pdf_bytes, dpi=300)
    return images[0]

def normalize_image(img, size=(3000, 3000)):
    img = img.convert("L")
    img = img.resize(size)
    return np.array(img)

def extract_edges(img):
    return cv2.Canny(img, 50, 150)

def highlight_missing_content(img1, img2):
    diff = cv2.subtract(img1, img2)
    _, mask = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)

    kernel = np.ones((5,5), np.uint8)
    mask_dilated = cv2.dilate(mask, kernel, 1)

    color = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR)
    color[mask_dilated > 0] = [0, 0, 255]

    contours, _ = cv2.findContours(
        mask_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    return color, len(contours)

# ==========================
# API
# ==========================

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/api/compare")
async def compare_images(
    goc: UploadFile = File(...),
    cheban: UploadFile = File(...)
):
    try:
        img1_pdf = pdf_to_image(goc)
        img2_pdf = pdf_to_image(cheban)

        img1 = normalize_image(img1_pdf)
        img2 = normalize_image(img2_pdf)

        edges1 = extract_edges(img1)
        edges2 = extract_edges(img2)

        diff = cv2.absdiff(edges1, edges2)
        diff_points = int(np.count_nonzero(diff))

        if diff_points == 0:
            return {"status": "ok", "changed": False}

        highlight, regions = highlight_missing_content(img1, img2)

        filename = f"{uuid.uuid4()}.png"
        path = os.path.join(OUTPUT_DIR, filename)
        cv2.imwrite(path, highlight)

        return {
            "status": "changed",
            "changed": True,
            "regions": regions,
            "image_url": f"/api/image/{filename}"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/image/{name}")
def get_image(name: str):
    path = os.path.join(OUTPUT_DIR, name)
    return FileResponse(path, media_type="image/png")
