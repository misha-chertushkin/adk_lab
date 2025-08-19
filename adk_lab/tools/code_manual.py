from google.adk.tools import FunctionTool
from google.cloud import discoveryengine_v1 as discoveryengine

from adk_lab.utils.proxy import DATASTORE_ID, GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT


def search_code_manual(query: str) -> str:
    """
    Searches the code manuals and documentation (Vertex AI Search) for solutions.
    Use this to find relevant articles, code examples, and best practices.
    Returns a formatted string of the top search results.
    """
    print(f"TOOL: Searching Code Manuals (Vertex AI Search) for: '{query}'")

    # Create a client
    client = discoveryengine.SearchServiceClient()

    project = GOOGLE_CLOUD_PROJECT
    location = "global"  # we always use global in this lab for VAIS to simplify the flow, in real world use GOOGLE_CLOUD_LOCATION
    data_store = DATASTORE_ID

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
    return results_str


# Wrap the function in a FunctionTool so the agent can use it
code_manual_tool = FunctionTool(func=search_code_manual)
