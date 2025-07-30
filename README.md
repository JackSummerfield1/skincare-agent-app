# Skincare Agent App

This repository contains a full‑stack web application for skin‑diagnosis and product recommendation.

## Backend

- Built with **FastAPI**
- Endpoints:
  - `/quiz/start`: ask a generic skin concern question
  - `/scan`: accept an uploaded image or webcam frame, run a placeholder face‑diagnosis model (MediaPipe FaceMesh / OpenCV) and return detected issues as JSON
  - `/recommend`: given answers and scan data, returns the top products based on the included `products.json`

## Frontend

- Vanilla React (no build tool) served with static HTML
- Components for quiz start, face scan capture/upload, follow‑up questionnaire, and displaying recommended product cards

## DevOps

- Dockerfile for building and running the backend and frontend
- GitHub Actions workflow for linting, testing, building the frontend, and creating a Docker image

Refer to the code and configuration files for details.
