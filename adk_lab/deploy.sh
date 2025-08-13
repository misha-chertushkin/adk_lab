#!/bin/bash
# this is for deploy to Cloud Run

# --- Parameter Validation ---
if [[ "$1" != "stackexchange" && "$1" != "github" ]]; then
    echo "Error: Invalid agent type specified."
    echo "Usage: $0 [stackexchange|github]"
    exit 1
fi
AGENT_TYPE=$1

# --- Configuration: Please edit these variables ---
export PROJECT_ID="chertushkin-genai-sa"           # Your Google Cloud project ID
# export REGION="global"                       # The region for your services (e.g., us-central1)
export REGION="us-central1"
# SERVICE_NAME is now set dynamically based on AGENT_TYPE
export REPO_NAME="adk-lab"                 # The name for your Artifact Registry repository

# --- Dynamic Configuration ---
if [ "$AGENT_TYPE" == "stackexchange" ]; then
  export SERVICE_NAME="stackexchange-agent"
  AGENT_MODULE="adk_lab.stackexchange_agent.main"
elif [ "$AGENT_TYPE" == "github" ]; then
  export SERVICE_NAME="github-agent"
  AGENT_MODULE="adk_lab.github_agent.main"
fi

# --- Script Logic ---
# Do not edit below this line unless you know what you are doing.

# Construct the Artifact Registry repository URL
export AR_REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

# Construct the full image name and tag
export IMAGE_NAME="${AR_REPO_URL}/${SERVICE_NAME}:latest"

echo "--- Configuration ---"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Deploying Agent: $AGENT_TYPE"
echo "Service Name: $SERVICE_NAME"
echo "Agent Module: $AGENT_MODULE"
echo "Artifact Registry Repo: $AR_REPO_URL"
echo "Full Image Name: $IMAGE_NAME"
echo "---------------------"

# 1. Enable required Google Cloud services
echo "\n- Enabling Google Cloud services..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --project=${PROJECT_ID}

# 2. Create Artifact Registry repository if it doesn't exist
echo "\n- Checking for Artifact Registry repository..."
if ! gcloud artifacts repositories describe ${REPO_NAME} --location=${REGION} --project=${PROJECT_ID} &> /dev/null; then
  echo "  Repository '${REPO_NAME}' not found. Creating it..."
  gcloud artifacts repositories create ${REPO_NAME} \
    --repository-format=docker \
    --location=${REGION} \
    --project=${PROJECT_ID} \
    --description="Repository for ADK and LangGraph agents"
else
  echo "  Repository '${REPO_NAME}' already exists."
fi


# 3. Build the container image using Cloud Build and push to Artifact Registry
echo "\n- Building container image with Cloud Build..."
gcloud builds submit . --tag=${IMAGE_NAME} --project=${PROJECT_ID}

# 4. Deploy the container to Cloud Run
# The --args flag overrides the CMD in the Dockerfile to select the agent.
echo "\n- Deploying service to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME} \
  --args="${AGENT_MODULE}" \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --project=${PROJECT_ID}

# 5. Display the URL of the deployed service
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform=managed --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "\n🚀 Deployment successful!"
echo "Your ${AGENT_TYPE} Agent is available at: ${SERVICE_URL}"
echo "You can view its Agent Card by visiting the URL in a browser."