"""
Main entrypoint for the skincare agent application backend.

This module defines a FastAPI application with endpoints for starting an initial
skin‑concern quiz, processing a face scan, serving a tailored follow‑up
questionnaire, and recommending products based on the scan result and user
answers.  It also demonstrates how to optionally integrate an external LLM
service (e.g. OpenAI) for follow‑up logic.
"""

import json
import os
from typing import List, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .schemas import Question, ScanResult, RecommendRequest

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None  # OpenCV is optional; scanning logic will fall back to dummy

try:
    import openai  # Optional: used to demonstrate LLM‑powered follow‑up logic
except ImportError:
    openai = None


def load_products(path: str) -> List[Dict[str, Any]]:
    """Load the product catalogue from a JSON file.

    Args:
        path: Path to a JSON file containing a list of products.

    Returns:
        A list of dictionaries describing products.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_issues_from_image(file_bytes: bytes) -> List[str]:
    """Placeholder face‑diagnosis routine.

    This function uses OpenCV to decode an image from raw bytes. Real
    implementations could use ML models such as MediaPipe FaceMesh or custom
    classifiers. For the purposes of this scaffold the function simply returns
    a hard‑coded set of issues after confirming the image decodes successfully.

    Args:
        file_bytes: Raw bytes of the uploaded image.

    Returns:
        A list of detected skin issues.
    """
    issues = []
    if cv2 is not None:
        # Attempt to decode the image. We ignore the result, but use failure as
        # a signal to return an error.
        try:
            import numpy as np  # cv2 requires numpy to decode images
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image")
            # Placeholder heuristics: pick some issues based on simplistic
            # properties of the image (mean brightness etc.). This is not
            # medically accurate and should be replaced with real analysis.
            mean_intensity = img.mean()
            if mean_intensity < 100:
                issues.append("dullness")
            if mean_intensity > 180:
                issues.append("oily")
        except Exception:
            # If decoding fails we still return an empty list; real
            # implementations should raise HTTP errors here.
            pass
    # Always include a couple of default issues for demonstration
    issues.extend(["dryness", "acne"])
    # Deduplicate
    return list(dict.fromkeys(issues))


def generate_followup_questions(issues: List[str]) -> List[Question]:
    """Generate a tailored follow‑up questionnaire.

    A simple rule‑based system creates questions based on the detected issues.
    If the OPENAI_API_KEY environment variable is set and the `openai` module
    is available, you could instead call a language model here to generate
    natural language questions.

    Args:
        issues: List of strings describing detected skin issues.

    Returns:
        A list of `Question` objects.
    """
    questions: List[Question] = []
    # Example: map each issue to a specific question
    mapping = {
        "dryness": {
            "text": "On a scale of 1–5, how dry does your skin feel?",
            "type": "number",
        },
        "acne": {
            "text": "Are your breakouts occasional or frequent?",
            "type": "select",
            "options": ["Occasional", "Frequent", "Severe"],
        },
        "redness": {
            "text": "Do you experience redness throughout the day?",
            "type": "select",
            "options": ["Yes", "No"],
        },
        "dullness": {
            "text": "Would you describe your complexion as dull?",
            "type": "select",
            "options": ["Yes", "No"],
        },
        "oily": {
            "text": "How oily does your skin get during the day?",
            "type": "select",
            "options": ["Slightly", "Moderately", "Very"],
        },
    }
    # If the OpenAI API key is set and the module is available, you may use
    # an LLM to generate follow‑up questions. This is purely illustrative and
    # should be replaced with your own logic when using an actual LLM.
    use_llm = False
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and openai is not None:
        use_llm = True
    # In this scaffold we stick with rule‑based logic.
    for issue in issues:
        if issue in mapping:
            meta = mapping[issue]
            questions.append(
                Question(
                    id=issue,
                    text=meta["text"],
                    type=meta.get("type", "text"),
                    options=meta.get("options"),
                )
            )
    return questions


def recommend_products(issues: List[str], answers: Dict[str, Any], products: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """Recommend products based on issues and answers.

    The matching algorithm assigns a simple score to each product: it adds one
    point for every overlap between the product's `concern_tags` and the
    detected issues. Additional heuristics could use the answers to weight
    matches. Products are then sorted by score descending and truncated.

    Args:
        issues: List of detected skin issues.
        answers: A mapping of question identifiers to user responses.
        products: List of available products.
        top_n: Number of products to return.

    Returns:
        A list of up to `top_n` product dictionaries sorted by relevance.
    """
    def score_product(prod: Dict[str, Any]) -> int:
        score = 0
        for tag in prod.get("concern_tags", []):
            if tag in issues:
                score += 1
        # Example: adjust score based on dryness level if provided
        dryness_level = answers.get("dryness")
        if dryness_level and "dryness" in prod.get("concern_tags", []):
            try:
                lvl = int(dryness_level)
                score += lvl  # weight dryness by severity
            except (ValueError, TypeError):
                pass
        return score
    scored = sorted(products, key=score_product, reverse=True)
    return scored[:top_n]


def get_products_path() -> str:
    """Resolve the product file path from an environment variable with fallback."""
    return os.getenv("PRODUCT_FILE_PATH", os.path.join(os.path.dirname(__file__), "data", "products.json"))


app = FastAPI(title="Skincare Agent API")

# Mount the frontend static assets. The React app builds into `frontend/public`.
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.get("/quiz/start", summary="Start the initial skin‑concern questionnaire")
async def quiz_start() -> Dict[str, str]:
    """Return a generic question to begin the consultation."""
    return {"question": "What’s your main skin issue today?"}


@app.post("/scan", response_model=ScanResult, summary="Process an uploaded face image and generate follow‑up questions")
async def scan(file: UploadFile = File(...)) -> ScanResult:
    """Accept a face photo, detect issues and return a tailored questionnaire."""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="No file uploaded")
    issues = detect_issues_from_image(file_bytes)
    questions = generate_followup_questions(issues)
    return ScanResult(issues=issues, questions=questions)


@app.post("/recommend", summary="Recommend skincare products based on scan and answers")
async def recommend(body: RecommendRequest = Body(...)) -> List[Dict[str, Any]]:
    """Return the top matching products given detected issues and user answers."""
    products_path = get_products_path()
    try:
        products = load_products(products_path)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Products file not found at {products_path}")
    recommended = recommend_products(body.issues, body.answers, products)
    return recommended
