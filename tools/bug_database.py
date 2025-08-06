from google.adk.tools import FunctionTool


def get_bug_database(query: str) -> str:
    """
    Searches the bug and issue database (BigQuery) for similar problems.
    Use this to find existing bug reports, their status, and potential workarounds.
    """
    print(f"TOOL: Searching Bug Database (BigQuery) for: '{query}'")
    # In a real implementation, this would connect to the BigQuery client
    # and execute a query.
    return f"Found 3 related bugs in the database for '{query}'. The top result is Bug #12345: 'Fix for NoneType error on get()'."


bug_database_tool = FunctionTool(func=get_bug_database)


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


# tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)

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
# bigquery_toolset = BigQueryToolset(
#     credentials_config=credentials_config, bigquery_tool_config=tool_config
# )
