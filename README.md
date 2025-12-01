# Agentic Video Ads

**`agentic-video-ads`** is a sophisticated, end-to-end platform for automatically generating 30-second video advertisements from a single text prompt. This project is built on a robust, scalable, and asynchronous microservice architecture, leveraging multiple specialized AI agents to orchestrate the entire video production pipeline from creative conception to final rendering.

The system uses a multi-agent workflow where a central **Orchestrator Agent** manages and delegates tasks to specialized agents for creative planning, asset generation, and post-production, demonstrating a powerful pattern for building complex, real-world AI applications.

---

## Features

-   **Prompt-to-Video**: Generate a complete 30-second video ad from a single natural language prompt.
-   **AI-Powered Creative Direction**: Utilizes Google's Gemini Pro to generate a professional script and a detailed, scene-by-scene storyboard.
-   **Generative Video Clips**: Leverages Google's state-of-the-art Veo model to create high-quality video clips for each scene in the storyboard.
-   **AI-Generated Voiceover**: Uses ElevenLabs text-to-speech API to generate professional voiceover narration from the script with customizable voice selection.
-   **Background Music Integration**: Automatically adds background music from a curated library of royalty-free tracks to enhance the final video.
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
| Asset Generation Service  |<----+                           +--->|   Post-Production Service   |
| (Celery Worker)           |     |                           |     | (Celery Worker + FFMPEG)    |
| - Veo (Video Generation)  |     |                           |     | - Audio/Video Mixing        |
| - ElevenLabs (Voiceover)  |     |                           |     | - Background Music          |
+---------------------------+     +---------------------------+     +---------------------------+

```

### Component Breakdown

-   **API Gateway**: The single entry point, powered by Nginx, routing traffic to the Orchestrator.
-   **Orchestrator Service**: The "brain" of the operation. A FastAPI application that uses **LangGraph** to manage the stateful workflow. It accepts user prompts and delegates tasks.
-   **Creative Director Service**: A FastAPI service that uses **Gemini Pro** to generate a script and storyboard.
-   **Asset Generation Service**: A **Celery** worker that listens for jobs on a dedicated RabbitMQ queue. It performs two main tasks:
    - Calls the **Google Veo** API to generate video clips for each scene
    - Calls the **ElevenLabs** API to generate AI voiceover from the script
    - Uploads all assets to MinIO with automatic retries for API rate limits
-   **Post-Production Service**: A **Celery** worker that listens on its own queue. It downloads all assets from MinIO (video clips, voiceover, and background music) and uses **FFmpeg** to combine them into a final polished video.

### Resilience & Reliability Features

This system is designed with production-grade reliability in mind:

-   **Service Health Checks**: All infrastructure services (PostgreSQL, RabbitMQ, MinIO) include health checks to ensure they are fully operational before dependent services start.
-   **Dependency Management**: Services use Docker Compose's `depends_on` with `condition: service_healthy` to ensure proper startup sequencing and avoid race conditions.
-   **Automatic Retries**: The asset generation service implements exponential backoff retry logic to handle API rate limits gracefully.
-   **Restart Policies**: All services are configured with `restart: unless-stopped` to automatically recover from failures.
-   **PYTHONPATH Configuration**: All Python services have proper PYTHONPATH settings to ensure reliable module imports.

---

## Project Structure

```
agentic-video-ads/
├── services/
│   ├── api-gateway/              # Nginx reverse proxy
│   ├── orchestrator-agent/       # LangGraph workflow orchestration
│   │   └── src/
│   │       ├── workflow/         # LangGraph state machine
│   │       ├── database/         # PostgreSQL models
│   │       └── core/             # Configuration
│   ├── creative-agent/           # Gemini Pro script generation
│   ├── asset-generator-agent/    # Veo video + ElevenLabs voiceover
│   └── post-production-agent/    # FFmpeg video assembly
│       └── assets/
│           └── music/            # Background music library (6 tracks)
├── docker-compose.yml            # Full stack orchestration
├── .env                          # Environment configuration
└── README.md
```

---

## Getting Started

Follow these instructions to get the entire platform running on your local machine.

### Prerequisites

-   [Docker](https://www.docker.com/products/docker-desktop/) and Docker Compose
-   Git
-   A **Google AI Studio API Key** with access to the **Veo** model
-   An **ElevenLabs API Key** for voiceover generation

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
3.  **You must replace the placeholder API keys with your actual keys.**

```env
# ======================================================
#         ENVIRONMENT VARIABLES for agentic-video-ads
# ======================================================

# --- Google AI Credentials ---
# Replace with your actual key from Google AI Studio
# Required for: Video generation (Veo) and script generation (Gemini Pro)
GOOGLE_API_KEY="your_real_google_api_key_here"

# --- ElevenLabs Credentials ---
# Replace with your actual key from ElevenLabs
# Required for: AI voiceover generation
ELEVENLABS_API_KEY="your_real_elevenlabs_api_key_here"

# Optional: Specify a custom voice ID (default: "21m00Tcm4TlvDq8ikWAM")
# You can find voice IDs at: https://elevenlabs.io/voice-library
ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"

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

The initial startup may take several minutes as it downloads all the necessary images. The healthcheck system ensures that all infrastructure services are ready before the application services start.

### 4. Create the MinIO Bucket

Before running your first job, you need to create the storage bucket.

1.  Open your web browser and navigate to the MinIO console: **http://localhost:9001**
2.  Log in with the credentials from your `.env` file (User: `minioadmin`, Password: `minioadmin`).
3.  Click the "Create Bucket" button and create a new bucket named **`video-assets`**.

### 5. Run Your First Job

You can now send a request to the API to generate your first video. Open a new terminal and use one of the following methods:

#### Using curl (Windows PowerShell):

```powershell
curl.exe -X POST "http://localhost:8080/jobs" -H "Content-Type: application/json" -d '{\"prompt\": \"A cinematic, high-speed, slow-motion shot of a water balloon exploding on a drum kit.\"}'
```

#### Using PowerShell (Invoke-WebRequest):

A PowerShell script example is included in the `request` file at the root of the project. You can run it directly:

```powershell
.\request
```

Or use this template:

```powershell
$headers = @{
    "Content-Type" = "application/json"
}

$body = '{\"prompt\": \"Your creative prompt here\"}'

Invoke-WebRequest -Uri "http://localhost:8080/jobs" -Method POST -Headers $headers -Body $body
```

The command will wait until the entire workflow is complete, which may take several minutes depending on the complexity and video generation time. Watch the Docker logs to see the agents at work! The final JSON response will contain the URL to your generated video on the local MinIO server.

---

## Monitoring & Debugging

### View Service Logs

To monitor the workflow in real-time:

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f orchestrator
docker-compose logs -f asset-generator
docker-compose logs -f post-production
```

### Access Management Interfaces

-   **RabbitMQ Management**: http://localhost:15672 (guest/guest)
-   **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
-   **Orchestrator API Docs**: http://localhost:8000/docs
-   **Creative Director API Docs**: http://localhost:8001/docs

---

## Technology Stack

-   **Backend**: Python, FastAPI, LangGraph
-   **AI Models**: 
    - Google Gemini Pro (Script Generation)
    - Google Veo (Video Generation)
    - ElevenLabs (Voiceover Generation)
-   **Orchestration**: Docker, Docker Compose
-   **Task Queue**: Celery, RabbitMQ
-   **Storage**: PostgreSQL (for job metadata), MinIO (for video assets)
-   **Video Processing**: FFmpeg
-   **API Gateway**: Nginx

---

## Audio Features

### AI Voiceover (ElevenLabs)

The system generates professional voiceover narration using ElevenLabs' text-to-speech API:

-   **Model**: `eleven_multilingual_v2` (supports multiple languages)
-   **Output Format**: MP3 (44.1kHz, 128kbps)
-   **Default Voice**: Rachel (ID: `21m00Tcm4TlvDq8ikWAM`)
-   **Customization**: You can specify any ElevenLabs voice ID via the `ELEVENLABS_VOICE_ID` environment variable

### Background Music

The post-production service includes a curated library of royalty-free background music tracks:

-   Aylex - Living
-   Aylex - Okay Energy
-   Walen - Echoes
-   Walen - HEADPHONK
-   Walen - Wanderer
-   Sandbreaker

Music is randomly selected and mixed with the voiceover during post-production. The background music volume is automatically adjusted to ensure the voiceover remains clear and prominent.

---

## License

This project is for educational and demonstration purposes. Please ensure you have the appropriate licenses for any AI models and music assets used in production.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## Troubleshooting

### Services fail to start

-   Ensure Docker Desktop is running
-   Check that ports 8080, 8000, 8001, 5432, 5672, 15672, 9000, and 9001 are not in use
-   Verify your `.env` file is properly configured with all required API keys

### Video generation fails

-   Verify your Google API key has access to the Veo model
-   Check the asset-generator logs for API errors
-   Ensure the MinIO bucket `video-assets` exists

### Voiceover generation fails

-   Verify your ElevenLabs API key is valid and has sufficient credits
-   Check the asset-generator logs for ElevenLabs API errors
-   Ensure the `ELEVENLABS_API_KEY` environment variable is set correctly

### Healthcheck failures

-   Wait for all services to fully initialize (can take 1-2 minutes)
-   Check individual service logs for specific errors
-   Restart the stack: `docker-compose down && docker-compose up --build`

### API Key Issues

If you see errors related to missing API keys:

1. Verify your `.env` file exists in the project root
2. Ensure all API keys are properly quoted and have no extra spaces
3. Restart the services after updating the `.env` file: `docker-compose restart`