"""Utility for verifying registered agents in Gemini Enterprise."""

import json
import logging
import os
import subprocess

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
APP_ID = os.getenv("GEMINI_APP_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

def verify_registration():
    """Verifies the registered agents for the Gemini Enterprise engine."""
    logger.info(f"Verifying registered agents for engine {APP_ID}...")
    
    try:
        token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
    except subprocess.CalledProcessError as e:
        logger.error("Failed to get gcloud access token. Ensure you are authenticated.")
        raise RuntimeError("Authentication failed") from e
        
    url = (
        f"https://{LOCATION}-discoveryengine.googleapis.com/v1alpha/"
        f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/"
        f"engines/{APP_ID}/assistants/default_assistant/agents"
    )
    
    cmd = [
        "curl", "-s", "-X", "GET",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"X-Goog-User-Project: {PROJECT_ID}",
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        response_json = json.loads(result.stdout)
        if "error" in response_json:
            logger.error(f"Failed to get agents: {response_json['error']}")
            return
            
        agents = response_json.get("agents", [])
        if not agents:
            logger.info("No agents found registered to this engine.")
            return
            
        logger.info(f"\\nFound {len(agents)} registered agent(s):")
        for agent in agents:
            display_name = agent.get("displayName", "Unknown")
            state = agent.get("state", "UNKNOWN_STATE")
            name = agent.get("name", "Unknown Name")
            logger.info(f"- {display_name} (State: {state})")
            logger.info(f"  Resource Name: {name}")
            
    else:
        logger.error(f"Failed to execute command: {result.stderr}")

if __name__ == "__main__":
    verify_registration()
