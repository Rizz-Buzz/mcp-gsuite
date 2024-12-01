from collections.abc import Sequence
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from . import gauth
from . import gmail
import json

class ToolHandler():
    def __init__(self, tool_name: str):
        self.name = tool_name

    def get_tool_description(self) -> Tool:
        raise NotImplementedError()

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        raise NotImplementedError()
    

class GetUserInfoToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("get_gmail_user_info")

    def get_tool_description(self) -> Tool:
        return Tool(
           name=self.name,
           description="""Returns the gmail user info.""",
           inputSchema={
               "type": "object",
               "properties": {},
               "required": []
           }
       )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        credentials = gauth.get_stored_credentials()
        user_info = gauth.get_user_info(credentials=credentials)
        return [
            TextContent(
                type="text",
                text=json.dumps(user_info, indent=2)
            )
        ]
    
class ReadEmailsToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("read_gmail_emails")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Reads Gmail emails based on an optional search query. Returns emails in reverse chronological order (newest first).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": """Gmail search query (optional). Examples:
                            - 'is:unread' for unread emails
                            - 'from:example@gmail.com' for emails from a specific sender
                            - 'newer_than:2d' for emails from last 2 days
                            - 'has:attachment' for emails with attachments
                            If not provided, returns recent emails without filtering.""",
                        "required": False
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to retrieve (1-500)",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 100
                    }
                },
                "required": []
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        gmail_service = gmail.GmailService()
        query = args.get('query')
        max_results = args.get('max_results', 100)
        emails = gmail_service.read_emails(query=query, max_results=max_results)

        return [
            TextContent(
                type="text",
                text=json.dumps(emails, indent=2)
            )
        ]