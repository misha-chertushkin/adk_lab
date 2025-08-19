import io
import os
import tempfile
import uuid
import logging  # Added for logging
import re

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
# SHARED_DRIVE_NAME = os.getenv("SHARED_DRIVE_NAME", "adk_lab_shared")
# GDRIVE_FOLDER_NAME = os.getenv("GDRIVE_FOLDER_NAME", "adk_lab")
SCOPES = ["https://www.googleapis.com/auth/drive"]

AGENTSPACE_AUTH_ID = "adk-lab-three-ga"  # os.getenv("AGENTSPACE_AUTH_ID")
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


def upload_image_to_drive(tool_context: ToolContext) -> str:
    """Uploads an image from the user's prompt to the root folder of Google Drive.

    The @register_tool decorator inspects this docstring to create the schema for the LLM.
    That is how it knows about the 'filename' argument.

    Args:
        tool_context: The context object provided by the ADK framework. It contains
                      both the user's original prompt and the parameters from the LLM.
    """
    # 1. Get the image bytes from the user's prompt via the tool_context
    logging.info(tool_context)
    logging.info(dir(tool_context))
    logging.info(type(tool_context))
    user_content = tool_context.user_content
    image_bytes = None
    logging.info("IN IMAGE 1")
    # Loop through each Part in the 'parts' list
    for part in user_content.parts:
        # Check if the part has image data by looking for the 'inline_data'
        # attribute and checking its 'mime_type'.
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            # If it's an image, get its raw byte data
            image_bytes = part.inline_data.data
            # Exit the loop since we found the image
            break
    logging.info("IN IMAGE 2")
    # Now, the 'image_bytes' variable holds the image data:
    # b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...'
    if image_bytes:
        logging.info("Successfully extracted image data!")
    else:
        logging.warning("No image found in the content.")
        return "❌ Error: No image found in the prompt."

    logging.info("IN IMAGE 3")
    # 3. Perform the upload using the extracted data
    filename = str(uuid.uuid4()) + ".png"
    try:
        image = Image.open(io.BytesIO(image_bytes))

        access_token = get_access_token(tool_context, AGENTSPACE_AUTH_ID)
        if not access_token:
            return (
                f"❌ Error: OAuth access token not found. "
                f"Ensure the agent is authorized in Agentspace with AUTH_ID='{AGENTSPACE_AUTH_ID}'. "
                "The user may need to click 'Authorize' in the Agentspace UI."
            )
        creds = Credentials(token=access_token)
        service = build("drive", "v3", credentials=creds)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as temp_file:
            image.save(temp_file.name, "PNG")

            # By not specifying 'parents', the file is uploaded to the root "My Drive" folder.
            file_metadata = {"name": filename}
            media = MediaFileUpload(temp_file.name, mimetype="image/png")

            # The 'supportsAllDrives' flag is not needed when not interacting with Shared Drives.
            uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id, name").execute()

            return f"✅ Successfully uploaded '{uploaded_file.get('name')}' to your Google Drive with File ID: {uploaded_file.get('id')}"

    except Exception as e:
        # Log the full exception details before returning the user-facing message
        logging.error(f"An unexpected error occurred during upload: {e}", exc_info=True)
        return f"❌ An unexpected error occurred during upload: {e}"


gdrive_upload_tool = FunctionTool(upload_image_to_drive)
