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
    def __init__(self, service_account_file=None, user_id=None):
        """
        Initialize the Google Slides service with either service account or user credentials.
        
        Args:
            service_account_file (str, optional): Path to service account key file
            user_id (str, optional): The ID of the user whose credentials to use
        
        Raises:
            RuntimeError: If neither valid credentials option is provided
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
            title (str): The title of the new presentation
        
        Returns:
            Dict[str, Any]: The created presentation's metadata
            None: If creation fails
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
        Retrieve a presentation by its ID.
        
        Args:
            presentation_id (str): The ID of the presentation to retrieve
        
        Returns:
            Dict[str, Any]: The presentation's metadata and content
            None: If retrieval fails
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
        List presentations owned by the user.
        
        Args:
            max_results (int): Maximum number of presentations to retrieve (default: 50)
        
        Returns:
            List[Dict[str, Any]]: List of presentation metadata
            None: If retrieval fails
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
        Create a new slide in the specified presentation.
        
        Args:
            presentation_id (str): The ID of the presentation to add the slide to
            layout (str): The predefined layout type (default: 'TITLE_AND_BODY')
                        Options include: 'TITLE_ONLY', 'TITLE_AND_BODY', 'BLANK', etc.
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If creation fails
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
        Add text to a specified shape in a slide.
        
        Args:
            presentation_id (str): The ID of the presentation
            slide_id (str): The ID of the slide
            shape_id (str): The ID of the shape to add text to
            text (str): The text content to add
            text_style (Dict[str, Any], optional): Style parameters for the text
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If operation fails
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
        Create a shape on a specific slide.
        
        Args:
            presentation_id (str): The ID of the presentation
            slide_id (str): The ID of the slide
            shape_type (str): The type of shape to create (default: 'RECTANGLE')
                            Options include: 'RECTANGLE', 'ELLIPSE', 'TEXT_BOX', etc.
            width (float): The width of the shape in points (default: 350.0)
            height (float): The height of the shape in points (default: 100.0)
            x_pos (float): The x-coordinate position in points (default: 100.0)
            y_pos (float): The y-coordinate position in points (default: 100.0)
        
        Returns:
            Dict[str, Any]: The response from the API including the ID of the created shape
            None: If creation fails
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
        Insert an image into a slide from URL or binary data.
        
        Args:
            presentation_id (str): The ID of the presentation
            slide_id (str): The ID of the slide
            image_url (str, optional): The URL of the image to insert
            image_data (bytes, optional): The binary data of the image to insert
            width (float): The width of the image in points (default: 400.0)
            height (float): The height of the image in points (default: 300.0)
            x_pos (float): The x-coordinate position in points (default: 100.0)
            y_pos (float): The y-coordinate position in points (default: 100.0)
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If operation fails
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
        Delete a temporary file from Google Drive.
        
        Args:
            file_id (str): The ID of the file to delete
        
        Returns:
            bool: True if deletion was successful, False otherwise
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
        Create a table on a slide.
        
        Args:
            presentation_id (str): The ID of the presentation
            slide_id (str): The ID of the slide
            rows (int): Number of rows in the table
            cols (int): Number of columns in the table
            width (float): The width of the table in points (default: 400.0)
            height (float): The height of the table in points (default: 300.0)
            x_pos (float): The x-coordinate position in points (default: 100.0)
            y_pos (float): The y-coordinate position in points (default: 100.0)
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If operation fails
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
        Update the content of a table cell.
        
        Args:
            presentation_id (str): The ID of the presentation
            table_id (str): The ID of the table
            row_idx (int): The row index (0-based)
            col_idx (int): The column index (0-based)
            text (str): The text content to insert into the cell
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If operation fails
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
            presentation_id (str): The ID of the presentation
            slide_id (str): The ID of the slide to delete
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If deletion fails
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
            presentation_id (str): The ID of the presentation
            slide_id (str): The ID of the slide to reorder
            new_position (int): The new position for the slide (0-based)
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If reordering fails
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
        Duplicate a slide in a presentation.
        
        Args:
            presentation_id (str): The ID of the presentation
            slide_id (str): The ID of the slide to duplicate
        
        Returns:
            Dict[str, Any]: The response from the API including the ID of the new slide
            None: If duplication fails
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
        Apply a theme from a master slide to a specific slide.
        
        Args:
            presentation_id (str): The ID of the presentation
            slide_id (str): The ID of the slide to apply the theme to
            master_slide_id (str): The ID of the master slide/layout to apply
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If operation fails
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
        Get thumbnails for slides in a presentation.
        
        Args:
            presentation_id (str): The ID of the presentation
            slide_id (str, optional): The ID of a specific slide to get thumbnail for
            thumbnail_properties (Dict[str, Any], optional): Properties for the thumbnail
                                                           (e.g., {'thumbnailSize': 'MEDIUM'})
        
        Returns:
            Dict[str, Any]: The thumbnails response from the API
            None: If retrieval fails
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
            presentation_id (str): The ID of the presentation to export
        
        Returns:
            bytes: The PDF file content as bytes
            None: If export fails
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
        Share a presentation with another user.
        
        Args:
            presentation_id (str): The ID of the presentation to share
            email (str): The email address of the user to share with
            role (str): The role to grant (default: 'reader')
                      Options include: 'owner', 'organizer', 'fileOrganizer', 'writer', 'commenter', 'reader'
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If sharing fails
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
        Perform a batch update with multiple operations in a single request.
        
        Args:
            presentation_id (str): The ID of the presentation
            requests (List[Dict[str, Any]]): List of request objects to perform
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If the batch update fails
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
        Create a new presentation from an existing template.
        
        Args:
            template_id (str): The ID of the template presentation
            title (str): The title for the new presentation
        
        Returns:
            Dict[str, Any]: The new presentation's metadata
            None: If creation fails
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
        Replace all instances of text in a presentation.
        
        Args:
            presentation_id (str): The ID of the presentation
            find_text (str): The text to find
            replace_text (str): The text to replace it with
            match_case (bool): Whether to match case (default: False)
        
        Returns:
            Dict[str, Any]: The response from the API with replacement counts
            None: If operation fails
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
        Add or update speaker notes for a slide.
        
        Args:
            presentation_id (str): The ID of the presentation
            slide_id (str): The ID of the slide
            notes (str): The speaker notes content
        
        Returns:
            Dict[str, Any]: The response from the API
            None: If operation fails
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