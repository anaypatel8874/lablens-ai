"""LabLens AI - Document Processing Service"""
import os
import io
import tempfile
import magic
from typing import List, Tuple, Optional
from PIL import Image
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import generate_secure_filename

logger = get_logger(__name__)
settings = get_settings()


class DocumentProcessor:
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/jpg",
        "image/png",
    }

    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

    @classmethod
    def validate_file(cls, file_bytes: bytes, filename: str) -> Tuple[bool, List[str]]:
        errors = []

        # Size check
        if len(file_bytes) > cls.MAX_UPLOAD_SIZE:
            errors.append(f"File size exceeds {cls.MAX_UPLOAD_SIZE // (1024*1024)}MB limit")

        # Extension check
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in settings.allowed_extensions:
            errors.append(f"File extension '.{ext}' not allowed")

        # MIME type check
        mime = magic.from_buffer(file_bytes, mime=True)
        if mime not in cls.ALLOWED_MIME_TYPES:
            errors.append(f"File type '{mime}' not supported")

        # Content validation
        if mime == "application/pdf":
            if not cls._is_valid_pdf(file_bytes):
                errors.append("Invalid or corrupted PDF file")
        elif mime.startswith("image/"):
            if not cls._is_valid_image(file_bytes):
                errors.append("Invalid or corrupted image file")

        return len(errors) == 0, errors

    @staticmethod
    def _is_valid_pdf(data: bytes) -> bool:
        return data.startswith(b"%PDF")

    @staticmethod
    def _is_valid_image(data: bytes) -> bool:
        try:
            Image.open(io.BytesIO(data)).verify()
            return True
        except Exception:
            return False

    @classmethod
    def get_page_count(cls, file_bytes: bytes, mime_type: str) -> int:
        if mime_type == "application/pdf":
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                count = len(doc)
                doc.close()
                return count
            except Exception as e:
                logger.error("Failed to get PDF page count", error=str(e))
                return 1
        return 1

    @classmethod
    def extract_pdf_text(cls, file_bytes: bytes) -> List[Tuple[int, str]]:
        """Extract text from PDF. Returns list of (page_num, text)."""
        results = []
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                results.append((page_num, text))
            doc.close()
        except Exception as e:
            logger.error("PDF text extraction failed", error=str(e))
        return results

    @classmethod
    def convert_pdf_to_images(
        cls, file_bytes: bytes, dpi: int = 300
    ) -> List[Tuple[int, bytes]]:
        """Convert PDF pages to images. Returns list of (page_num, image_bytes)."""
        results = []
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            images = convert_from_path(tmp_path, dpi=dpi, fmt="png")
            for page_num, image in enumerate(images, 1):
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                results.append((page_num, img_buffer.getvalue()))

            os.unlink(tmp_path)
        except Exception as e:
            logger.error("PDF to image conversion failed", error=str(e))
        return results

    @classmethod
    def preprocess_image(cls, image_bytes: bytes) -> bytes:
        """Preprocess image for better OCR: deskew, contrast, denoise."""
        try:
            img = Image.open(io.BytesIO(image_bytes))

            # Convert to grayscale if needed
            if img.mode != "L":
                img = img.convert("L")

            # Auto-rotate based on EXIF
            img = cls._auto_rotate(img)

            # Enhance contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5)

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
        except Exception as e:
            logger.error("Image preprocessing failed", error=str(e))
            return image_bytes

    @staticmethod
    def _auto_rotate(img: Image.Image) -> Image.Image:
        try:
            exif = img._getexif()
            if exif:
                orientation = exif.get(274)
                rotations = {3: 180, 6: 270, 8: 90}
                if orientation in rotations:
                    img = img.rotate(rotations[orientation], expand=True)
        except Exception:
            pass
        return img

    @classmethod
    def detect_blur(cls, image_bytes: bytes, threshold: float = 100.0) -> Tuple[bool, float]:
        """Detect if image is blurry using Laplacian variance."""
        try:
            import cv2
            import numpy as np

            img = Image.open(io.BytesIO(image_bytes))
            if img.mode != "L":
                img = img.convert("L")

            arr = np.array(img)
            laplacian_var = cv2.Laplacian(arr, cv2.CV_64F).var()
            is_blurry = laplacian_var < threshold
            return is_blurry, float(laplacian_var)
        except ImportError:
            return False, 0.0
        except Exception as e:
            logger.error("Blur detection failed", error=str(e))
            return False, 0.0

    @classmethod
    def detect_cropped_report(cls, image_bytes: bytes) -> Tuple[bool, str]:
        """Detect if report appears cropped or incomplete."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size

            # Check if aspect ratio is unusual (very wide or very tall)
            ratio = w / h
            if ratio > 3 or ratio < 0.3:
                return True, "Unusual aspect ratio - report may be cropped"

            # Check if image is too small
            if w < 400 or h < 400:
                return True, "Image resolution too low - may be missing content"

            return False, ""
        except Exception:
            return False, ""
