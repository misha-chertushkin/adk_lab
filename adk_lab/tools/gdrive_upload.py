import io
import logging  # Added for logging
import os
import re
import tempfile
import uuid

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# The correct imports from the ADK documentation that you found.
from google.adk.tools import FunctionTool, ToolContext
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image

# --- Configuration ---
SERVICE_ACCOUNT_FILE = os.getenv(
    "SERVICE_ACCOUNT_FILE", "/home/chertushkin/adk-lab-real/adk_lab/adk_lab/service_account.json"
)
# These are no longer needed as we are uploading to the root directory
SHARED_DRIVE_NAME = os.getenv("SHARED_DRIVE_NAME", "adk_lab_shared")
GDRIVE_FOLDER_NAME = os.getenv("GDRIVE_FOLDER_NAME", "adk_lab")
SCOPES = ["https://www.googleapis.com/auth/drive"]

AGENTSPACE_AUTH_ID = "adk-lab-1"  # os.getenv("AGENTSPACE_AUTH_ID")
if not AGENTSPACE_AUTH_ID:
    raise ValueError("AGENTSPACE_AUTH_ID environment variable not set.")


def get_access_token(tool_context: ToolContext, auth_id: str) -> str | None:
    """Retrieves the OAuth access token from the ToolContext state provided by Agentspace."""
    # Pattern to find the token key, e.g., "temp:YOUR_AGENTSPACE_AUTH_ID" or "temp:YOUR_AGENTSPACE_AUTH_ID_0"
    logging.info("TOOL CONTEXT")
    logging.info(tool_context)
    auth_id_pattern = re.compile(f"temp:{re.escape(auth_id)}(_\\d+)?")
    state_dict = tool_context.state.to_dict()
    logging.info(state_dict)
    for key, value in state_dict.items():
        if auth_id_pattern.match(key) and isinstance(value, str):
            logging.info(f"Found access token in state key: {key}")
            return value
    logging.warning(f"Access token not found for AGENTSPACE_AUTH_ID='{auth_id}' in tool_context.state")
    logging.warning(f"Available state keys: {list(state_dict.keys())}")
    return None


def upload_text_to_drive(tool_context: ToolContext, text_content: str) -> str:
    """Uploads the given text content to a file in Google Drive.

    Args:
        tool_context: The context object provided by the ADK framework.
        text_content: The string content to be saved in the text file.
    """
    logging.info("Preparing to upload user query to Google Drive...")
    filename = str(uuid.uuid4()) + ".txt"

    file_bytes = text_content.encode("utf-8")
    mime_type = "text/plain"

    try:
        # Use OAuth2 credentials from the tool_context
        access_token = get_access_token(tool_context, AGENTSPACE_AUTH_ID)
        if not access_token:
            return (
                f"❌ Error: OAuth access token not found. "
                f"Ensure the agent is authorized in Agentspace with AUTH_ID='{AGENTSPACE_AUTH_ID}'. "
                "The user may need to click 'Authorize' in the Agentspace UI."
            )
        creds = Credentials(token=access_token)

        # creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build("drive", "v3", credentials=creds)

        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush()

            # By not specifying 'parents', the file is uploaded to the root "My Drive" folder.
            file_metadata = {"name": filename}
            media = MediaFileUpload(temp_file.name, mimetype=mime_type)

            uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id, name").execute()

            return f"✅ Successfully uploaded '{uploaded_file.get('name')}' to your Google Drive with File ID: {uploaded_file.get('id')}"

    except Exception as e:
        logging.error(f"An unexpected error occurred during upload: {e}", exc_info=True)
        return f"❌ An unexpected error occurred during upload: {e}"


gdrive_upload_tool = FunctionTool(upload_text_to_drive)
