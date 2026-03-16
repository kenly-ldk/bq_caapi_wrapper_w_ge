#!/bin/bash

# Deployment script for ADK Agents to Vertex AI Agent Engine

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== ADK Agent Deployment Script ===${NC}"
echo ""

# Load environment variables from root .env
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables from .env${NC}"
    # Use -a to export all variables
    set -a
    source .env
    set +a
else
    echo -e "${RED}ERROR: .env file not found in project root${NC}"
    exit 1
fi

# Verify required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ]; then
    echo -e "${RED}ERROR: GOOGLE_CLOUD_PROJECT_ID not set${NC}"
    exit 1
fi

if [ -z "$OAUTH_CLIENT_ID" ] || [ -z "$OAUTH_CLIENT_SECRET" ] || [ "$OAUTH_CLIENT_ID" == "PLACEHOLDER" ] || [ "$OAUTH_CLIENT_SECRET" == "PLACEHOLDER" ]; then
    echo -e "${RED}ERROR: OAuth credentials not set or are placeholders${NC}"
    echo -e "${YELLOW}Please update .env with valid OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET${NC}"
    exit 1
fi

echo -e "${GREEN}Environment loaded${NC}"
echo "  Project: $GOOGLE_CLOUD_PROJECT_ID"
echo ""

PROJECT_ID="$GOOGLE_CLOUD_PROJECT_ID"
LOCATION="${GOOGLE_CLOUD_REGION:-us-central1}"

deploy_agent() {
    local agent_dir=$1
    local display_name=$2
    
    echo -e "${YELLOW}Deploying $display_name...${NC}"
    
    # We use env UV_NO_CONFIG=1 for uv run as well
    env UV_NO_CONFIG=1 uv run adk deploy agent_engine "$agent_dir" \
        --project="$PROJECT_ID" \
        --region="$LOCATION" \
        --display_name="$display_name"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}$display_name deployed successfully${NC}"
        echo ""
    else
        echo -e "${RED}Failed to deploy $display_name${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}=== Deploying CAAPI Wrapper Agent ===${NC}"
deploy_agent "app/bq_caapi_wrapper_agent" "CAAPI Wrapper Agent"

echo -e "${GREEN}=== Deployment Complete ===${NC}"
