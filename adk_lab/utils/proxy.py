import os
import logging
import dotenv
from google.cloud import secretmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str | None:
    """Fetches a secret from Google Cloud Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to access secret '{secret_id}' in project '{project_id}': {e}")
        return None


def _get_config_value(env_var: str, secret_name: str | None = None) -> str | None:
    """
    Gets a configuration value from an environment variable first,
    then falls back to Secret Manager if a secret_name is provided.
    """
    value = os.getenv(env_var)
    if value:
        logger.info(f"Loaded '{env_var}' from environment.")
        return value

    if secret_name:
        logger.info(f"'{env_var}' not in environment, fetching from Secret Manager as '{secret_name}'...")
        return _get_secret(PROJECT_ID, secret_name)

    logger.warning(f"Configuration for '{env_var}' not found in environment or Secret Manager.")
    return None


# --- Project Configuration ---
dotenv.load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "chertushkin-genai-sa")

# --- Secret Constants ---
GITHUB_TOKEN = _get_config_value("GITHUB_PERSONAL_ACCESS_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN")

# BigQuery Secrets
BQ_DATASET = _get_config_value("BIGQUERY_DATASET", "BIGQUERY_DATASET")
BQ_TABLE = _get_config_value("BIGQUERY_TABLE", "BIGQUERY_TABLE")
BQ_LOCATION = _get_config_value("BIGQUERY_LOCATION", "BIGQUERY_LOCATION")
EMBEDDING_MODEL_NAME = _get_config_value("EMBEDDING_MODEL", "EMBEDDING_MODEL")
