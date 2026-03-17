"""Utility for listing Discovery Engine (Gemini Enterprise) engines."""

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
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

def list_engines():
    """Lists available Discovery Engine engines in the project."""
    logger.info(f"Listing engines for project {PROJECT_ID} in location {LOCATION}...")
    
    try:
        token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
    except subprocess.CalledProcessError as e:
        logger.error("Failed to get gcloud access token. Ensure you are authenticated.")
        raise RuntimeError("Authentication failed") from e
        
    url = (
        f"https://{LOCATION}-discoveryengine.googleapis.com/v1alpha/"
        f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/engines"
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
            logger.error(f"Failed to list engines: {response_json['error']}")
            return
            
        engines = response_json.get("engines", [])
        if not engines:
            logger.info("No engines found in this location.")
            return
            
        logger.info(f"\\nFound {len(engines)} engine(s):")
        for engine in engines:
            name = engine.get("name")
            display_name = engine.get("displayName")
            engine_id = name.split("/")[-1] if name else "Unknown"
            logger.info(f"- Engine ID: {engine_id} (Name: {display_name})")
            
    else:
        logger.error(f"Failed to execute command: {result.stderr}")

if __name__ == "__main__":
    list_engines()
