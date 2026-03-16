"""Admin tools for managing Conversational Analytics agents."""

import logging
import os

from dotenv import load_dotenv
from google.cloud import geminidataanalytics_v1beta as geminidataanalytics
from google.protobuf import field_mask_pb2

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
AGENT_ID = os.getenv("BIGQUERY_DATA_AGENT_ID", "your-agent-id")


def get_bq_refs(table_ids: list[str]) -> list[geminidataanalytics.BigQueryTableReference]:
    """Construct BigQuery table references from full IDs.

    Args:
        table_ids: List of full table IDs (e.g., 'project.dataset.table' or 'dataset.table').

    Returns:
        List of BigQueryTableReference objects.
    """
    refs = []
    for full_id in table_ids:
        parts = [p.strip() for p in full_id.split(".")]
        if len(parts) == 3:
            refs.append(
                geminidataanalytics.BigQueryTableReference(
                    project_id=parts[0], dataset_id=parts[1], table_id=parts[2]
                )
            )
        elif len(parts) == 2:
            # Fallback to current project if omitted
            refs.append(
                geminidataanalytics.BigQueryTableReference(
                    project_id=PROJECT_ID, dataset_id=parts[0], table_id=parts[1]
                )
            )
        else:
            logger.warning(f"Invalid table ID format: {full_id}. Expected 'project.dataset.table' or 'dataset.table'.")
    return refs


def create_agent(client: geminidataanalytics.DataAgentServiceClient) -> None:
    """Create an Agent with order and user context.

    Args:
        client: DataAgentServiceClient instance.
    """
    logger.info(f"Creating Agent: {AGENT_ID}...")
    table_ids_str = os.getenv("BIGQUERY_TABLE_IDS", "")
    if not table_ids_str:
        logger.warning("No BIGQUERY_TABLE_IDS found in environment. Agent will have no tables.")
        table_ids = []
    else:
        table_ids = [t.strip() for t in table_ids_str.split(",")]
    
    bq_refs = get_bq_refs(table_ids)

    datasource_references = geminidataanalytics.DatasourceReferences(
        bq=geminidataanalytics.BigQueryTableReferences(table_references=bq_refs)
    )

    published_context = geminidataanalytics.Context(
        system_instruction=(
            "You are an expert in data analysis and querying. "
            "Focus on analyzing data and answering user queries."
        ),
        datasource_references=datasource_references,
    )

    agent = geminidataanalytics.DataAgent(
        data_analytics_agent=geminidataanalytics.DataAnalyticsAgent(
            published_context=published_context
        ),
        description="Specialized agent for data analysis.",
    )

    request = geminidataanalytics.CreateDataAgentRequest(
        parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
        data_agent_id=AGENT_ID,
        data_agent=agent,
    )

    try:
        operation = client.create_data_agent(request=request)
        result = operation.result()
        logger.info(f"Agent created successfully: {result.name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.info("Agent already exists, skipping creation.")
        else:
            logger.error(f"Failed to create Agent: {e}", exc_info=True)
            raise


def list_agents(client: geminidataanalytics.DataAgentServiceClient) -> None:
    """List all agents in the project.

    Args:
        client: DataAgentServiceClient instance.
    """
    logger.info("Listing all agents in project...")
    request = geminidataanalytics.ListDataAgentsRequest(
        parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
    )
    page_result = client.list_data_agents(request=request)
    for agent in page_result:
        agent_id = agent.name.split("/")[-1]
        logger.info(f"Agent Found - ID: {agent_id}, Description: {agent.description}")


if __name__ == "__main__":
    client = geminidataanalytics.DataAgentServiceClient()
    create_agent(client)
    list_agents(client)
