"""
File validation utilities for secure file uploads.
Validates file content using magic numbers and actual file inspection.
"""
import logging
from typing import Optional
from fastapi import UploadFile
from app.config import settings

logger = logging.getLogger(__name__)


def validate_image_file(file: UploadFile) -> bool:
    """
    Validates an image file by checking:
    1. Real MIME type using magic numbers
    2. Actual image validity using PIL
    
    Args:
        file: UploadFile object to validate
        
    Returns:
        True if file is a valid image, False otherwise
    """
    try:
        # Try to use python-magic if available
        try:
            import magic
            file_content = file.file.read(1024)
            file.file.seek(0)
            
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type not in ["image/jpeg", "image/png"]:
                logger.warning(f"Invalid MIME type detected: {mime_type} (expected image/jpeg or image/png)")
                return False
        except ImportError:
            # python-magic not available, skip magic number check
            logger.warning("python-magic not available, skipping magic number validation")
        except Exception as e:
            logger.warning(f"Error checking magic number: {e}, falling back to PIL validation")
        
        # Verify that it's actually a valid image using PIL
        try:
            from PIL import Image
            file.file.seek(0)
            img = Image.open(file.file)
            img.verify()
            file.file.seek(0)
            return True
        except ImportError:
            logger.warning("PIL/Pillow not available, cannot verify image validity")
            return False
        except Exception as e:
            logger.warning(f"Image validation failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error validating image file: {e}")
        return False


def validate_file_size(file: UploadFile) -> bool:
    """
    Validates file size before processing.
    For streamed files, checks size during upload.
    
    Args:
        file: UploadFile object to validate
        
    Returns:
        True if file size is within limits, False otherwise
    """
    try:
        # If file has size attribute, check it directly
        if hasattr(file, 'size') and file.size:
            if file.size > settings.MAX_FILE_SIZE:
                logger.warning(f"File size {file.size} exceeds maximum {settings.MAX_FILE_SIZE}")
                return False
            return True
        
        # For streamed files, check size during read
        total_size = 0
        chunk_size = 8192
        file.file.seek(0)
        
        while True:
            chunk = file.file.read(chunk_size)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > settings.MAX_FILE_SIZE:
                logger.warning(f"File size {total_size} exceeds maximum {settings.MAX_FILE_SIZE}")
                file.file.seek(0)
                return False
        
        file.file.seek(0)
        return True
    except Exception as e:
        logger.error(f"Error validating file size: {e}")
        return False


def validate_document_file(file: UploadFile) -> bool:
    """
    Validates a document file by checking the real MIME type using magic numbers.
    
    Args:
        file: UploadFile object to validate
        
    Returns:
        True if file is a valid document type, False otherwise
    """
    allowed_mime_types = [
        "application/pdf",
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "text/plain",  # .txt
        "text/csv",  # .csv
        "application/vnd.ms-excel",  # .xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    ]
    
    try:
        # Try to use python-magic if available
        try:
            import magic
            file_content = file.file.read(1024)
            file.file.seek(0)
            
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type not in allowed_mime_types:
                logger.warning(f"Invalid MIME type detected: {mime_type} (not in allowed list)")
                return False
            return True
        except ImportError:
            # python-magic not available, fall back to content_type check
            logger.warning("python-magic not available, using content_type validation (less secure)")
            return file.content_type in allowed_mime_types
        except Exception as e:
            logger.warning(f"Error checking magic number: {e}, falling back to content_type")
            return file.content_type in allowed_mime_types
            
    except Exception as e:
        logger.error(f"Error validating document file: {e}")
        return False
