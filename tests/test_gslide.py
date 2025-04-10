import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import os
from mcp_gsuite.gslide import GoogleSlidesService
import time

class TestServiceAccountGoogleSlides(unittest.TestCase):
    def setUp(self):
        # Path to your service account key file
        # /Users/binyamsisay/Desktop/rizzbuzz/MCP/mcp-gsuite/mcp-admin-455612-3259f209b7a6.json
        # Go to console.cloud.google.com and create a new project
        # Go to credentials and create new credentials
        # Select service account and create
        # Download the credentials and save as mcp-admin-455612-3259f209b7a6.json
        # Put the json file in the root directory
        self.service_account_file = "path/to/your/service-account-key.json"
        
        # Make sure the service account key file exists
        if not os.path.exists(self.service_account_file):
            self.fail(f"Service account key file not found at {self.service_account_file}")
    
    def test_service_account_create_presentation(self):
        # Create an instance of GoogleSlidesService using service account
        service = GoogleSlidesService(service_account_file=self.service_account_file)
        
        # 1. Create a presentation
        title = "Test Presentation 102"
        presentation = service.create_presentation(title)
        self.assertIsNotNone(presentation)
        presentation_id = presentation['presentationId']
        print(f"Created presentation with ID: {presentation_id}")
        
        # 2. Create a slide
        slide = service.create_slide(presentation_id, layout='TITLE_AND_BODY')
        self.assertIsNotNone(slide)
        slide_id = slide['replies'][0]['createSlide']['objectId']
        print(f"Created slide with ID: {slide_id}")
        
        # 3. Create a shape
        shape = service.create_shape(
            presentation_id, 
            slide_id,
            shape_type='RECTANGLE',
            width=300.0,
            height=150.0,
            x_pos=200.0,
            y_pos=200.0
        )
        self.assertIsNotNone(shape)
        shape_id = shape.get('createdObjectId')
        print(f"Created shape with ID: {shape_id}")
        
        # 4. Add text to shape
        shape_text = "Created with Service Account Authentication!"
        text_result = service.add_text_to_slide(
            presentation_id, 
            slide_id, 
            shape_id, 
            shape_text,
            {'bold': True, 'foregroundColor': {'opaqueColor': {'rgbColor': {'red': 0.1, 'green': 0.5, 'blue': 0.8}}}}
        )
        self.assertIsNotNone(text_result)
        print(f"Added text to shape")
        
        # 5. Get the presentation details to confirm changes
        presentation_details = service.get_presentation(presentation_id)
        self.assertIsNotNone(presentation_details)
        print(f"Retrieved presentation details")
        
        # Print the link to the presentation
        print(f"\nView the presentation at: https://docs.google.com/presentation/d/{presentation_id}/edit")
        
        # Sleep briefly to ensure all API calls complete
        time.sleep(2)

if __name__ == "__main__":
    unittest.main()