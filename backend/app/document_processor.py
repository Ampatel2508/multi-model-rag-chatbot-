from typing import List
from langchain_core.documents import Document
import logging
import tempfile
import os
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Check if EasyOCR is available (primary OCR engine)
EASYOCR_AVAILABLE = False
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    logger.info("[OK] EasyOCR is available - will use for superior OCR")
except ImportError as e:
    logger.warning(f"EasyOCR not available: {e}")

# Check if Tesseract is available (fallback OCR engine)
TESSERACT_AVAILABLE = False
try:
    import pytesseract
    from pdf2image import convert_from_path
    # Try to access Tesseract to verify it's actually installed
    try:
        pytesseract.get_tesseract_version()
        TESSERACT_AVAILABLE = True
        logger.info("[OK] Tesseract OCR is available (fallback)")
    except Exception as e:
        logger.warning(f"Tesseract system software not found: {e}")
        TESSERACT_AVAILABLE = False
except ImportError as e:
    logger.warning(f"OCR dependencies not fully available: {e}")


class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize document processor with chunk parameters."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_document(self, file_path: str, filename: str, file_ext: str) -> List[Document]:
        """
        Process document and return list of Document chunks.
        Handles text files, PDFs, images, and other formats.
        Uses Tesseract OCR for scanned PDFs and image files.
        """
        try:
            logger.info(f"Processing document: {filename} ({file_ext})")
            
            # Check if this is an OCR-based format but Tesseract is not available
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'] and not TESSERACT_AVAILABLE:
                logger.error(f"Cannot process image {filename} - Tesseract OCR not installed")
                chunks = [Document(
                    page_content=f"[ERROR: Cannot extract text from image {filename}. Tesseract OCR is not installed. Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki]",
                    metadata={
                        "filename": filename,
                        "file_ext": file_ext,
                        "file_path": file_path,
                        "chunk_index": 0,
                        "error": True,
                        "reason": "tesseract_not_installed",
                    }
                )]
                return chunks
            
            content = self._extract_content(file_path, file_ext)
            
            if not content or not content.strip():
                logger.error(f"Failed to extract content from {filename}")
                error_msg = f"[ERROR: Could not extract text from {filename}."
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
                    error_msg += " The image may not contain readable text or may be too low quality."
                    if not TESSERACT_AVAILABLE:
                        error_msg += " Tesseract OCR is also not installed."
                elif file_ext == '.pdf':
                    error_msg += " The PDF may be scanned or corrupted."
                    if not TESSERACT_AVAILABLE:
                        error_msg += " Install Tesseract for better scanned PDF support."
                error_msg += "]"
                
                chunks = [Document(
                    page_content=error_msg,
                    metadata={
                        "filename": filename,
                        "file_ext": file_ext,
                        "file_path": file_path,
                        "chunk_index": 0,
                        "error": True,
                    }
                )]
                logger.warning(f"Document {filename} has no readable content, created error document")
                return chunks
            
            logger.info(f"Successfully extracted {len(content)} characters from {filename}")
            
            # Split into chunks
            chunks = self._chunk_text(content, filename, file_path, file_ext)
            
            if not chunks:
                # Fallback: return entire content as single chunk
                logger.warning(f"Chunking failed for {filename}, using entire content as single chunk")
                chunks = [Document(
                    page_content=content,
                    metadata={
                        "filename": filename,
                        "file_ext": file_ext,
                        "file_path": file_path,
                        "chunk_index": 0,
                    }
                )]
            
            logger.info(f"✓ Created {len(chunks)} chunks from {filename}")
            return chunks
            
        except Exception as e:
            logger.error(f"Exception processing document {filename}: {type(e).__name__}: {e}", exc_info=True)
            raise

    def _extract_content(self, file_path: str, file_ext: str) -> str:
        """Extract text content from various file formats."""
        
        # Text-based formats
        if file_ext in ['.txt', '.md', '.json', '.csv', '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.xml', '.log']:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if content.strip():
                        logger.info(f"Extracted {len(content)} characters from text file")
                        return content
                    else:
                        logger.warning("Text file is empty")
                        return ""
            except Exception as e:
                logger.error(f"Error reading text file: {e}")
                return ""
        
        # Image formats - use OCR
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
            logger.info(f"Processing image file: {file_path}")
            return self._extract_image_text(file_path)
        
        # PDF format - try multiple extraction methods
        elif file_ext == '.pdf':
            # Try primary method (which now includes OCR fallback)
            content = self._extract_pdf(file_path)
            if content and content.strip():
                return content
            
            logger.warning("Could not extract text from PDF using any method")
            return ""
        
        # Fallback for other formats
        else:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if content.strip():
                        return content
                    else:
                        logger.warning(f"File {file_path} appears to be empty")
                        return ""
            except Exception:
                logger.warning(f"Could not read file {file_path} as text")
                return ""

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file using best available OCR."""
        try:
            import PyPDF2
            text = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                logger.info(f"PDF has {len(reader.pages)} pages")
                
                if len(reader.pages) == 0:
                    logger.warning("PDF file has no pages")
                    return ""
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text.strip()
                        else:
                            logger.warning(f"Page {page_num + 1} has no extractable text")
                    except Exception as page_error:
                        logger.warning(f"Error extracting page {page_num + 1}: {page_error}")
                        continue
            
            if text.strip() and len(text.strip()) > 500:
                logger.info(f"Successfully extracted {len(text)} characters from PDF using text extraction")
                return text
            else:
                logger.info("PDF text extraction yielded minimal text. Using OCR for scanned document...")
                return self._extract_pdf_with_ocr(file_path)
                
        except ImportError:
            logger.warning("PyPDF2 not installed - using OCR directly")
            return self._extract_pdf_with_ocr(file_path)
        except Exception as e:
            logger.warning(f"Error with PDF text extraction: {e} - falling back to OCR")
            return self._extract_pdf_with_ocr(file_path)

    def _preprocess_image_aggressive(self, image_cv) -> np.ndarray:
        """Apply ultra-aggressive preprocessing for optimal OCR results."""
        try:
            # Convert to grayscale if needed
            if len(image_cv.shape) == 3:
                gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
            else:
                gray = image_cv
            
            # 1. Upscale image for better OCR (2x scaling)
            height, width = gray.shape
            gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
            
            # 2. Advanced noise reduction (2-pass)
            denoised = cv2.fastNlMeansDenoising(gray, None, h=12, templateWindowSize=7, searchWindowSize=25)
            denoised = cv2.fastNlMeansDenoising(denoised, None, h=10, templateWindowSize=7, searchWindowSize=25)
            
            # 3. Histogram equalization for better contrast
            equalized = cv2.equalizeHist(denoised)
            
            # 4. CLAHE (Contrast Limited Adaptive Histogram Equalization) - stronger
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(6, 6))
            contrast_enhanced = clahe.apply(equalized)
            
            # 5. Bilateral filter to preserve edges
            bilateral = cv2.bilateralFilter(contrast_enhanced, 11, 85, 85)
            
            # 6. Morphological operations (stronger kernel)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morph = cv2.morphologyEx(bilateral, cv2.MORPH_CLOSE, kernel)
            morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
            
            # 7. Adaptive thresholding (better for varying lighting)
            binary = cv2.adaptiveThreshold(morph, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # 8. Final binary refinement with OTSU
            _, binary = cv2.threshold(binary, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            logger.debug("Ultra-aggressive preprocessing applied: upscale, denoise, equalize, CLAHE, filter, morph, adaptive+OTSU threshold")
            return binary
            
        except Exception as e:
            logger.warning(f"Error in preprocessing: {e} - using original image")
            return image_cv

    def _extract_pdf_with_ocr(self, file_path: str) -> str:
        """Extract PDF using EasyOCR (superior) or Tesseract (fallback)."""
        try:
            from pdf2image import convert_from_path
            
            logger.info(f"Converting PDF to images for OCR processing...")
            
            # Convert PDF to images at high DPI
            try:
                images = convert_from_path(file_path, dpi=300, timeout=600)
                logger.info(f"Converted PDF to {len(images)} images at 300 DPI")
            except Exception as e:
                logger.error(f"Failed to convert PDF: {e}")
                return ""
            
            # Use EasyOCR if available (superior to Tesseract)
            if EASYOCR_AVAILABLE:
                logger.info("Using EasyOCR for text extraction (recommended)")
                return self._extract_with_easyocr(images)
            elif TESSERACT_AVAILABLE:
                logger.info("EasyOCR not available, using Tesseract")
                return self._extract_with_tesseract(images)
            else:
                logger.error("No OCR engine available")
                return ""
        
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            return ""

    def _clean_ocr_text(self, text: str) -> str:
        """Minimal post-processing to preserve all extracted content."""
        try:
            import re
            
            # Only remove the most egregious artifacts
            # Keep most content - RAG will filter relevant parts during query
            
            # Fix excessive blank lines (more than 2 consecutive)
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            # Fix excessive spacing within lines
            text = re.sub(r' {2,}', ' ', text)
            
            # Remove leading/trailing spaces from each line but keep line structure
            lines = text.split('\n')
            cleaned_lines = [line.strip() for line in lines]
            text = '\n'.join(cleaned_lines)
            
            text = text.strip()
            
            return text
        except Exception as e:
            logger.warning(f"Error in minimal text cleaning: {e}")
            return text

    def _extract_with_easyocr(self, images: List) -> str:
        """Extract text using EasyOCR - capture ALL content with minimal filtering."""
        try:
            import easyocr
            
            # Initialize EasyOCR reader (English only for speed, can add more languages)
            reader = easyocr.Reader(['en'], gpu=False)
            text = ""
            
            logger.info(f"Extracting text from {len(images)} pages using EasyOCR...")
            
            for page_num, pil_image in enumerate(images):
                try:
                    # Convert PIL image to OpenCV format
                    image_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    
                    # Apply ultra-aggressive preprocessing
                    processed_image = self._preprocess_image_aggressive(image_cv)
                    
                    # Extract text using EasyOCR - minimal filtering to capture all content
                    results = reader.readtext(processed_image, detail=1)  # detail=1 for confidence scores
                    
                    if results:
                        # Very permissive filtering - include almost everything
                        # Confidence > 0.1 means we keep even low-confidence text
                        filtered_text = []
                        for (bbox, text_result, confidence) in results:
                            if confidence > 0.1:  # Very permissive threshold
                                filtered_text.append(text_result)
                        
                        if filtered_text:
                            page_text = "\n".join(filtered_text)
                            # Minimal cleanup - preserve content
                            page_text = self._clean_ocr_text(page_text)
                            
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text
                            logger.info(f"Page {page_num + 1}: Extracted {len(page_text)} characters (all content captured)")
                        else:
                            logger.warning(f"Page {page_num + 1}: No text found")
                    else:
                        logger.warning(f"Page {page_num + 1}: No text found")
                        
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1}: {e}")
                    continue
            
            if text.strip():
                logger.info(f"[SUCCESS] EasyOCR extracted {len(text)} characters total (full content preserved)")
                return text
            else:
                logger.warning("EasyOCR returned no text")
                return ""
        
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return ""

    def _extract_with_tesseract(self, images: List) -> str:
        """Fallback: Extract text using Tesseract."""
        try:
            import pytesseract
            
            text = ""
            logger.info(f"Extracting text from {len(images)} pages using Tesseract...")
            
            for page_num, pil_image in enumerate(images):
                try:
                    # Convert PIL image to OpenCV format
                    image_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    
                    # Apply aggressive preprocessing
                    processed_image = self._preprocess_image_aggressive(image_cv)
                    
                    # Convert back to PIL for Tesseract
                    from PIL import Image
                    processed_pil = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
                    
                    # Extract text
                    page_text = pytesseract.image_to_string(processed_pil, lang='eng', config='--psm 3')
                    
                    if page_text.strip():
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text.strip()
                        logger.info(f"Page {page_num + 1}: Extracted {len(page_text)} characters")
                    else:
                        logger.warning(f"Page {page_num + 1}: No text found")
                        
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1}: {e}")
                    continue
            
            if text.strip():
                logger.info(f"[SUCCESS] Tesseract extracted {len(text)} characters total")
                return text
            else:
                logger.warning("Tesseract returned no text")
                return ""
        
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return ""

    def _extract_image_text(self, file_path: str) -> str:
        """Extract text from image files using EasyOCR or Tesseract with post-processing."""
        try:
            image_cv = cv2.imread(file_path)
            if image_cv is None:
                logger.error(f"Failed to load image: {file_path}")
                return ""
            
            logger.info(f"Extracting text from image: {file_path}")
            
            # Apply ultra-aggressive preprocessing
            processed_image = self._preprocess_image_aggressive(image_cv)
            
            # Use EasyOCR if available
            if EASYOCR_AVAILABLE:
                logger.info("Using EasyOCR for image text extraction")
                try:
                    import easyocr
                    reader = easyocr.Reader(['en'], gpu=False)
                    results = reader.readtext(processed_image, detail=1)  # detail=1 for confidence
                    
                    if results:
                        # Filter by confidence and join
                        filtered_text = []
                        for (bbox, text_result, confidence) in results:
                            if confidence > 0.3:
                                filtered_text.append(text_result)
                        
                        if filtered_text:
                            text = "\n".join(filtered_text)
                            text = self._clean_ocr_text(text)
                            logger.info(f"Successfully extracted {len(text)} characters from image with EasyOCR")
                            return text
                except Exception as e:
                    logger.warning(f"EasyOCR failed: {e} - trying Tesseract")
            
            # Fallback to Tesseract
            if TESSERACT_AVAILABLE:
                logger.info("Using Tesseract for image text extraction")
                try:
                    import pytesseract
                    from PIL import Image
                    processed_pil = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
                    text = pytesseract.image_to_string(processed_pil, lang='eng')
                    
                    if text and text.strip():
                        text = self._clean_ocr_text(text)
                        logger.info(f"Successfully extracted {len(text)} characters from image with Tesseract")
                        return text
                except Exception as e:
                    logger.warning(f"Tesseract also failed: {e}")
            
            logger.error("No OCR engine available for image extraction")
            return ""
        
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""

    def _chunk_text(self, text: str, filename: str, file_path: str, file_ext: str) -> List[Document]:
        """Split text into chunks with metadata."""
        if not text or not text.strip():
            return []
        
        chunks = []
        chunk_size = self.chunk_size
        chunk_overlap = self.chunk_overlap
        
        # Split by paragraphs first, then by size
        paragraphs = text.split('\n\n')
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            # If adding this paragraph exceeds chunk size, save current chunk
            if current_chunk and len(current_chunk) + len(para) > chunk_size:
                if current_chunk.strip():
                    chunks.append(Document(
                        page_content=current_chunk.strip(),
                        metadata={
                            "filename": filename,
                            "file_ext": file_ext,
                            "file_path": file_path,
                            "chunk_index": chunk_index,
                        }
                    ))
                    chunk_index += 1
                    # Keep overlap
                    current_chunk = current_chunk[-chunk_overlap:] + "\n" + para
                else:
                    current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(Document(
                page_content=current_chunk.strip(),
                metadata={
                    "filename": filename,
                    "file_ext": file_ext,
                    "file_path": file_path,
                    "chunk_index": chunk_index,
                }
            ))
        
        return chunks
