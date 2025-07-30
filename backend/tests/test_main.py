"""
Unit tests for the FastAPI backend.

These tests validate that the primary endpoints return the expected
responses. They rely on FastAPI's TestClient, which is part of the
starlette.testclient module and does not require an active network.
"""

import io

from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)



def test_quiz_start():
    response = client.get("/quiz/start")
    assert response.status_code == 200
    data = response.json()
    assert "question" in data


def test_scan_endpoint_returns_issues_and_questions():
    # Create a tiny black square as a JPEG to simulate an uploaded image
    import numpy as np
    import cv2

    img = np.zeros((10, 10, 3), dtype=np.uint8)
    retval, buffer = cv2.imencode(".jpg", img)
    assert retval, "Failed to encode test image"
    file_bytes = io.BytesIO(buffer.tobytes())

    files = {"file": ("test.jpg", file_bytes, "image/jpeg")}
    response = client.post("/scan", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert isinstance(data["issues"], list)
    assert "questions" in data
    assert isinstance(data["questions"], list)


def test_recommend_endpoint_returns_products():
    # Send dummy issues and empty answers
    payload = {
        "issues": ["dryness", "acne"],
        "answers": {"dryness": "3"},
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Should return up to 5 products
    assert isinstance(data, list)
    assert 0 <= len(data) <= 5
