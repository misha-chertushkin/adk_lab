from google.adk.tools import FunctionTool
import os

# from google.adk.auth import AuthCredentialTypes
# from google.adk.tools.bigquery import BigQueryCredentialsConfig
# from google.adk.tools.bigquery import BigQueryToolset
# from google.adk.tools.bigquery.config import BigQueryToolConfig
# from google.adk.tools.bigquery.config import WriteMode
# import google.auth

# # Define an appropriate credential type
# CREDENTIALS_TYPE = AuthCredentialTypes.HTTP

# # Write modes define BigQuery access control of agent:
# # ALLOWED: Tools will have full write capabilites.
# # BLOCKED: Default mode. Effectively makes the tool read-only.
# # PROTECTED: Only allows writes on temporary data for a given BigQuery session.


# tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

# if CREDENTIALS_TYPE == AuthCredentialTypes.OAUTH2:
#   # Initiaze the tools to do interactive OAuth
#   credentials_config = BigQueryCredentialsConfig(
#       client_id=os.getenv("OAUTH_CLIENT_ID"),
#       client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
#   )
# elif CREDENTIALS_TYPE == AuthCredentialTypes.SERVICE_ACCOUNT:
#   # Initialize the tools to use the credentials in the service account key.
#   creds, _ = google.auth.load_credentials_from_file("service_account_key.json")
#   credentials_config = BigQueryCredentialsConfig(credentials=creds)
# else:
#   # Initialize the tools to use the application default credentials.
#   application_default_credentials, _ = google.auth.default()
#   credentials_config = BigQueryCredentialsConfig(
#       credentials=application_default_credentials
#   )

# # Instantiate a BigQuery toolset
# bug_database_tool = BigQueryToolset(
#     credentials_config=credentials_config, bigquery_tool_config=tool_config
# )


import os
from google.cloud import bigquery
from vertexai.language_models import TextEmbeddingModel
from google.adk.tools import FunctionTool

# --- Configuration ---
# Make sure to set these to your actual project, dataset, and table names.
import dotenv
from google.cloud import secretmanager
import os

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
    BIGQUERY_DATASET = get_secret(GOOGLE_CLOUD_PROJECT, "BIGQUERY_DATASET")
    BIGQUERY_TABLE = get_secret(GOOGLE_CLOUD_PROJECT, "BIGQUERY_TABLE")
    BIGQUERY_LOCATION = get_secret(GOOGLE_CLOUD_PROJECT,"BIGQUERY_LOCATION")
    EMBEDDING_MODEL = get_secret(GOOGLE_CLOUD_PROJECT, "EMBEDDING_MODEL")
else:
    # we are deloyed locally, reading from .env
    dotenv.load_dotenv()
    GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
    BIGQUERY_DATASET = os.environ["BIGQUERY_DATASET"]
    BIGQUERY_TABLE = os.environ["BIGQUERY_TABLE"]
    BIGQUERY_LOCATION = os.environ["BIGQUERY_LOCATION"]
    EMBEDDING_MODEL = os.environ["EMBEDDING_MODEL"]

# Initialize clients once to reuse them.
bq_client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)


def find_similar_bugs(bug_description: str) -> str:
    """
    Performs a semantic search in the BigQuery bug database to find bugs
    with descriptions similar to the user's query.

    Args:
        bug_description: The description of the new bug to search for.

    Returns:
        A formatted string of the top 3 most similar bugs found, or a message
        if no similar bugs are found.
    """
    print(f"TOOL: Received search query: '{bug_description}'")

    # 1. Generate an embedding for the incoming bug description
    print("TOOL: Generating embedding for the query...")
    try:
        # The model expects a list of texts and returns a list of embeddings
        embeddings = embedding_model.get_embeddings([bug_description])
        query_embedding = embeddings[0].values
    except Exception as e:
        return f"Error: Could not generate text embedding. Details: {e}"

    # 2. Construct and run the VECTOR_SEARCH query
    # This query finds the top 3 bugs with the smallest cosine distance to our query embedding.
    sql_query = f"""
    SELECT
      base.title,
      base.description,
      distance
    FROM
      VECTOR_SEARCH(
        TABLE `{GOOGLE_CLOUD_PROJECT}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`,
        'description_embedding',  -- The column containing the vectors
        (SELECT @query_embedding AS embedding),
        top_k => 3,
        distance_type => 'COSINE'
      )
    """

    # 3. Execute the query with parameters to prevent SQL injection
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
        ]
    )

    print("TOOL: Executing BigQuery vector search...")
    try:
        query_job = bq_client.query(sql_query, job_config=job_config)
        results = query_job.result()  # Waits for the job to complete
    except Exception as e:
        print("HERE", e)
        return f"Error: BigQuery search failed. Details: {e}"

    # 4. Format the results into a clean string for the agent
    if results.total_rows == 0:
        return "No similar bugs were found in the database."

    response_parts = ["Found similar bugs:\n"]
    for i, row in enumerate(results):
        response_parts.append(
            f"{i+1}. Title: {row.title}\n"
            f"   Description: {row.description}\n"
            f"   (Similarity Score/Distance: {row.distance:.4f})\n"  # Lower distance is more similar
        )

    result = "\n".join(response_parts)
    # print(result)
    return result


# 5. Wrap the function in a FunctionTool for the agent to use
bug_database_tool = FunctionTool(func=find_similar_bugs)
