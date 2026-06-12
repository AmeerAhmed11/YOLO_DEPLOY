
# MISSION PRD: End-to-End Deployment of YOLO TensorRT (best.engine) on Google Cloud Vertex AI with Web UI
## 1. Executive Summary & Objective
The goal of this mission is to successfully host a pre-trained YOLO object detection model, compiled as a TensorRT engine (best.engine), on Google Cloud Vertex AI using a custom serving container. Additionally, you will build a sleek, user-friendly frontend web interface that allows users to upload images or videos, send them to the deployed Vertex AI endpoint, and visually display the bounding boxes and inference results in real-time.
## 2. Your Persona & Scope of Work (Antigravity)
As Antigravity, an autonomous software engineering agent, you are fully responsible for the research, architecture, configuration, and implementation of this pipeline.
 * No code will be provided to you. You must conduct your own research regarding Google Cloud Platform (GCP) SDKs, Vertex AI custom container specifications, and modern frontend frameworks.
 * You are expected to design a robust plan, handle edge cases (especially environment compatibility for TensorRT), and deliver a production-ready solution.
## 3. Core Requirements & Milestones
### Phase 1: Technical Research & Environment Alignment
 * TensorRT Dependency Mapping: Investigate the specific GPU, CUDA, and TensorRT version used to compile the best.engine file. You must ensure that the Vertex AI prediction node (e.g., NVIDIA T4, V100, or A100) and the base Docker image match these exact specifications to avoid hardware incompatibility errors.
 * Vertex AI Custom Serving Standards: Research Vertex AI requirements for custom containers. Specifically, understand how Vertex AI handles health checks (/health) and prediction requests (/predict), including the required JSON request/response structures.
### Phase 2: Model Packaging & API Wrapping
 * Inference Server: Create a lightweight web server (e.g., FastAPI or Flask) inside a custom container. It must load best.engine using the appropriate libraries (like ultralytics or tensorrt) and expose the required HTTP endpoints.
 * Payload Handling: Standardize the API to accept incoming media (optimized via Base64 or multipart streaming) and return clean, structured JSON containing bounding boxes, class names, and confidence scores.
 * Containerization: Write a optimized Dockerfile utilizing a GPU-accelerated base image (e.g., NVIDIA CUDA or Ultralytics GPU images) and prepare it for Google Artifact Registry.
### Phase 3: GCP Cloud Infrastructure Setup
 * Image Registry: Orchestrate the process of pushing the container image to GCP Artifact Registry or Container Registry.
 * Vertex AI Model Registry: Register the custom container as a deployable model asset.
 * Endpoint Deployment: Deploy the model to a Vertex AI Endpoint with the appropriate GPU accelerator configuration, ensuring minimum and maximum autoscaling parameters are considered.
### Phase 4: User Interface Development (The Frontend)
 * The Web UI: Build a clean, modern, and highly intuitive web dashboard (using Streamlit, Gradio, or a web framework of your choice).
 * Media Upload: Support both static image uploads (PNG/JPG) and video file uploads.
 * Inference Rendering:
   * For images: Display the original image with clearly drawn bounding boxes, labels, and percentages over the detected objects.
   * For videos: Process the video frames, run inference via the Vertex AI endpoint, and display the annotated video playback or a downloadable processed video file.
   * GCP Integration: Securely connect the frontend to the Vertex AI endpoint using official Google Cloud client libraries.
## 4. Key Technical Constraints
 * Zero Pre-baked Code: You must generate all Dockerfiles, server scripts, deployment manifests, and UI codes from scratch based on your own internal knowledge and updated research.
 * Latency Optimization: Because TensorRT is built for high performance, ensure that the preprocessing (image resizing/normalization) and postprocessing (Non-Maximum Suppression) are optimized to minimize latency.
 * Cost Efficiency: Configuration scripts should ensure resources scale down or alert the user on potential idling costs where applicable.
## 5. Definition of Done (Success Criteria)
 1. Successful Verification: The /health check route passes successfully within the Vertex AI ecosystem.
 2. Live Endpoint: A working Vertex AI endpoint URL capable of receiving data and returning accurate JSON predictions from the best.engine model.
 3. Functional UI: A beautifully designed web interface where a user can drag and drop an image or a video, click "Run Inference", and visually witness the YOLO model's predictions rendered cleanly on the screen.
 4. Documentation: A concise markdown file explaining how to launch the frontend and any environment variables required (e.g., GCP Credentials).
Please begin by presenting your step-by-step research findings, your architectural plan, and your technical stack choice before initiating code generation.