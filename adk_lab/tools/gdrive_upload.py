import os
import io
import tempfile
from PIL import Image
import uuid

# The correct imports from the ADK documentation that you found.
from google.adk.tools import ToolContext, FunctionTool

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- Configuration ---
SERVICE_ACCOUNT_FILE = os.getenv(
    "SERVICE_ACCOUNT_FILE", "/home/chertushkin/adk-lab-real/adk_lab/adk_lab/service_account.json"
)
SHARED_DRIVE_NAME = os.getenv("SHARED_DRIVE_NAME", "adk_lab_shared")
GDRIVE_FOLDER_NAME = os.getenv("GDRIVE_FOLDER_NAME", "adk_lab")
SCOPES = ["https://www.googleapis.com/auth/drive"]


def upload_image_to_drive(tool_context: ToolContext) -> str:
    """Uploads an image from the user's prompt to a specific folder on Google Drive.

    The @register_tool decorator inspects this docstring to create the schema for the LLM.
    That is how it knows about the 'filename' argument.

    Args:
        tool_context: The context object provided by the ADK framework. It contains
                      both the user's original prompt and the parameters from the LLM.
    """
    # 1. Get the image bytes from the user's prompt via the tool_context
    print(tool_context)
    print(dir(tool_context))
    print(type(tool_context))
    user_content = tool_context.user_content
    image_bytes = None

    # Loop through each Part in the 'parts' list
    for part in user_content.parts:
        # Check if the part has image data by looking for the 'inline_data'
        # attribute and checking its 'mime_type'.
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            # If it's an image, get its raw byte data
            image_bytes = part.inline_data.data
            # Exit the loop since we found the image
            break

    # Now, the 'image_bytes' variable holds the image data:
    # b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...'
    if image_bytes:
        print("Successfully extracted image data!")
    else:
        print("No image found in the content.")

    # 3. Perform the upload using the extracted data
    filename = str(uuid.uuid4()) + ".png"
    try:
        image = Image.open(io.BytesIO(image_bytes))
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build("drive", "v3", credentials=creds)

        drive_response = service.drives().list(q=f"name='{SHARED_DRIVE_NAME}'").execute()
        drive_id = drive_response.get("drives")[0].get("id")

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
        folder_id = folder_response.get("files")[0].get("id")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as temp_file:
            image.save(temp_file.name, "PNG")
            file_metadata = {"name": filename, "parents": [folder_id]}
            media = MediaFileUpload(temp_file.name, mimetype="image/png")
            uploaded_file = (
                service.files()
                .create(body=file_metadata, media_body=media, supportsAllDrives=True, fields="id, name")
                .execute()
            )

            return f"✅ Successfully uploaded '{uploaded_file.get('name')}' with File ID: {uploaded_file.get('id')}"

    except Exception as e:
        return f"❌ An unexpected error occurred during upload: {e}"


gdrive_upload_tool = FunctionTool(upload_image_to_drive)
