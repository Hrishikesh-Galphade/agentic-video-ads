# Agentic Video Ads

**`agentic-video-ads`** is a sophisticated, end-to-end platform for automatically generating 30-second video advertisements from a single text prompt. This project is built on a robust, scalable, and asynchronous microservice architecture, leveraging multiple specialized AI agents to orchestrate the entire video production pipeline from creative conception to final rendering.

The system uses a multi-agent workflow where a central **Orchestrator Agent** manages and delegates tasks to specialized agents for creative planning, asset generation, and post-production, demonstrating a powerful pattern for building complex, real-world AI applications.

---

## Features

-   **Prompt-to-Video**: Generate a complete 30-second video ad from a single natural language prompt.
-   **AI-Powered Creative Direction**: Utilizes Google's Gemini Pro to generate a professional script and a detailed, scene-by-scene storyboard.
-   **Generative Video Clips**: Leverages Google's state-of-the-art Veo model to create high-quality video clips for each scene in the storyboard.
-   **Asynchronous & Scalable**: Built on a message queue (RabbitMQ) and a task-based worker system (Celery), allowing for parallel processing of long-running tasks like video generation.
-   **Resilient by Design**: Incorporates automatic retries with exponential backoff for handling API rate limits, and healthchecks to ensure a stable startup sequence.
-   **Fully Containerized**: The entire application stack is containerized with Docker and orchestrated with Docker Compose for easy setup and deployment.

---

## System Architecture

This project is designed as a **Hybrid Agentic Microservices Model**. It combines the scalability and resilience of a microservices pattern with a powerful, stateful workflow engine (LangGraph) for intelligent, centralized orchestration.

### Architectural Diagram

```
+----------------+      +----------------+      +---------------------------+
|                |      |                |      |                           |
|   End User /   |----->|   API Gateway  |----->|   Orchestrator Service    |
|      UI        |      | (Nginx)        |      | (FastAPI + LangGraph)     |
|                |      |                |      |                           |
+----------------+      +----------------+      +-------------+-------------+
                                                              | (Sync REST Call)
                                                              |
                                                +-------------v-------------+
                                                |                           |
                                                | Creative Director Service |
                                                | (Gemini Pro for Scripting)|
                                                |                           |
                                                +---------------------------+

+---------------------------+      +---------------------------+      +----------------------------+
|     State Database        |      |     Message Queue         |      |     Cloud Object Storage   |
| (PostgreSQL)              |<---->| (RabbitMQ)                |<---->|   (MinIO)                  |
|  - Stores job status      |      |  - Asynchronous task jobs |      |    - Stores video assets   |
+---------------------------+      +-------------+-------------+      +----------------------------+
                                                 | (Async Celery Tasks)
                               +-----------------v-----------------+-----------------v------------------+
                               |                                   |                                    |
+---------------------------+  |  +---------------------------+  |  +---------------------------+
|                           |  |  |                           |  |  |                           |
| Asset Generation Service  |<----+                           +---->|   Post-Production Service   |
| (Celery Worker + Veo)     |     |                           |     | (Celery Worker + FFMPEG)    |
|                           |     |                           |     |                           |
+---------------------------+     +---------------------------+     +---------------------------+

```

### Component Breakdown
-   **API Gateway**: The single entry point, powered by Nginx, routing traffic to the Orchestrator.
-   **Orchestrator Service**: The "brain" of the operation. A FastAPI application that uses **LangGraph** to manage the stateful workflow. It accepts user prompts and delegates tasks.
-   **Creative Director Service**: A FastAPI service that uses **Gemini Pro** to generate a script and storyboard.
-   **Asset Generation Service**: A **Celery** worker that listens for jobs on a dedicated RabbitMQ queue. It calls the **Google Veo** API to generate video clips and uploads them to MinIO. Features automatic retries for API rate limits.
-   **Post-Production Service**: A **Celery** worker that listens on its own queue. It is responsible for downloading assets from MinIO and using **FFmpeg** to combine them into a final video. (Note: The FFMPEG logic is implemented, but a more complex audio/transition layer could be added).

---

## Getting Started

Follow these instructions to get the entire platform running on your local machine.

### Prerequisites

-   [Docker](https://www.docker.com/products/docker-desktop/) and Docker Compose
-   Git
-   A Google AI Studio API Key with access to the **Veo** model.

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/agentic-video-ads.git
cd agentic-video-ads
```

### 2. Configure Environment Variables

This project uses a single `.env` file to manage all configurations and secrets. You must create this file in the root directory of the project.

1.  Create a file named `.env`:
    ```bash
    touch .env
    ```
2.  Copy the contents of the block below and paste it into your new `.env` file.
3.  **You must replace `"your_real_google_api_key_here"` with your actual API key.**

```env
# ======================================================
#         ENVIRONMENT VARIABLES for agentic-video-ads
# ======================================================

# --- Google AI Credentials ---
# Replace with your actual key from Google AI Studio
GOOGLE_API_KEY="your_real_google_api_key_here"

# --- Local Docker Infrastructure Credentials ---
# These are used by the infrastructure services themselves
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=video_jobs

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# --- S3/MinIO Client Configuration ---
# These are used by the Python services to connect to MinIO
# The hostname MUST match the service name in docker-compose.yml
S3_ENDPOINT_URL="http://minio-storage:9000"
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=video-assets

# --- Celery/RabbitMQ Configuration ---
# Used by Python services to connect to RabbitMQ
CELERY_BROKER_URL="amqp://guest:guest@message_queue:5672/"

# --- Creative Agent Configuration ---
# Used by the Orchestrator to call the Creative Director service
CREATIVE_AGENT_URL="http://creative-director:8001/v1/creative-plan"
```

### 3. Build and Run the Application

This single command will build all the custom container images, download the infrastructure images, and start the entire application stack.

```bash
docker-compose up --build
```
The initial startup may take several minutes as it downloads all the necessary images.

### 4. Create the MinIO Bucket

Before running your first job, you need to create the storage bucket.
1.  Open your web browser and navigate to the MinIO console: **http://localhost:9001**
2.  Log in with the credentials from your `.env` file (User: `minioadmin`, Password: `minioadmin`).
3.  Click the "Create Bucket" button and create a new bucket named **`video-assets`**.

### 5. Run Your First Job

You can now send a request to the API to generate your first video. Open a new terminal and use the following `curl` command (or your favorite API client).

```powershell
# Example using curl.exe on Windows PowerShell
curl.exe -X POST "http://localhost:8080/jobs" -H "Content-Type: application/json" -d '{"prompt": "A cinematic, high-speed, slow-motion shot of a water balloon exploding on a drum kit."}'
```

The command will wait until the entire workflow is complete, which may take several minutes depending on the complexity and video generation time. Watch the Docker logs to see the agents at work! The final JSON response will contain the URL to your generated video on the local MinIO server.

---

## Technology Stack

-   **Backend**: Python, FastAPI, LangGraph
-   **AI Models**: Google Gemini Pro, Google Veo
-   **Orchestration**: Docker, Docker Compose
-   **Task Queue**: Celery, RabbitMQ
-   **Storage**: PostgreSQL (for job metadata), MinIO (for video assets)
-   **Video Processing**: FFmpeg
-   **API Gateway**: Nginx