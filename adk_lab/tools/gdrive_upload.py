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


def upload_text_to_drive(text_content: str) -> str:
    """Uploads the given text content to a file in Google Drive.

    Args:
        text_content: The string content to be saved in the text file.
    """
    logging.info("Preparing to upload user query to Google Drive...")
    filename = str(uuid.uuid4()) + ".txt"
    # Use the text_content parameter instead of hardcoded bytes
    file_bytes = text_content.encode("utf-8")
    mime_type = "text/plain"

    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build("drive", "v3", credentials=creds)

        drive_response = service.drives().list(q=f"name='{SHARED_DRIVE_NAME}'").execute()
        drives = drive_response.get("drives")
        if not drives:
            return f"❌ Error: Shared Drive '{SHARED_DRIVE_NAME}' not found."
        drive_id = drives[0].get("id")

        folder_query = f"name='{GDRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder'"
        folder_response = (
            service.files()
            .list(
                q=folder_query,
                driveId=drive_id,
                corpora="drive",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
        folders = folder_response.get("files")
        if not folders:
            return f"❌ Error: Folder '{GDRIVE_FOLDER_NAME}' not found in Shared Drive '{SHARED_DRIVE_NAME}'."
        folder_id = folders[0].get("id")

        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush()

            file_metadata = {"name": filename, "parents": [folder_id]}
            media = MediaFileUpload(temp_file.name, mimetype=mime_type)

            uploaded_file = (
                service.files()
                .create(body=file_metadata, media_body=media, supportsAllDrives=True, fields="id, name")
                .execute()
            )

            return f"✅ Successfully uploaded '{uploaded_file.get('name')}' to folder '{GDRIVE_FOLDER_NAME}' with File ID: {uploaded_file.get('id')}"

    except Exception as e:
        logging.error(f"An unexpected error occurred during upload: {e}", exc_info=True)
        return f"❌ An unexpected error occurred during upload: {e}"


gdrive_upload_tool = FunctionTool(upload_text_to_drive)
