import numpy as np
from PIL import Image
import io
from skimage.metrics import structural_similarity as ssim
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

class VisualPerception:
    @staticmethod
    def calculate_ssim(img1_bytes: bytes, img2_bytes: bytes) -> float:
        """
        Calculates the Structural Similarity Index Measure (SSIM) between two screenshots.
        Uses uint8 conversion to ensure consistent data range.
        """
        img1 = Image.open(io.BytesIO(img1_bytes)).convert('L')
        img2 = Image.open(io.BytesIO(img2_bytes)).convert('L')
        
        # Ensure identical size
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
            
        img1_array = np.array(img1, dtype=np.uint8)
        img2_array = np.array(img2, dtype=np.uint8)
        
        # Use data_range=255 for uint8 images
        score, _ = ssim(img1_array, img2_array, full=True, data_range=255)
        return float(score)

    @staticmethod
    def get_element_coordinates(screenshot_bytes: bytes, element_description: str):
        """
        Placeholder for visual element detection.
        In a production environment, this would use a vision-fine-tuned model or OCR.
        """
        # This would return normalized coordinates (0-1000)
        return {"x": 500, "y": 500}

    @staticmethod
    def preprocess_image(image_bytes: bytes):
        """
        Prepares image for AI consumption (resizing, grayscale, etc. if needed).
        """
        if not HAS_CV2:
            print("Warning: opencv-python not installed. Skipping image preprocessing.")
            return image_bytes

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Apply filters if needed
        return img
