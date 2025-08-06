from google.adk.tools import FunctionTool


def get_code_manual(query: str) -> str:
    """
    Searches the code manuals and documentation (Vertex AI Search) for solutions.
    Use this to understand functions, classes, and find official code examples.
    """
    print(f"TOOL: Searching Code Manuals (Vertex AI Search) for: '{query}'")
    # In a real implementation, this would call the Vertex AI Search API.
    return f"The code manual has an article on 'Handling NoneType Errors' that might be relevant to '{query}'."


code_manual_tool = FunctionTool(func=get_code_manual)