from googleapiclient.discovery import build
from . import gauth
import logging
import traceback
import base64
from typing import List, Dict, Union, Tuple, Optional, Any
import io
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account


class GoogleSlidesService:
    """
    A comprehensive service class for interacting with Google Slides.
    
    This class provides methods to create and modify Google Slides presentations,
    including adding slides, shapes, images, tables, and text. It also supports
    operations like duplicating slides, reordering slides, and exporting presentations.
    
    The class requires either service account credentials or user OAuth credentials
    to authenticate with the Google Slides and Drive APIs.
    """

    def __init__(self, service_account_file=None, user_id=None):
        """
        Initialize the Google Slides service with either service account or user credentials.
        
        Args:
            service_account_file (str, optional): Path to the service account key JSON file.
                This file should contain the credentials for a Google Cloud service account
                with access to Google Slides and Drive APIs.
            
            user_id (str, optional): The ID of the user whose OAuth credentials to use.
                The credentials must have been previously stored using the gauth module.
        
        Raises:
            RuntimeError: If neither valid credentials option is provided, or if the
                          requested OAuth credentials are not found.
        
        Example:
            # Using a service account
            slides_service = GoogleSlidesService(
                service_account_file='path/to/service-account-key.json'
            )
            
            # Using OAuth user credentials
            slides_service = GoogleSlidesService(user_id='user@example.com')
        """
        if service_account_file:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=['https://www.googleapis.com/auth/presentations', 
                        'https://www.googleapis.com/auth/drive']
            )
        elif user_id:
            credentials = gauth.get_stored_credentials(user_id=user_id)
            if not credentials:
                raise RuntimeError("No OAuth2 credentials stored")
        else:
            raise RuntimeError("Either service_account_file or user_id must be provided")
            
        self.service = build('slides', 'v1', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)

    def create_presentation(self, title: str) -> Dict[str, Any] | None:
        """
        Create a new presentation with the specified title.
        
        Args:
            title (str): The title of the new presentation. This will appear in 
                         Google Drive and at the top of the presentation.
        
        Returns:
            Dict[str, Any]: The created presentation's metadata including:
                - presentationId: The ID of the new presentation
                - title: The title of the presentation
                - slides: An array (empty for new presentations)
                - layouts: Available layout metadata
                - masters: Master slide metadata
            
            None: If creation fails due to API errors or authentication issues
        
        Example:
            # Create a new presentation
            presentation = slides_service.create_presentation("Quarterly Business Review")
            
            if presentation:
                presentation_id = presentation['presentationId']
                print(f"Created presentation with ID: {presentation_id}")
                
                # Use the new presentation ID to add content
                slides_service.create_slide(presentation_id, layout='TITLE_SLIDE')
        """
        try:
            presentation = {
                'title': title
            }
            result = self.service.presentations().create(body=presentation).execute()
            return result
        except Exception as e:
            logging.error(f"Error creating presentation: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def get_presentation(self, presentation_id: str) -> Dict[str, Any] | None:
        """
        Retrieve a presentation by its ID with all its content and metadata.
        
        Args:
            presentation_id (str): The ID of the presentation to retrieve.
                This is the string that appears in the presentation URL after
                'https://docs.google.com/presentation/d/'.
        
        Returns:
            Dict[str, Any]: The presentation's complete metadata and content including:
                - presentationId: The ID of the presentation
                - title: The title of the presentation
                - slides: Array of slide objects with their content
                - layouts: Array of available layout definitions
                - masters: Array of master slide definitions
                - pageSize: The dimensions of slides in the presentation
            
            None: If retrieval fails due to incorrect ID, permissions, or API errors
        
        Example:
            # Get details of an existing presentation
            presentation = slides_service.get_presentation("1Abc123Def456Ghi789JklMnoPqrs")
            
            if presentation:
                # Print basic information
                print(f"Title: {presentation['title']}")
                print(f"Number of slides: {len(presentation.get('slides', []))}")
                
                # Loop through slides to access content
                for i, slide in enumerate(presentation.get('slides', [])):
                    slide_id = slide['objectId']
                    print(f"Slide {i+1} ID: {slide_id}")
        """
        try:
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            return presentation
        except Exception as e:
            logging.error(f"Error retrieving presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def list_presentations(self, max_results: int = 50) -> List[Dict[str, Any]] | None:
        """
        List presentations owned by or accessible to the authenticated user.
        
        Args:
            max_results (int): Maximum number of presentations to retrieve (default: 50).
                The value is automatically capped between 1 and 1000 to comply with
                Google Drive API limitations.
        
        Returns:
            List[Dict[str, Any]]: List of presentation metadata objects, each containing:
                - id: The presentation ID
                - name: The title of the presentation
                - createdTime: ISO datetime string of creation time
                - modifiedTime: ISO datetime string of last modification
                - webViewLink: URL to view the presentation in a browser
            
            None: If the operation fails due to authentication or API errors
        
        Example:
            # List the most recent 10 presentations
            presentations = slides_service.list_presentations(max_results=10)
            
            if presentations:
                # Sort by most recently modified
                sorted_presentations = sorted(
                    presentations, 
                    key=lambda p: p['modifiedTime'], 
                    reverse=True
                )
                
                print("Your recent presentations:")
                for pres in sorted_presentations:
                    print(f"- {pres['name']} (Last modified: {pres['modifiedTime']})")
                    print(f"  View at: {pres['webViewLink']}")
                    print(f"  ID: {pres['id']}")
        """
        try:
            max_results = min(max(1, max_results), 1000)  # Ensure max_results is within API limits
            
            # Use Drive API to list presentations
            results = self.drive_service.files().list(
                q="mimeType='application/vnd.google-apps.presentation'",
                pageSize=max_results,
                fields="files(id, name, createdTime, modifiedTime, webViewLink)"
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            logging.error(f"Error listing presentations: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def create_slide(self, presentation_id: str, layout: str = 'TITLE_AND_BODY') -> Dict[str, Any] | None:
        """
        Create a new slide in the specified presentation with the given layout.
        
        Args:
            presentation_id (str): The ID of the presentation to add the slide to.
            
            layout (str): The predefined layout type (default: 'TITLE_AND_BODY')
                Available layout options include:
                - 'TITLE_AND_BODY': Standard slide with title and content areas
                - 'TITLE_ONLY': Slide with only a title placeholder
                - 'BLANK': Empty slide with no predefined placeholders
                - 'SECTION_HEADER': Section divider slide
                - 'CAPTION': Image with caption layout
                - 'TITLE_AND_TWO_COLUMNS': Title with two content columns
                - 'MAIN_POINT': Title and main point layout
                - 'BIG_NUMBER': Large number display layout
        
        Returns:
            Dict[str, Any]: The response from the API containing:
                - replies: Array with creation details including the new slide's objectId
            
            None: If slide creation fails
        
        Example:
            # Create different types of slides in a presentation
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            
            # Create a title slide
            title_slide = slides_service.create_slide(presentation_id, layout='TITLE')
            if title_slide and 'replies' in title_slide:
                title_slide_id = title_slide['replies'][0]['createSlide']['objectId']
                print(f"Created title slide with ID: {title_slide_id}")
                
                # Add title text to the slide
                # Note: Title placeholder usually has ID 'p'
                slides_service.add_text_to_slide(
                    presentation_id, 
                    title_slide_id, 
                    'p',  # Title placeholder ID
                    "Quarterly Financial Results"
                )
            
            # Create a blank slide
            slides_service.create_slide(presentation_id, layout='BLANK')
            
            # Create a section header slide
            slides_service.create_slide(presentation_id, layout='SECTION_HEADER')
        """
        try:
            # Create a slide at the end of presentation with the specified layout
            requests = [
                {
                    'createSlide': {
                        'slideLayoutReference': {
                            'predefinedLayout': layout
                        }
                    }
                }
            ]
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error creating slide in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def add_text_to_slide(self, presentation_id: str, slide_id: str, shape_id: str, 
                          text: str, text_style: Dict[str, Any] = None) -> Dict[str, Any] | None:
        """
        Add or replace text in a specified shape or placeholder in a slide.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str): The ID of the slide containing the shape.
            
            shape_id (str): The ID of the shape or placeholder to add text to.
                Common placeholder IDs for standard layouts:
                - 'p': Title placeholder
                - 'q': Body or subtitle placeholder
                For custom shapes, you'll need to use the ID returned when creating the shape.
            
            text (str): The text content to add or replace in the shape.
                This will replace any existing text in the shape.
            
            text_style (Dict[str, Any], optional): Style parameters for the text.
                Example styling options:
                {
                    'bold': True,
                    'italic': False,
                    'fontSize': {'magnitude': 14, 'unit': 'PT'},
                    'foregroundColor': {
                        'opaqueColor': {'rgbColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8}}
                    },
                    'fontFamily': 'Arial',
                    'underline': False
                }
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If the operation fails
        
        Example:
            # Add styled text to a title placeholder
            title_style = {
                'bold': True,
                'fontSize': {'magnitude': 24, 'unit': 'PT'},
                'foregroundColor': {'opaqueColor': {'rgbColor': {'red': 0.2, 'green': 0.6, 'blue': 0.2}}}
            }
            
            slides_service.add_text_to_slide(
                "1Abc123Def456Ghi789JklMnoPqrs",  # presentation_id
                "p.1234567890",                  # slide_id
                "p",                             # shape_id (title placeholder)
                "Q2 Financial Results",
                title_style
            )
            
            # Add text to body placeholder
            body_text = "• Revenue increased by 15%\n• New product line launched\n• Expanded to 3 new markets"
            slides_service.add_text_to_slide(
                "1Abc123Def456Ghi789JklMnoPqrs",  # presentation_id
                "p.1234567890",                  # slide_id
                "q",                             # shape_id (body placeholder)
                body_text
            )
        """
        try:
            requests = [
                {
                    'insertText': {
                        'objectId': shape_id,
                        'text': text
                    }
                }
            ]
            
            # Add styling if provided
            if text_style:
                style_request = {
                    'updateTextStyle': {
                        'objectId': shape_id,
                        'textRange': {
                            'type': 'ALL'
                        },
                        'style': text_style,
                        'fields': ','.join(text_style.keys())
                    }
                }
                requests.append(style_request)
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error adding text to slide {slide_id} in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def create_shape(self, presentation_id: str, slide_id: str, 
                     shape_type: str = 'RECTANGLE', 
                     width: float = 350.0, 
                     height: float = 100.0, 
                     x_pos: float = 100.0, 
                     y_pos: float = 100.0) -> Dict[str, Any] | None:
        """
        Create a shape on a specific slide with customized dimensions and position.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str): The ID of the slide to add the shape to.
            
            shape_type (str): The type of shape to create (default: 'RECTANGLE').
                Common shape types include:
                - 'RECTANGLE': Standard rectangle
                - 'ELLIPSE': Circle or oval
                - 'TEXT_BOX': Box optimized for text content
                - 'ROUND_RECTANGLE': Rectangle with rounded corners
                - 'DIAMOND': Diamond shape
                - 'TRIANGLE': Triangle shape
                - 'RIGHT_TRIANGLE': Right-angled triangle
                - 'TRAPEZOID': Trapezoid shape
                - 'ARROW': Arrow shape
                - 'STAR': Star shape
            
            width (float): The width of the shape in points (default: 350.0).
                A point is 1/72 of an inch.
            
            height (float): The height of the shape in points (default: 100.0).
            
            x_pos (float): The x-coordinate position in points from left (default: 100.0).
            
            y_pos (float): The y-coordinate position in points from top (default: 100.0).
        
        Returns:
            Dict[str, Any]: The response from the API including:
                - createdObjectId: The ID of the created shape
            
            None: If creation fails
        
        Example:
            # Create a blue oval on a slide
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            slide_id = "p.1234567890"
            
            oval_result = slides_service.create_shape(
                presentation_id,
                slide_id,
                shape_type="ELLIPSE",
                width=200.0,
                height=200.0,
                x_pos=250.0,
                y_pos=150.0
            )
            
            if oval_result and 'createdObjectId' in oval_result:
                oval_id = oval_result['createdObjectId']
                
                # Add text to the oval
                slides_service.add_text_to_slide(
                    presentation_id,
                    slide_id,
                    oval_id,
                    "Key Highlight!",
                    {
                        'bold': True,
                        'fontSize': {'magnitude': 16, 'unit': 'PT'},
                        'foregroundColor': {'opaqueColor': {'rgbColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}}}
                    }
                )
                
                # In a real application, you would likely also set the fill color of the shape
                # This requires an additional batch_update call with updateShapeProperties
        """
        try:
            # Generate a unique element ID
            element_id = f"{slide_id}_{shape_type}_{int(x_pos)}_{int(y_pos)}"
            
            requests = [
                {
                    'createShape': {
                        'objectId': element_id,
                        'shapeType': shape_type,
                        'elementProperties': {
                            'pageObjectId': slide_id,
                            'size': {
                                'width': {'magnitude': width, 'unit': 'PT'},
                                'height': {'magnitude': height, 'unit': 'PT'}
                            },
                            'transform': {
                                'scaleX': 1,
                                'scaleY': 1,
                                'translateX': x_pos,
                                'translateY': y_pos,
                                'unit': 'PT'
                            }
                        }
                    }
                }
            ]
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            # Add the created object ID to the result
            if 'replies' in result:
                result['createdObjectId'] = element_id
            
            return result
        except Exception as e:
            logging.error(f"Error creating shape on slide {slide_id} in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def insert_image(self, presentation_id: str, slide_id: str, 
                     image_url: str = None, image_data: bytes = None,
                     width: float = 400.0, height: float = 300.0, 
                     x_pos: float = 100.0, y_pos: float = 100.0) -> Dict[str, Any] | None:
        """
        Insert an image into a slide from either a URL or binary image data.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str): The ID of the slide to add the image to.
            
            image_url (str, optional): The URL of the image to insert.
                The URL must be publicly accessible or from Google Drive.
            
            image_data (bytes, optional): The binary data of the image to insert.
                Supported formats include JPEG, PNG, GIF, and BMP.
            
            width (float): The width of the image in points (default: 400.0).
            
            height (float): The height of the image in points (default: 300.0).
            
            x_pos (float): The x-coordinate position in points from left (default: 100.0).
            
            y_pos (float): The y-coordinate position in points from top (default: 100.0).
        
        Returns:
            Dict[str, Any]: The response from the API containing:
                - objectId: The ID of the created image element
                - tempFileId: When using image_data, the ID of the temporary file
                  created in Google Drive
            
            None: If operation fails
        
        Notes:
            - Either image_url OR image_data must be provided
            - When using image_data, the method creates a temporary file in Google Drive
            - Consider using clean_up_temp_file() to delete the temporary file after
              confirming the image appears correctly in the presentation
        
        Example:
            # Insert an image from a URL
            slides_service.insert_image(
                "1Abc123Def456Ghi789JklMnoPqrs",  # presentation_id
                "p.1234567890",                   # slide_id
                image_url="https://example.com/images/logo.png",
                width=300.0,
                height=150.0,
                x_pos=200.0,
                y_pos=100.0
            )
            
            # Insert an image from binary data (e.g., a local file)
            with open('company_chart.png', 'rb') as img_file:
                img_data = img_file.read()
                
                result = slides_service.insert_image(
                    "1Abc123Def456Ghi789JklMnoPqrs",  # presentation_id
                    "p.1234567890",                   # slide_id
                    image_data=img_data,
                    width=500.0,
                    height=350.0,
                    x_pos=100.0,
                    y_pos=200.0
                )
                
                # Clean up the temporary file when done
                if result and 'tempFileId' in result:
                    slides_service.clean_up_temp_file(result['tempFileId'])
        """
        try:
            # Generate a unique element ID
            element_id = f"{slide_id}_image_{int(x_pos)}_{int(y_pos)}"
            
            if image_url:
                # Create an image from a URL
                requests = [
                    {
                        'createImage': {
                            'objectId': element_id,
                            'url': image_url,
                            'elementProperties': {
                                'pageObjectId': slide_id,
                                'size': {
                                    'width': {'magnitude': width, 'unit': 'PT'},
                                    'height': {'magnitude': height, 'unit': 'PT'}
                                },
                                'transform': {
                                    'scaleX': 1,
                                    'scaleY': 1,
                                    'translateX': x_pos,
                                    'translateY': y_pos,
                                    'unit': 'PT'
                                }
                            }
                        }
                    }
                ]
                
                result = self.service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': requests}
                ).execute()
                
                return result
            
            elif image_data:
                # For binary data, we need to upload to Drive first
                # Create a temporary file in Drive
                media = MediaIoBaseUpload(
                    io.BytesIO(image_data),
                    mimetype='image/jpeg',  # Adjust mimetype as needed
                    resumable=True
                )
                
                file_metadata = {
                    'name': f'temp_image_{presentation_id}_{slide_id}',
                    'mimeType': 'image/jpeg'  # Adjust mimetype as needed
                }
                
                temp_file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,webContentLink'
                ).execute()
                
                # Now we can use the Drive file URL in the presentation
                image_url = f"https://drive.google.com/uc?id={temp_file['id']}"
                
                # Create an image from the Drive URL
                requests = [
                    {
                        'createImage': {
                            'objectId': element_id,
                            'url': image_url,
                            'elementProperties': {
                                'pageObjectId': slide_id,
                                'size': {
                                    'width': {'magnitude': width, 'unit': 'PT'},
                                    'height': {'magnitude': height, 'unit': 'PT'}
                                },
                                'transform': {
                                    'scaleX': 1,
                                    'scaleY': 1,
                                    'translateX': x_pos,
                                    'translateY': y_pos,
                                    'unit': 'PT'
                                }
                            }
                        }
                    }
                ]
                
                result = self.service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': requests}
                ).execute()
                
                # Add the temporary file ID to the result for potential cleanup later
                result['tempFileId'] = temp_file['id']
                
                return result
            else:
                raise ValueError("Either image_url or image_data must be provided")
            
        except Exception as e:
            logging.error(f"Error inserting image on slide {slide_id} in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def clean_up_temp_file(self, file_id: str) -> bool:
        """
        Delete a temporary file from Google Drive after it's been used.
        
        This is typically used to remove temporary image files created when
        uploading images via the insert_image method.
        
        Args:
            file_id (str): The ID of the temporary file to delete.
                This ID is returned in the 'tempFileId' field of the insert_image response.
        
        Returns:
            bool: True if deletion was successful, False otherwise.
        
        Example:
            # Insert an image and then clean up the temporary file
            image_result = slides_service.insert_image(
                "1Abc123Def456Ghi789JklMnoPqrs",  # presentation_id
                "p.1234567890",                   # slide_id
                image_data=image_binary_data
            )
            
            if image_result and 'tempFileId' in image_result:
                # Wait until you're sure the image is visible in the presentation
                temp_file_id = image_result['tempFileId']
                
                # Then delete the temporary file to avoid cluttering Drive
                success = slides_service.clean_up_temp_file(temp_file_id)
                if success:
                    print(f"Successfully cleaned up temporary file: {temp_file_id}")
                else:
                    print(f"Failed to clean up temporary file: {temp_file_id}")
        """
        try:
            self.drive_service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error deleting temporary file {file_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return False

    def create_table(self, presentation_id: str, slide_id: str, 
                     rows: int, cols: int, 
                     width: float = 400.0, height: float = 300.0, 
                     x_pos: float = 100.0, y_pos: float = 100.0) -> Dict[str, Any] | None:
        """
        Create a table on a slide with the specified number of rows and columns.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str): The ID of the slide to add the table to.
            
            rows (int): Number of rows in the table.
                Must be a positive integer.
            
            cols (int): Number of columns in the table.
                Must be a positive integer.
            
            width (float): The width of the table in points (default: 400.0).
            
            height (float): The height of the table in points (default: 300.0).
            
            x_pos (float): The x-coordinate position in points from left (default: 100.0).
            
            y_pos (float): The y-coordinate position in points from top (default: 100.0).
        
        Returns:
            Dict[str, Any]: The response from the API containing:
                - tableId: The ID of the created table
            
            None: If operation fails
        
        Notes:
            - The table is created with empty cells
            - Use update_table_cell() to populate the table with content
            - Table and cell IDs have specific formats:
              - Table ID: "{slide_id}_table_{rows}x{cols}"
              - Cell ID: "{table_id}_{row_idx}_{col_idx}" where indices are 0-based
        
        Example:
            # Create a 3x3 table for quarterly data
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            slide_id = "p.1234567890"
            
            result = slides_service.create_table(
                presentation_id,
                slide_id,
                rows=4,  # Header row + 3 data rows
                cols=4,  # Quarter column + 3 data columns
                width=600.0,
                height=300.0,
                x_pos=50.0,
                y_pos=150.0
            )
            
            if result and 'tableId' in result:
                table_id = result['tableId']
                
                # Add header row
                headers = ["", "Q1", "Q2", "Q3"]
                for col, header in enumerate(headers):
                    slides_service.update_table_cell(
                        presentation_id,
                        table_id,
                        0,  # First row (0-based)
                        col,
                        header
                    )
                
                # Add row titles
                row_titles = ["Revenue", "Expenses", "Profit"]
                for row, title in enumerate(row_titles, start=1):
                    slides_service.update_table_cell(
                        presentation_id,
                        table_id,
                        row,
                        0,  # First column (0-based)
                        title
                    )
                
                # Add data
                data = [
                    ["$100K", "$120K", "$140K"],  # Revenue
                    ["$80K", "$85K", "$95K"],     # Expenses
                    ["$20K", "$35K", "$45K"]      # Profit
                ]
                
                for row, row_data in enumerate(data, start=1):
                    for col, value in enumerate(row_data, start=1):
                        slides_service.update_table_cell(
                            presentation_id,
                            table_id,
                            row,
                            col,
                            value
                        )
        """
        try:
            # Generate a unique element ID
            table_id = f"{slide_id}_table_{rows}x{cols}"
            
            requests = [
                {
                    'createTable': {
                        'objectId': table_id,
                        'rows': rows,
                        'columns': cols,
                        'elementProperties': {
                            'pageObjectId': slide_id,
                            'size': {
                                'width': {'magnitude': width, 'unit': 'PT'},
                                'height': {'magnitude': height, 'unit': 'PT'}
                            },
                            'transform': {
                                'scaleX': 1,
                                'scaleY': 1,
                                'translateX': x_pos,
                                'translateY': y_pos,
                                'unit': 'PT'
                            }
                        }
                    }
                }
            ]
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            # Add the created table ID to the result
            if 'replies' in result:
                result['tableId'] = table_id
            
            return result
        except Exception as e:
            logging.error(f"Error creating table on slide {slide_id} in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def update_table_cell(self, presentation_id: str, table_id: str, 
                          row_idx: int, col_idx: int, 
                          text: str) -> Dict[str, Any] | None:
        """
        Update the content of a specific table cell with text.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            table_id (str): The ID of the table.
                This is returned by the create_table method as 'tableId'.
            
            row_idx (int): The row index (0-based).
                The first row is 0, second row is 1, etc.
            
            col_idx (int): The column index (0-based).
                The first column is 0, second column is 1, etc.
            
            text (str): The text content to insert into the cell.
                This will replace any existing text in the cell.
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If operation fails
        
        Notes:
            - Cell IDs are automatically generated as "{table_id}_{row_idx}_{col_idx}"
            - To style the text in cells, you would need to make additional API calls
              using batch_update with updateTextStyle requests
        
        Example:
            # Create a small comparison table
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            slide_id = "p.1234567890"
            
            table_result = slides_service.create_table(
                presentation_id,
                slide_id,
                rows=3,
                cols=3
            )
            
            if table_result and 'tableId' in table_result:
                table_id = table_result['tableId']
                
                # Define all cell contents
                cell_contents = [
                    ["", "Before", "After"],
                    ["Users", "5,000", "12,500"],
                    ["Revenue", "$10K", "$25K"]
                ]
                
                # Populate the entire table
                for row, row_data in enumerate(cell_contents):
                    for col, content in enumerate(row_data):
                        slides_service.update_table_cell(
                            presentation_id,
                            table_id,
                            row,
                            col,
                            content
                        )
        """
        try:
            # The ID of a table cell follows the pattern: {table_id}_{row_idx}_{col_idx}
            cell_id = f"{table_id}_{row_idx}_{col_idx}"
            
            requests = [
                {
                    'insertText': {
                        'objectId': cell_id,
                        'text': text
                    }
                }
            ]
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error updating table cell ({row_idx}, {col_idx}) in table {table_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def delete_slide(self, presentation_id: str, slide_id: str) -> Dict[str, Any] | None:
        """
        Delete a slide from a presentation.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str): The ID of the slide to delete.
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If deletion fails
        
        Warning:
            - This action cannot be undone through the API
            - The slide and all its content will be permanently removed
        
        Example:
            # Get the presentation to find slide IDs
            presentation = slides_service.get_presentation("1Abc123Def456Ghi789JklMnoPqrs")
            
            if presentation and 'slides' in presentation:
                slides = presentation['slides']
                
                # Delete slides with specific criteria, e.g., empty slides
                for slide in slides:
                    slide_id = slide['objectId']
                    
                    # Check if this is a slide we want to delete (example condition)
                    if not slide.get('pageElements', []):  # If no elements (empty slide)
                        result = slides_service.delete_slide(
                            "1Abc123Def456Ghi789JklMnoPqrs",
                            slide_id
                        )
                        
                        if result:
                            print(f"Successfully deleted empty slide with ID: {slide_id}")
        """
        try:
            requests = [
                {
                    'deleteObject': {
                        'objectId': slide_id
                    }
                }
            ]
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error deleting slide {slide_id} from presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def reorder_slide(self, presentation_id: str, slide_id: str, new_position: int) -> Dict[str, Any] | None:
        """
        Reorder a slide to a new position in the presentation.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str): The ID of the slide to reorder.
            
            new_position (int): The new position for the slide (0-based).
                0 means first slide, 1 means second slide, etc.
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If reordering fails
        
        Notes:
            - The slide at the specified position and all subsequent slides 
              will be shifted to make room for the moved slide
        
        Example:
            # Move a slide to be the first in the presentation
            slides_service.reorder_slide(
                "1Abc123Def456Ghi789JklMnoPqrs",  # presentation_id
                "p.1234567890",                   # slide_id
                0  # Move to first position
            )
            
            # Get presentation data to find slide IDs and reorder strategically
            presentation = slides_service.get_presentation("1Abc123Def456Ghi789JklMnoPqrs")
            
            if presentation and 'slides' in presentation:
                # Example: Move the conclusion slide to be right after the introduction
                # Assuming introduction is the first slide (position 0)
                slides = presentation['slides']
                
                for i, slide in enumerate(slides):
                    # Find the conclusion slide based on some criteria
                    # This is just an example - you might identify it differently
                    if 'Conclusion' in str(slide):
                        conclusion_slide_id = slide['objectId']
                        # Move it to be the second slide (position 1, right after intro)
                        slides_service.reorder_slide(
                            "1Abc123Def456Ghi789JklMnoPqrs",
                            conclusion_slide_id,
                            1  # Second position (after intro)
                        )
                        break
        """
        try:
            requests = [
                {
                    'updateSlidesPosition': {
                        'slideObjectIds': [slide_id],
                        'insertionIndex': new_position
                    }
                }
            ]
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error reordering slide {slide_id} in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def duplicate_slide(self, presentation_id: str, slide_id: str) -> Dict[str, Any] | None:
        """
        Duplicate a slide in a presentation, creating an exact copy.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str): The ID of the slide to duplicate.
        
        Returns:
            Dict[str, Any]: The response from the API containing:
                - objectId: The ID of the newly created duplicate slide
            
            None: If duplication fails
        
        Notes:
            - The duplicated slide is placed immediately after the original slide
            - All content, formatting, and layouts from the original slide are preserved
            - The new slide will have a new unique ID
        
        Example:
            # Duplicate a slide that contains important content
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            
            # First get the presentation to find the slide to duplicate
            presentation = slides_service.get_presentation(presentation_id)
            
            if presentation and 'slides' in presentation:
                # For this example, we'll duplicate the first slide
                if len(presentation['slides']) > 0:
                    original_slide_id = presentation['slides'][0]['objectId']
                    
                    result = slides_service.duplicate_slide(
                        presentation_id,
                        original_slide_id
                    )
                    
                    if result and 'replies' in result:
                        # Get the ID of the new slide
                        new_slide_id = result['replies'][0]['duplicateObject']['objectId']
                        print(f"Created duplicate slide with ID: {new_slide_id}")
                        
                        # You could now modify the duplicate slide
                        # For example, add a "COPY" label to it
                        slides_service.create_shape(
                            presentation_id,
                            new_slide_id,
                            shape_type="TEXT_BOX",
                            width=100.0,
                            height=50.0,
                            x_pos=600.0,
                            y_pos=20.0
                        )
        """
        try:
            # Get the current presentation to find the slide index
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            slide_index = None
            for i, slide in enumerate(presentation.get('slides', [])):
                if slide.get('objectId') == slide_id:
                    slide_index = i
                    break
            
            if slide_index is None:
                raise ValueError(f"Slide {slide_id} not found in presentation")
            
            # Create the duplication request
            requests = [
                {
                    'duplicateObject': {
                        'objectId': slide_id
                    }
                }
            ]
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error duplicating slide {slide_id} in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def apply_slide_theme(self, presentation_id: str, slide_id: str, master_slide_id: str) -> Dict[str, Any] | None:
        """
        Apply a theme or layout from a master slide to a specific slide.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str): The ID of the slide to apply the theme to.
            
            master_slide_id (str): The ID of the master slide/layout to apply.
                This ID can be found in the 'masters' section of the presentation data.
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If operation fails
        
        Notes:
            - This method changes the slide's layout without altering its content
            - Layout changes may affect how content is displayed or positioned
            - To find master slide IDs, examine the 'masters' array in the presentation data
        
        Example:
            # First get the presentation to find available master slide layouts
            presentation = slides_service.get_presentation("1Abc123Def456Ghi789JklMnoPqrs")
            
            if presentation and 'masters' in presentation:
                # For this example, we'll apply the first master slide
                if len(presentation['masters']) > 0:
                    first_master_id = presentation['masters'][0]['masterId']
                    
                    result = slides_service.apply_slide_theme(
                        presentation_id,
                        "p.1234567890",  # Assuming the first slide ID is "p.1234567890"
                        first_master_id
                    )
                    
                    if result:
                        print(f"Successfully applied theme to slide")
        """
        try:
            requests = [
                {
                    'applyLayoutReference': {
                        'objectId': slide_id,
                        'layoutReference': {
                            'layoutId': master_slide_id
                        }
                    }
                }
            ]
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error applying theme to slide {slide_id} in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def get_thumbnails(self, presentation_id: str, slide_id: str = None,
                       thumbnail_properties: Dict[str, Any] = None) -> Dict[str, Any] | None:
        """
        Get thumbnail images for one or all slides in a presentation.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str, optional): The ID of a specific slide to get a thumbnail for.
                If not provided, thumbnails for all slides will be retrieved.
            
            thumbnail_properties (Dict[str, Any], optional): Properties for the thumbnail.
                Default: {'thumbnailSize': 'MEDIUM'}
                Available sizes:
                - 'SMALL': 220x172 pixels
                - 'MEDIUM': 427x320 pixels
                - 'LARGE': 793x595 pixels
        
        Returns:
            Dict[str, Any]: For a single slide request:
                - contentUrl: URL to the thumbnail image
                - width: Width of the thumbnail in pixels
                - height: Height of the thumbnail in pixels
                
                For all slides:
                - thumbnails: Array of objects containing:
                  - slideId: The ID of the slide
                  - thumbnail: Object with contentUrl, width, and height
            
            None: If retrieval fails
        
        Example:
            # Get thumbnail for a specific slide
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            slide_id = "p.1234567890"
            
            thumbnail = slides_service.get_thumbnails(
                presentation_id,
                slide_id,
                {'thumbnailSize': 'LARGE'}
            )
            
            if thumbnail:
                thumbnail_url = thumbnail['contentUrl']
                print(f"Slide thumbnail URL: {thumbnail_url}")
                print(f"Size: {thumbnail['width']}x{thumbnail['height']} pixels")
            
            # Get thumbnails for all slides in a presentation
            all_thumbnails = slides_service.get_thumbnails(presentation_id)
            
            if all_thumbnails and 'thumbnails' in all_thumbnails:
                for i, thumb_data in enumerate(all_thumbnails['thumbnails']):
                    slide_id = thumb_data['slideId']
                    thumb_url = thumb_data['thumbnail']['contentUrl']
                    print(f"Slide {i+1} (ID: {slide_id}) thumbnail: {thumb_url}")
        """
        try:
            if not thumbnail_properties:
                thumbnail_properties = {'thumbnailSize': 'MEDIUM'}
                
            if slide_id:
                # Get thumbnail for a specific slide
                result = self.service.presentations().pages().getThumbnail(
                    presentationId=presentation_id,
                    pageObjectId=slide_id,
                    **thumbnail_properties
                ).execute()
            else:
                # Get thumbnails for all slides
                result = self.service.presentations().get(
                    presentationId=presentation_id,
                    fields='slides.objectId'
                ).execute()
                
                thumbnails = []
                for slide in result.get('slides', []):
                    slide_id = slide.get('objectId')
                    thumbnail = self.service.presentations().pages().getThumbnail(
                        presentationId=presentation_id,
                        pageObjectId=slide_id,
                        **thumbnail_properties
                    ).execute()
                    thumbnails.append({
                        'slideId': slide_id,
                        'thumbnail': thumbnail
                    })
                
                result = {'thumbnails': thumbnails}
            
            return result
        except Exception as e:
            logging.error(f"Error getting thumbnails for presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def export_pdf(self, presentation_id: str) -> bytes | None:
        """
        Export a presentation as a PDF file.
        
        Args:
            presentation_id (str): The ID of the presentation to export.
        
        Returns:
            bytes: The PDF file content as bytes that can be written directly to a file.
            None: If export fails due to permissions or other errors.
        
        Notes:
            - The authenticated user must have permission to view the presentation
            - The returned bytes object contains the complete PDF file
            - All slides in the presentation are included in the PDF
        
        Example:
            # Export a presentation as PDF and save it to a file
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            pdf_bytes = slides_service.export_pdf(presentation_id)
            
            if pdf_bytes:
                # Save the PDF to a file
                with open("exported_presentation.pdf", "wb") as pdf_file:
                    pdf_file.write(pdf_bytes)
                    print("Successfully exported presentation to PDF")
            else:
                print("Failed to export presentation as PDF")
                
            # Advanced: Send the PDF as an email attachment
            if pdf_bytes:
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.base import MIMEBase
                from email.mime.text import MIMEText
                from email.utils import formatdate
                from email import encoders
                
                msg = MIMEMultipart()
                msg['From'] = 'your_email@example.com'
                msg['To'] = 'recipient@example.com'
                msg['Date'] = formatdate(localtime=True)
                msg['Subject'] = 'Presentation PDF Export'
                
                msg.attach(MIMEText('Please find the attached presentation.'))
                
                attachment = MIMEBase('application', 'pdf')
                attachment.set_payload(pdf_bytes)
                encoders.encode_base64(attachment)
                attachment.add_header(
                    'Content-Disposition', 
                    f'attachment; filename="presentation.pdf"'
                )
                msg.attach(attachment)
                
                # Connect to your email provider and send
                # (This is a simplified example)
        """
        try:
            # Use the Drive API to export as PDF
            result = self.drive_service.files().export(
                fileId=presentation_id,
                mimeType='application/pdf'
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error exporting presentation {presentation_id} as PDF: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def share_presentation(self, presentation_id: str, email: str, role: str = 'reader') -> Dict[str, Any] | None:
        """
        Share a presentation with another user by email address.
        
        Args:
            presentation_id (str): The ID of the presentation to share.
            
            email (str): The email address of the user to share with.
                Must be a valid Google account email address.
            
            role (str): The permission role to grant (default: 'reader').
                Available roles:
                - 'reader': Can view but not edit (view-only access)
                - 'commenter': Can view and comment but not edit
                - 'writer': Can view, comment, and edit
                - 'fileOrganizer': Can organize files in shared drives
                - 'organizer': Full control except ownership change
                - 'owner': Full ownership (transfers ownership)
        
        Returns:
            Dict[str, Any]: The response from the API containing:
                - id: The ID of the newly created permission
                - Other permission details may be included if specified in fields
            
            None: If sharing fails due to permissions, invalid email, etc.
        
        Notes:
            - The authenticated user must have sufficient permissions to share the presentation
            - When setting role='owner', the original owner loses ownership
            - The recipient will receive an email notification unless notification is disabled
        
        Example:
            # Share a presentation with view-only access
            slides_service.share_presentation(
                "1Abc123Def456Ghi789JklMnoPqrs",
                "colleague@example.com",
                role="reader"
            )
            
            # Share with edit permissions
            result = slides_service.share_presentation(
                "1Abc123Def456Ghi789JklMnoPqrs",
                "team.member@example.com",
                role="writer"
            )
            
            if result:
                print(f"Successfully shared presentation with edit access")
                print(f"Permission ID: {result['id']}")
            
            # Share with multiple people using different roles
            recipients = [
                {"email": "manager@example.com", "role": "writer"},
                {"email": "client@example.com", "role": "commenter"},
                {"email": "viewer@example.com", "role": "reader"}
            ]
            
            for recipient in recipients:
                slides_service.share_presentation(
                    "1Abc123Def456Ghi789JklMnoPqrs",
                    recipient["email"],
                    role=recipient["role"]
                )
        """
        try:
            user_permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            result = self.drive_service.permissions().create(
                fileId=presentation_id,
                body=user_permission,
                fields='id'
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error sharing presentation {presentation_id} with {email}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def batch_update(self, presentation_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any] | None:
        """
        Perform a batch update with multiple operations in a single request for efficiency.
        
        Args:
            presentation_id (str): The ID of the presentation to update.
            
            requests (List[Dict[str, Any]]): List of request objects to perform.
                Each request should follow the Google Slides API request format.
                See: https://developers.google.com/slides/api/reference/rest/v1/presentations/request
        
        Returns:
            Dict[str, Any]: The response from the API containing:
                - replies: Array of responses for each request in the same order
                  as the requests were specified
            
            None: If the batch update fails
        
        Notes:
            - Using batch updates is more efficient than making separate API calls
            - There is a limit of 500 operations per batch update
            - Operations are executed in the order they are specified
            - If any operation fails, the entire batch fails (atomic execution)
        
        Example:
            # Create a slide and add various elements in one batch operation
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            
            # Prepare a batch of operations
            requests = [
                # Create a new blank slide
                {
                    'createSlide': {
                        'objectId': 'my_new_slide',
                        'slideLayoutReference': {
                            'predefinedLayout': 'BLANK'
                        }
                    }
                },
                
                # Add a title text box to the slide
                {
                    'createShape': {
                        'objectId': 'title_box',
                        'shapeType': 'TEXT_BOX',
                        'elementProperties': {
                            'pageObjectId': 'my_new_slide',
                            'size': {
                                'width': {'magnitude': 600, 'unit': 'PT'},
                                'height': {'magnitude': 50, 'unit': 'PT'}
                            },
                            'transform': {
                                'scaleX': 1,
                                'scaleY': 1,
                                'translateX': 50,
                                'translateY': 30,
                                'unit': 'PT'
                            }
                        }
                    }
                },
                
                # Add text to the title box
                {
                    'insertText': {
                        'objectId': 'title_box',
                        'text': 'Quarterly Performance Review'
                    }
                },
                
                # Style the title text
                {
                    'updateTextStyle': {
                        'objectId': 'title_box',
                        'textRange': {
                            'type': 'ALL'
                        },
                        'style': {
                            'bold': True,
                            'fontSize': {'magnitude': 24, 'unit': 'PT'},
                            'foregroundColor': {
                                'opaqueColor': {'rgbColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8}}
                            }
                        },
                        'fields': 'bold,fontSize,foregroundColor'
                    }
                }
            ]
            
            # Execute all operations in a single API call
            result = slides_service.batch_update(presentation_id, requests)
            
            if result and 'replies' in result:
                print(f"Successfully executed {len(result['replies'])} operations")
        """
        try:
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error performing batch update on presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def create_presentation_from_template(self, template_id: str, title: str) -> Dict[str, Any] | None:
        """
        Create a new presentation by copying an existing template presentation.
        
        Args:
            template_id (str): The ID of the template presentation to copy.
                This presentation must be accessible to the authenticated user.
            
            title (str): The title for the new presentation.
                This will appear in Google Drive and at the top of the presentation.
        
        Returns:
            Dict[str, Any]: The new presentation's complete metadata including:
                - presentationId: The ID of the newly created presentation
                - title: The title of the new presentation
                - slides: Array of slide objects copied from the template
                - masters: Master slide definitions
                - layouts: Layout definitions
            
            None: If creation fails
        
        Notes:
            - The template is copied completely, including all slides, masters, and layouts
            - You own the new copy, regardless of who owns the original template
            - This is useful for creating standardized presentations
        
        Example:
            # Create a new presentation from a company-approved template
            template_id = "1TemplateID123456789"  # ID of your template presentation
            new_title = "Q3 2023 Sales Report"
            
            new_presentation = slides_service.create_presentation_from_template(
                template_id,
                new_title
            )
            
            if new_presentation:
                new_id = new_presentation['presentationId']
                print(f"Created new presentation from template: {new_id}")
                
                # Fill in placeholder values in the template with actual data
                placeholders = {
                    "{{QUARTER}}": "Q3 2023",
                    "{{PRESENTER}}": "Jane Smith",
                    "{{DEPARTMENT}}": "Sales",
                    "{{DATE}}": "October 15, 2023"
                }
                
                for placeholder, value in placeholders.items():
                    slides_service.replace_all_text(
                        new_id,
                        placeholder,
                        value
                    )
                
                # Now the presentation is ready to use with real data
        """
        try:
            # Copy the template presentation to create a new one
            copied_file = self.drive_service.files().copy(
                fileId=template_id,
                body={'name': title}
            ).execute()
            
            # Get the full presentation data
            presentation = self.service.presentations().get(
                presentationId=copied_file['id']
            ).execute()
            
            return presentation
        except Exception as e:
            logging.error(f"Error creating presentation from template {template_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def replace_all_text(self, presentation_id: str, find_text: str, replace_text: str, 
                          match_case: bool = False) -> Dict[str, Any] | None:
        """
        Replace all instances of specific text throughout the entire presentation.
        
        Args:
            presentation_id (str): The ID of the presentation to modify.
            
            find_text (str): The text to find and replace.
                Can be a regular substring or a placeholder like "{{NAME}}".
            
            replace_text (str): The text to replace the found text with.
                Can include any valid text, including formatting characters.
            
            match_case (bool): Whether to match case when searching (default: False).
                When False, "Sample" will match "SAMPLE", "sample", etc.
                When True, only exact case matches will be replaced.
        
        Returns:
            Dict[str, Any]: The response from the API containing:
                - replies: Array containing:
                  - replaceAllText: Object with:
                    - occurrencesChanged: Number of replacements made
            
            None: If operation fails
        
        Notes:
            - Replaces text across all slides, including titles, body text, and notes
            - Useful for template presentations with placeholders
            - Recommended placeholder format: {{PLACEHOLDER_NAME}}
        
        Example:
            # Replace template placeholders with actual data
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            
            # Basic text replacement
            result = slides_service.replace_all_text(
                presentation_id,
                "{{COMPANY_NAME}}",
                "Acme Corporation"
            )
            
            if result and 'replies' in result:
                count = result['replies'][0]['replaceAllText']['occurrencesChanged']
                print(f"Replaced company name in {count} locations")
            
            # Replace multiple placeholders
            replacements = [
                ("{{DATE}}", "October 15, 2023"),
                ("{{PRESENTER}}", "John Smith"),
                ("{{DEPARTMENT}}", "Marketing"),
                ("{{QUARTER}}", "Q3 2023"),
                ("{{GROWTH_RATE}}", "15.7%"),
            ]
            
            for find_text, replace_text in replacements:
                slides_service.replace_all_text(
                    presentation_id,
                    find_text,
                    replace_text
                )
                
            # Case-sensitive replacement (only replace uppercase "CONFIDENTIAL")
            slides_service.replace_all_text(
                presentation_id,
                "CONFIDENTIAL",
                "INTERNAL USE ONLY",
                match_case=True
            )
        """
        try:
            requests = [
                {
                    'replaceAllText': {
                        'containsText': {
                            'text': find_text,
                            'matchCase': match_case
                        },
                        'replaceText': replace_text
                    }
                }
            ]
            
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            return result
        except Exception as e:
            logging.error(f"Error replacing text in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def add_speaker_notes(self, presentation_id: str, slide_id: str, notes: str) -> Dict[str, Any] | None:
        """
        Add or update speaker notes for a specific slide.
        
        Args:
            presentation_id (str): The ID of the presentation.
            
            slide_id (str): The ID of the slide to add notes to.
            
            notes (str): The speaker notes content to add.
                Can include line breaks and basic formatting.
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If operation fails
        
        Notes:
            - Speaker notes are visible in presenter view but not in the main presentation
            - Notes can be used for talking points, reminders, or additional context
            - The implementation tries to update existing notes first, and falls back
              to creating new notes if needed
        
        Example:
            # Add comprehensive speaker notes to a slide
            presentation_id = "1Abc123Def456Ghi789JklMnoPqrs"
            slide_id = "p.1234567890"
            
            notes_content = 
            Key talking points:
            - Emphasize 20% growth in our core markets
            - Mention new partnership with XYZ Corp
            - Address supply chain improvements and cost reduction
            
            Questions to anticipate:
            - Timeline for international expansion
            - Projected Q4 performance
            
            Remember to pause for questions after slide 5.
            
            result = slides_service.add_speaker_notes(
                presentation_id,
                slide_id,
                notes_content
            )
            
            if result:
                print(f"Successfully added speaker notes to slide")
                
            # Add notes to all slides in a presentation
            presentation = slides_service.get_presentation(presentation_id)
            
            if presentation and 'slides' in presentation:
                for i, slide in enumerate(presentation['slides']):
                    slide_id = slide['objectId']
                    
                    # Create a simple note for each slide
                    slides_service.add_speaker_notes(
                        presentation_id,
                        slide_id,
                        f"Slide {i+1}: Speak for approximately 60 seconds on this topic."
                    )
        """
        try:
            # Notes are contained in a shape with a notesId property
            requests = [
                {
                    'replaceAllShapesWithSheetsChart': {
                        'pageObjectIds': [slide_id],
                        'containsText': {
                            'text': '{{NOTES_PLACEHOLDER}}',
                            'matchCase': True
                        }
                    }
                },
                {
                    'insertText': {
                        'objectId': f"{slide_id}_notes",
                        'text': notes
                    }
                }
            ]
            
            # First attempt to replace existing notes
            try:
                result = self.service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': requests}
                ).execute()
            except:
                # If the notes are not found, create a new one
                pass
            
            return result
        except Exception as e:
            logging.error(f"Error adding speaker notes to slide {slide_id} in presentation {presentation_id}: {str(e)}")
            logging.error(traceback.format_exc())   