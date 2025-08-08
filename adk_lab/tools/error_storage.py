from google.adk.tools import FunctionTool


def get_error_storage(error_id: str) -> str:
    """
    Retrieves specific error logs or files from cloud storage (Google Drive).
    Use this when you have a specific ID for an error log or a file.
    """
    print(f"TOOL: Retrieving from Error Storage (Google Drive) with ID: '{error_id}'")
    # In a real implementation, this would use the Google Drive API to fetch a file.
    return f"Retrieved error log {error_id}. The log shows a 'KeyError' at line 52."


error_storage_tool = FunctionTool(func=get_error_storage)