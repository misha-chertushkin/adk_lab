from google.adk.tools import FunctionTool

# In your tool definition file (e.g., tools/code_manual.py)

import os
from google.adk.tools import FunctionTool
from google.cloud import discoveryengine_v1 as discoveryengine
import dotenv

from google.cloud import secretmanager
def get_secret(project_id, secret_id):
    # Make sure to replace 'your-gcp-project-id' with your actual project ID
    version_id = "latest"

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


if os.getenv("BIGQUERY_DATASET", None) is None:
    # we are deployed remotely:
    GOOGLE_CLOUD_PROJECT = "chertushkin-genai-sa"
    GOOGLE_CLOUD_LOCATION = get_secret(GOOGLE_CLOUD_PROJECT, "GOOGLE_CLOUD_LOCATION")
    DATASTORE_ID = get_secret(GOOGLE_CLOUD_PROJECT, "DATASTORE_ID")
else:
    # we are deloyed locally, reading from .env
    dotenv.load_dotenv()
    GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
    GOOGLE_CLOUD_LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]
    DATASTORE_ID = os.environ["DATASTORE_ID"]


def search_code_manual(query: str) -> str:
    """
    Searches the code manuals and documentation (Vertex AI Search) for solutions.
    Use this to find relevant articles, code examples, and best practices.
    Returns a formatted string of the top search results.
    """
    print(f"TOOL: Searching Code Manuals (Vertex AI Search) for: '{query}'")

    # Create a client
    client = discoveryengine.SearchServiceClient()

    project=GOOGLE_CLOUD_PROJECT
    location=GOOGLE_CLOUD_LOCATION
    data_store=DATASTORE_ID

    # The full resource name of the search engine serving configuration
    serving_config = client.serving_config_path(
        project=project,
        location=location,
        data_store=data_store,
        serving_config="default_config",
    )

    # Construct the search request
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=3,  # Limit to the top 3 results to keep the context concise
    )

    try:
        response = client.search(request)
    except Exception as e:
        print(f"Error calling Vertex AI Search: {e}")
        return "An error occurred while searching the documentation."

    # Format the results into a string for the LLM
    results_str = f"Found {len(response.results)} results for '{query}':\n\n"
    for i, result in enumerate(response.results):
        doc = result.document
        title = doc.derived_struct_data.get("title", "No Title")
        link = doc.derived_struct_data.get("link", "")
        # Get the first snippet, which is usually the most relevant
        snippet = doc.derived_struct_data.get("snippets", [{}])[0].get("snippet", "No snippet available.")

        results_str += f"{i+1}. Title: {title}\n"
        results_str += f"   Link: {link}\n"
        results_str += f"   Snippet: {snippet.strip()}...\n\n"

    if not response.results:
        return "No relevant documents were found in the code manual for your query."
    print('HERE')
    print(results_str)
    return results_str


# Wrap the function in a FunctionTool so the agent can use it
code_manual_tool = FunctionTool(func=search_code_manual)