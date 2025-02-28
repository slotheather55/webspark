import logging
import os
import io
from typing import Dict, Optional, BinaryIO, Tuple

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import StorageError

logger = logging.getLogger(__name__)


class CloudStorageService:
    """
    Service for interacting with cloud storage (AWS S3)
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.base_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com"
    
    async def upload_file(
        self, 
        file_data: bytes, 
        file_path: str, 
        content_type: Optional[str] = None,
        public: bool = True
    ) -> str:
        """
        Upload a file to cloud storage
        
        Args:
            file_data: File data as bytes
            file_path: Path where the file should be stored
            content_type: MIME type of the file
            public: Whether the file should be publicly accessible
            
        Returns:
            URL of the uploaded file
        """
        try:
            # Determine content type if not provided
            if not content_type:
                ext = os.path.splitext(file_path)[1].lower()
                content_type = self._get_content_type(ext)
            
            # Set up upload parameters
            extra_args = {
                'ContentType': content_type
            }
            
            # Set ACL if file should be public
            if public:
                extra_args['ACL'] = 'public-read'
            
            # Upload to S3
            logger.info(f"Uploading file to S3: {file_path}")
            self.s3_client.upload_fileobj(
                io.BytesIO(file_data),
                self.bucket_name,
                file_path,
                ExtraArgs=extra_args
            )
            
            # Return the URL
            return f"{self.base_url}/{file_path}"
        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise StorageError(
                detail=f"Error uploading to cloud storage: {str(e)}",
                error_code="upload_error"
            )
        except Exception as e:
            logger.error(f"Unexpected error in upload_file: {str(e)}")
            raise StorageError(
                detail="Unexpected error during file upload",
                error_code="upload_error",
                details=str(e)
            )
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from cloud storage
        
        Args:
            file_path: Path of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Deleting file from S3: {file_path}")
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in delete_file: {str(e)}")
            return False
    
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """
        Get a file from cloud storage
        
        Args:
            file_path: Path of the file to get
            
        Returns:
            File data as bytes if found, None otherwise
        """
        try:
            logger.info(f"Getting file from S3: {file_path}")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found in S3: {file_path}")
                return None
            else:
                logger.error(f"Error getting file from S3: {str(e)}")
                raise StorageError(
                    detail=f"Error retrieving file from storage: {str(e)}",
                    error_code="retrieval_error"
                )
        except Exception as e:
            logger.error(f"Unexpected error in get_file: {str(e)}")
            raise StorageError(
                detail="Unexpected error retrieving file",
                error_code="retrieval_error",
                details=str(e)
            )
    
    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Generate a pre-signed URL for a file
        
        Args:
            file_path: Path of the file
            expires_in: Expiration time in seconds
            
        Returns:
            Pre-signed URL
        """
        try:
            logger.info(f"Generating pre-signed URL for: {file_path}")
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            raise StorageError(
                detail="Error generating access URL",
                error_code="url_generation_error",
                details=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_file_url: {str(e)}")
            raise StorageError(
                detail="Unexpected error generating URL",
                error_code="url_generation_error",
                details=str(e)
            )
    
    def _get_content_type(self, extension: str) -> str:
        """Get content type based on file extension"""
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.pdf': 'application/pdf',
            '.json': 'application/json',
            '.html': 'text/html',
            '.txt': 'text/plain',
            '.css': 'text/css',
            '.js': 'application/javascript'
        }
        
        return content_types.get(extension, 'application/octet-stream')


# Create a singleton instance
cloud_storage = CloudStorageService()

async def get_screenshot_url(screenshot_path: str, expires_in: int = 3600) -> str:
    """
    Get a pre-signed URL for a screenshot
    
    Args:
        screenshot_path: Path of the screenshot in storage
        expires_in: Expiration time in seconds
        
    Returns:
        Pre-signed URL for the screenshot
    """
    return await cloud_storage.get_file_url(screenshot_path, expires_in) 