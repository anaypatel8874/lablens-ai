"""LabLens AI - OCR Service (Pluggable)"""
import io
from typing import List, Tuple, Optional
from PIL import Image
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class OCRResult:
    def __init__(self, text: str, confidence: float = 0.0, bbox: Optional[dict] = None):
        self.text = text
        self.confidence = confidence
        self.bbox = bbox


class BaseOCRProvider:
    def extract_text(self, image_bytes: bytes) -> List[OCRResult]:
        raise NotImplementedError


class TesseractOCRProvider(BaseOCRProvider):
    def __init__(self):
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract_text(self, image_bytes: bytes) -> List[OCRResult]:
        if not self.available:
            logger.error("Tesseract not available")
            return [OCRResult("", 0.0)]

        try:
            import pytesseract
            from pytesseract import Output
            import numpy as np

            img = Image.open(io.BytesIO(image_bytes))
            data = pytesseract.image_to_data(img, output_type=Output.DICT)

            results = []
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                conf = int(data["conf"][i])
                if text and conf > 0:
                    bbox = {
                        "x": data["left"][i],
                        "y": data["top"][i],
                        "w": data["width"][i],
                        "h": data["height"][i],
                    }
                    results.append(OCRResult(text, conf / 100.0, bbox))

            return results
        except Exception as e:
            logger.error("Tesseract OCR failed", error=str(e))
            return [OCRResult("", 0.0)]


class AWSTextractProvider(BaseOCRProvider):
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            import boto3
            self.client = boto3.client(
                "textract",
                region_name=settings.storage_region,
                aws_access_key_id=settings.storage_access_key,
                aws_secret_access_key=settings.storage_secret_key,
            )
        except Exception as e:
            logger.error("Failed to initialize Textract client", error=str(e))

    def extract_text(self, image_bytes: bytes) -> List[OCRResult]:
        if not self.client:
            return [OCRResult("", 0.0)]

        try:
            response = self.client.detect_document_text(Document={"Bytes": image_bytes})
            results = []
            for block in response.get("Blocks", []):
                if block["BlockType"] == "WORD":
                    conf = block.get("Confidence", 0) / 100.0
                    text = block.get("Text", "")
                    bbox = block.get("Geometry", {}).get("BoundingBox", {})
                    results.append(OCRResult(text, conf, bbox))
            return results
        except Exception as e:
            logger.error("Textract OCR failed", error=str(e))
            return [OCRResult("", 0.0)]


class OCRService:
    def __init__(self):
        self.provider = self._get_provider()

    def _get_provider(self) -> BaseOCRProvider:
        provider_name = settings.ocr_provider.lower()
        if provider_name == "textract":
            return AWSTextractProvider()
        return TesseractOCRProvider()

    def extract_text(self, image_bytes: bytes) -> Tuple[str, float]:
        """Extract text from image. Returns (full_text, avg_confidence)."""
        results = self.provider.extract_text(image_bytes)

        if not results:
            return "", 0.0

        texts = [r.text for r in results if r.text]
        full_text = " ".join(texts)

        confidences = [r.confidence for r in results if r.text]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return full_text, avg_confidence

    def extract_from_pdf_pages(
        self, page_images: List[Tuple[int, bytes]]
    ) -> List[Tuple[int, str, float]]:
        """Extract text from multiple PDF page images."""
        results = []
        for page_num, img_bytes in page_images:
            text, confidence = self.extract_text(img_bytes)
            results.append((page_num, text, confidence))
        return results
