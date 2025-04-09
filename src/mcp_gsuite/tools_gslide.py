from collections.abc import Sequence
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from . import gslide as gslides
import json
from . import toolhandler
import base64
import io

def decode_base64_data(file_data):
    standard_base64_data = file_data.replace("-", "+").replace("_", "/")
    missing_padding = len(standard_base64_data) % 4
    if missing_padding:
        standard_base64_data += '=' * (4 - missing_padding)
    return base64.b64decode(standard_base64_data, validate=True)

class ListPresentationsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("list_google_presentations")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""List Google Slides presentations owned by the user.
            Returns metadata such as title, creation date, and modification date.
            Results are sorted by last modified date, with most recently modified presentations first.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of presentations to retrieve (1-1000)",
                        "minimum": 1,
                        "maximum": 1000,
                        "default": 50
                    }
                },
                "required": [toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        max_results = args.get('max_results', 50)
        presentations = slides_service.list_presentations(max_results=max_results)

        if presentations is None:
            return [
                TextContent(
                    type="text",
                    text="Failed to retrieve presentations"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(presentations, indent=2)
            )
        ]

class GetPresentationToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("get_google_presentation")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Retrieves a Google Slides presentation by its ID, including metadata and content structure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "find_text": {
                        "type": "string",
                        "description": "The text to find"
                    },
                    "replace_text": {
                        "type": "string",
                        "description": "The text to replace it with"
                    },
                    "match_case": {
                        "type": "boolean",
                        "description": "Whether to match case",
                        "default": False
                    }
                },
                "required": ["presentation_id", "find_text", "replace_text", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["presentation_id", "find_text", "replace_text"]
        if not all(key in args for key in required):
            missing = [key for key in required if key not in args]
            raise RuntimeError(f"Missing required arguments: {', '.join(missing)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.replace_all_text(
            presentation_id=args["presentation_id"],
            find_text=args["find_text"],
            replace_text=args["replace_text"],
            match_case=args.get("match_case", False)
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to replace text in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class AddSpeakerNotesToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("add_speaker_notes_google_slide")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Adds or updates speaker notes for a slide in a Google Slides presentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide"
                    },
                    "notes": {
                        "type": "string",
                        "description": "The speaker notes content"
                    }
                },
                "required": ["presentation_id", "slide_id", "notes", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["presentation_id", "slide_id", "notes"]
        if not all(key in args for key in required):
            missing = [key for key in required if key not in args]
            raise RuntimeError(f"Missing required arguments: {', '.join(missing)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.add_speaker_notes(
            presentation_id=args["presentation_id"],
            slide_id=args["slide_id"],
            notes=args["notes"]
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to add speaker notes to slide {args['slide_id']} in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class GetSlideNotesToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("get_speaker_notes_google_slide")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Retrieves the speaker notes for a specific slide in a Google Slides presentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide"
                    }
                },
                "required": ["presentation_id", "slide_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "presentation_id" not in args or "slide_id" not in args:
            raise RuntimeError("Missing required arguments: presentation_id and slide_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        notes = slides_service.get_slide_notes(
            presentation_id=args["presentation_id"],
            slide_id=args["slide_id"]
        )

        if notes is None:
            return [
                TextContent(
                    type="text",
                    text=f"No speaker notes found for slide {args['slide_id']} or failed to retrieve notes"
                )
            ]

        return [
            TextContent(
                type="text",
                text=notes
            )
        ]

class ExportPdfToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("export_google_presentation_pdf")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Exports a Google Slides presentation as a PDF file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation to export"
                    },
                    "filename": {
                        "type": "string",
                        "description": "The filename for the exported PDF"
                    }
                },
                "required": ["presentation_id", "filename", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "presentation_id" not in args or "filename" not in args:
            raise RuntimeError("Missing required arguments: presentation_id and filename")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        pdf_data = slides_service.export_pdf(args["presentation_id"])

        if pdf_data is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to export presentation {args['presentation_id']} as PDF"
                )
            ]

        # Create a resource with the PDF data
        filename = args["filename"]
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'

        return [
            EmbeddedResource(
                type="resource",
                resource={
                    "blob": base64.b64encode(pdf_data).decode('utf-8'),
                    "uri": f"attachment://slides/{args['presentation_id']}/{filename}",
                    "mimeType": "application/pdf",
                },
            )
        ]

class SharePresentationToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("share_google_presentation")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Shares a Google Slides presentation with another user with specified permissions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation to share"
                    },
                    "email": {
                        "type": "string",
                        "description": "The email address of the user to share with"
                    },
                    "role": {
                        "type": "string",
                        "description": "The role to grant to the user",
                        "enum": ["owner", "organizer", "fileOrganizer", "writer", "commenter", "reader"],
                        "default": "reader"
                    }
                },
                "required": ["presentation_id", "email", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "presentation_id" not in args or "email" not in args:
            raise RuntimeError("Missing required arguments: presentation_id and email")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.share_presentation(
            presentation_id=args["presentation_id"],
            email=args["email"],
            role=args.get("role", "reader")
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to share presentation {args['presentation_id']} with {args['email']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class AddChartToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("add_chart_google_slide")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Adds a chart from Google Sheets to a Google Slides slide.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide"
                    },
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The ID of the spreadsheet containing the chart"
                    },
                    "sheet_id": {
                        "type": "integer",
                        "description": "The ID of the sheet containing the chart"
                    },
                    "chart_id": {
                        "type": "integer",
                        "description": "The ID of the chart to add"
                    },
                    "width": {
                        "type": "number",
                        "description": "The width of the chart in points",
                        "default": 400.0
                    },
                    "height": {
                        "type": "number",
                        "description": "The height of the chart in points",
                        "default": 300.0
                    },
                    "x_pos": {
                        "type": "number",
                        "description": "The x-coordinate position in points",
                        "default": 100.0
                    },
                    "y_pos": {
                        "type": "number",
                        "description": "The y-coordinate position in points",
                        "default": 100.0
                    }
                },
                "required": ["presentation_id", "slide_id", "spreadsheet_id", "sheet_id", "chart_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["presentation_id", "slide_id", "spreadsheet_id", "sheet_id", "chart_id"]
        if not all(key in args for key in required):
            missing = [key for key in required if key not in args]
            raise RuntimeError(f"Missing required arguments: {', '.join(missing)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.add_chart(
            presentation_id=args["presentation_id"],
            slide_id=args["slide_id"],
            spreadsheet_id=args["spreadsheet_id"],
            sheet_id=args["sheet_id"],
            chart_id=args["chart_id"],
            width=args.get("width", 400.0),
            height=args.get("height", 300.0),
            x_pos=args.get("x_pos", 100.0),
            y_pos=args.get("y_pos", 100.0)
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to add chart to slide {args['slide_id']} in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class AddVideoToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("add_video_google_slide")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Adds a YouTube video to a Google Slides slide.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide"
                    },
                    "video_url": {
                        "type": "string",
                        "description": "The URL of the YouTube video to add"
                    },
                    "width": {
                        "type": "number",
                        "description": "The width of the video in points",
                        "default": 400.0
                    },
                    "height": {
                        "type": "number",
                        "description": "The height of the video in points",
                        "default": 300.0
                    },
                    "x_pos": {
                        "type": "number",
                        "description": "The x-coordinate position in points",
                        "default": 100.0
                    },
                    "y_pos": {
                        "type": "number",
                        "description": "The y-coordinate position in points",
                        "default": 100.0
                    }
                },
                "required": ["presentation_id", "slide_id", "video_url", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["presentation_id", "slide_id", "video_url"]
        if not all(key in args for key in required):
            missing = [key for key in required if key not in args]
            raise RuntimeError(f"Missing required arguments: {', '.join(missing)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.add_video(
            presentation_id=args["presentation_id"],
            slide_id=args["slide_id"],
            video_url=args["video_url"],
            width=args.get("width", 400.0),
            height=args.get("height", 300.0),
            x_pos=args.get("x_pos", 100.0),
            y_pos=args.get("y_pos", 100.0)
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to add video to slide {args['slide_id']} in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class GetThumbnailsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("get_google_slide_thumbnails")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Gets thumbnails for slides in a Google Slides presentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of a specific slide to get thumbnail for (optional)",
                        "required": False
                    },
                    "thumbnail_size": {
                        "type": "string",
                        "description": "The size of thumbnails to generate",
                        "enum": ["SMALL", "MEDIUM", "LARGE"],
                        "default": "MEDIUM"
                    }
                },
                "required": ["presentation_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "presentation_id" not in args:
            raise RuntimeError("Missing required argument: presentation_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        thumbnail_properties = {
            "thumbnailSize": args.get("thumbnail_size", "MEDIUM")
        }
        
        result = slides_service.get_thumbnails(
            presentation_id=args["presentation_id"],
            slide_id=args.get("slide_id"),
            thumbnail_properties=thumbnail_properties
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to get thumbnails for presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class CreatePresentationFromTemplateToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("create_google_presentation_from_template")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Creates a new Google Slides presentation from an existing template.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "template_id": {
                        "type": "string",
                        "description": "The ID of the template presentation"
                    },
                    "title": {
                        "type": "string",
                        "description": "The title for the new presentation"
                    }
                },
                "required": ["template_id", "title", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "template_id" not in args or "title" not in args:
            raise RuntimeError("Missing required arguments: template_id and title")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        presentation = slides_service.create_presentation_from_template(
            template_id=args["template_id"],
            title=args["title"]
        )

        if presentation is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to create presentation from template {args['template_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(presentation, indent=2)
            )
        ]

class MergePresentationsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("merge_google_presentations")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Merges all slides from one Google Slides presentation into another.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "target_presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation to merge into"
                    },
                    "source_presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation to merge from"
                    }
                },
                "required": ["target_presentation_id", "source_presentation_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "target_presentation_id" not in args or "source_presentation_id" not in args:
            raise RuntimeError("Missing required arguments: target_presentation_id and source_presentation_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.merge_presentation(
            target_presentation_id=args["target_presentation_id"],
            source_presentation_id=args["source_presentation_id"]
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to merge presentation {args['source_presentation_id']} into {args['target_presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class CreatePresentationToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("create_google_presentation")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Creates a new Google Slides presentation with the specified title.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "title": {
                        "type": "string",
                        "description": "The title for the new presentation"
                    }
                },
                "required": ["title", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "title" not in args:
            raise RuntimeError("Missing required argument: title")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        presentation = slides_service.create_presentation(args["title"])

        if presentation is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to create presentation with title: {args['title']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(presentation, indent=2)
            )
        ]

class CreateSlideToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("create_google_slide")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Creates a new slide in the specified Google Slides presentation with the selected layout.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation to add the slide to"
                    },
                    "layout": {
                        "type": "string",
                        "description": "The predefined layout type for the slide",
                        "enum": [
                            "TITLE_AND_BODY",
                            "TITLE_ONLY",
                            "BLANK",
                            "TITLE_AND_TWO_COLUMNS",
                            "MAIN_POINT",
                            "SECTION_HEADER",
                            "CAPTION_ONLY"
                        ],
                        "default": "TITLE_AND_BODY"
                    }
                },
                "required": ["presentation_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "presentation_id" not in args:
            raise RuntimeError("Missing required argument: presentation_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        layout = args.get("layout", "TITLE_AND_BODY")
        result = slides_service.create_slide(args["presentation_id"], layout=layout)

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to create slide in presentation: {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class AddTextToSlideToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("add_text_to_google_slide")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Adds text to a specific shape or text box in a Google Slides slide.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide"
                    },
                    "shape_id": {
                        "type": "string",
                        "description": "The ID of the shape or text box to add text to"
                    },
                    "text": {
                        "type": "string",
                        "description": "The text content to add"
                    },
                    "text_style": {
                        "type": "object",
                        "description": "Optional style parameters for the text (fontSize, bold, italic, etc.)",
                        "properties": {
                            "bold": {"type": "boolean"},
                            "italic": {"type": "boolean"},
                            "underline": {"type": "boolean"},
                            "fontSize": {"type": "object", "properties": {"magnitude": {"type": "number"}, "unit": {"type": "string", "enum": ["PT"]}}}
                        }
                    }
                },
                "required": ["presentation_id", "slide_id", "shape_id", "text", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["presentation_id", "slide_id", "shape_id", "text"]
        if not all(key in args for key in required):
            missing = [key for key in required if key not in args]
            raise RuntimeError(f"Missing required arguments: {', '.join(missing)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        text_style = args.get("text_style")
        
        result = slides_service.add_text_to_slide(
            presentation_id=args["presentation_id"],
            slide_id=args["slide_id"],
            shape_id=args["shape_id"],
            text=args["text"],
            text_style=text_style
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to add text to slide {args['slide_id']} in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class CreateShapeToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("create_google_slide_shape")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Creates a shape on a specific slide in a Google Slides presentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide"
                    },
                    "shape_type": {
                        "type": "string",
                        "description": "The type of shape to create",
                        "enum": [
                            "RECTANGLE", 
                            "ELLIPSE", 
                            "TEXT_BOX", 
                            "ROUNDED_RECTANGLE", 
                            "DIAMOND",
                            "TRIANGLE",
                            "RIGHT_TRIANGLE"
                        ],
                        "default": "RECTANGLE"
                    },
                    "width": {
                        "type": "number",
                        "description": "The width of the shape in points",
                        "default": 350.0
                    },
                    "height": {
                        "type": "number",
                        "description": "The height of the shape in points",
                        "default": 100.0
                    },
                    "x_pos": {
                        "type": "number",
                        "description": "The x-coordinate position in points",
                        "default": 100.0
                    },
                    "y_pos": {
                        "type": "number",
                        "description": "The y-coordinate position in points",
                        "default": 100.0
                    }
                },
                "required": ["presentation_id", "slide_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "presentation_id" not in args or "slide_id" not in args:
            raise RuntimeError("Missing required arguments: presentation_id and slide_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.create_shape(
            presentation_id=args["presentation_id"],
            slide_id=args["slide_id"],
            shape_type=args.get("shape_type", "RECTANGLE"),
            width=args.get("width", 350.0),
            height=args.get("height", 100.0),
            x_pos=args.get("x_pos", 100.0),
            y_pos=args.get("y_pos", 100.0)
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to create shape on slide {args['slide_id']} in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class InsertImageToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("insert_google_slide_image")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Inserts an image into a Google Slides slide from a URL or binary data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide"
                    },
                    "image_url": {
                        "type": "string",
                        "description": "The URL of the image to insert"
                    },
                    "width": {
                        "type": "number",
                        "description": "The width of the image in points",
                        "default": 400.0
                    },
                    "height": {
                        "type": "number",
                        "description": "The height of the image in points",
                        "default": 300.0
                    },
                    "x_pos": {
                        "type": "number",
                        "description": "The x-coordinate position in points",
                        "default": 100.0
                    },
                    "y_pos": {
                        "type": "number",
                        "description": "The y-coordinate position in points",
                        "default": 100.0
                    }
                },
                "required": ["presentation_id", "slide_id", "image_url", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["presentation_id", "slide_id", "image_url"]
        if not all(key in args for key in required):
            missing = [key for key in required if key not in args]
            raise RuntimeError(f"Missing required arguments: {', '.join(missing)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.insert_image(
            presentation_id=args["presentation_id"],
            slide_id=args["slide_id"],
            image_url=args["image_url"],
            width=args.get("width", 400.0),
            height=args.get("height", 300.0),
            x_pos=args.get("x_pos", 100.0),
            y_pos=args.get("y_pos", 100.0)
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to insert image on slide {args['slide_id']} in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class CreateTableToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("create_google_slide_table")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Creates a table on a specific slide in a Google Slides presentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide"
                    },
                    "rows": {
                        "type": "integer",
                        "description": "Number of rows in the table",
                        "minimum": 1,
                        "default": 3
                    },
                    "cols": {
                        "type": "integer",
                        "description": "Number of columns in the table",
                        "minimum": 1,
                        "default": 3
                    },
                    "width": {
                        "type": "number",
                        "description": "The width of the table in points",
                        "default": 400.0
                    },
                    "height": {
                        "type": "number",
                        "description": "The height of the table in points",
                        "default": 300.0
                    },
                    "x_pos": {
                        "type": "number",
                        "description": "The x-coordinate position in points",
                        "default": 100.0
                    },
                    "y_pos": {
                        "type": "number",
                        "description": "The y-coordinate position in points",
                        "default": 100.0
                    }
                },
                "required": ["presentation_id", "slide_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "presentation_id" not in args or "slide_id" not in args:
            raise RuntimeError("Missing required arguments: presentation_id and slide_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.create_table(
            presentation_id=args["presentation_id"],
            slide_id=args["slide_id"],
            rows=args.get("rows", 3),
            cols=args.get("cols", 3),
            width=args.get("width", 400.0),
            height=args.get("height", 300.0),
            x_pos=args.get("x_pos", 100.0),
            y_pos=args.get("y_pos", 100.0)
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to create table on slide {args['slide_id']} in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class UpdateTableCellToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("update_google_slide_table_cell")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Updates the content of a table cell in a Google Slides presentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "table_id": {
                        "type": "string",
                        "description": "The ID of the table"
                    },
                    "row_idx": {
                        "type": "integer",
                        "description": "The row index (0-based)",
                        "minimum": 0
                    },
                    "col_idx": {
                        "type": "integer",
                        "description": "The column index (0-based)",
                        "minimum": 0
                    },
                    "text": {
                        "type": "string",
                        "description": "The text content to insert into the cell"
                    }
                },
                "required": ["presentation_id", "table_id", "row_idx", "col_idx", "text", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["presentation_id", "table_id", "row_idx", "col_idx", "text"]
        if not all(key in args for key in required):
            missing = [key for key in required if key not in args]
            raise RuntimeError(f"Missing required arguments: {', '.join(missing)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        
        result = slides_service.update_table_cell(
            presentation_id=args["presentation_id"],
            table_id=args["table_id"],
            row_idx=args["row_idx"],
            col_idx=args["col_idx"],
            text=args["text"]
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to update table cell ({args['row_idx']}, {args['col_idx']}) in table {args['table_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class DeleteSlideToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("delete_google_slide")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Deletes a slide from a Google Slides presentation. This action cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide to delete"
                    }
                },
                "required": ["presentation_id", "slide_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "presentation_id" not in args or "slide_id" not in args:
            raise RuntimeError("Missing required arguments: presentation_id and slide_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        result = slides_service.delete_slide(args["presentation_id"], args["slide_id"])

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to delete slide {args['slide_id']} from presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class DuplicateSlideToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("duplicate_google_slide")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Duplicates a slide in a Google Slides presentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide to duplicate"
                    }
                },
                "required": ["presentation_id", "slide_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "presentation_id" not in args or "slide_id" not in args:
            raise RuntimeError("Missing required arguments: presentation_id and slide_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        result = slides_service.duplicate_slide(args["presentation_id"], args["slide_id"])

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to duplicate slide {args['slide_id']} in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class ReorderSlideToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("reorder_google_slide")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Reorders a slide to a new position in a Google Slides presentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide to reorder"
                    },
                    "new_position": {
                        "type": "integer",
                        "description": "The new position for the slide (0-based)",
                        "minimum": 0
                    }
                },
                "required": ["presentation_id", "slide_id", "new_position", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["presentation_id", "slide_id", "new_position"]
        if not all(key in args for key in required):
            missing = [key for key in required if key not in args]
            raise RuntimeError(f"Missing required arguments: {', '.join(missing)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        slides_service = gslides.GoogleSlidesService(user_id=user_id)
        result = slides_service.reorder_slide(
            presentation_id=args["presentation_id"],
            slide_id=args["slide_id"],
            new_position=args["new_position"]
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to reorder slide {args['slide_id']} in presentation {args['presentation_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class ReplaceAllTextToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("replace_all_text_google_presentation")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Inserts an image into a Google Slides slide from a URL or binary data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "presentation_id": {
                        "type": "string",
                        "description": "The ID of the presentation"
                    },
                    "slide_id": {
                        "type": "string",
                        "description": "The ID of the slide"
                    },
                    "image_url": {
                        "type": "string",
                        "description": "The URL of the image to insert"
                    },
                    "width": {
                        "type": "number",
                        "description": "The width of the image in points",
                        "default": 400.0
                    },
                    "height": {
                        "type": "number",
                        "description": "The height of the image in points",
                        "default": 300.0
                    },
                    "x_pos": {
                        "type": "number",
                        "description": "The x-coordinate position in points",
                        "default": 100.0
                    },
                    "y_pos": {
                        "type": "number",
                        "description": "The y-coordinate position in points",
                        "default": 100.0
                    }
                },
                "required": ["presentation_id", "slide_id", "image_url", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["presentation_id", "slide_id", "image_url"]
        if not all(key in args for key in required):
            missing = [key for key in required if key not in args]
            raise RuntimeError(f"Missing required arguments: {', '.join(missing)}")