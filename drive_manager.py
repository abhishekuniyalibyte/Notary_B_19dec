"""
Track B - Milestone 2: Google Drive File Manager
Handles fetching, downloading, and indexing files from Google Drive.
"""

import io
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from drive_auth import DriveAuthenticator


class DriveManager:
    """
    Manages Google Drive file operations.
    Fetches customer folders and downloads files with metadata.
    """

    # Google Drive MIME types
    MIME_TYPE_FOLDER = 'application/vnd.google-apps.folder'

    # Supported document types for certificate processing
    SUPPORTED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
        'application/msword',  # DOC
        'image/jpeg',
        'image/png',
        'image/tiff',
        'text/plain'
    }

    def __init__(self, authenticator: DriveAuthenticator, download_dir: str = "./downloaded_files"):
        """
        Initialize Drive manager.

        Args:
            authenticator: Authenticated DriveAuthenticator instance
            download_dir: Local directory to download files
        """
        self.auth = authenticator
        self.service = authenticator.get_drive_service()
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def list_folders(self, parent_folder_id: Optional[str] = None) -> List[Dict]:
        """
        List all folders in Drive or within a specific parent folder.

        Args:
            parent_folder_id: ID of parent folder (None = root)

        Returns:
            List of folder metadata dictionaries
        """
        try:
            query = f"mimeType='{self.MIME_TYPE_FOLDER}'"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            query += " and trashed=false"

            results = self.service.files().list(
                q=query,
                fields="files(id, name, createdTime, modifiedTime)",
                pageSize=100
            ).execute()

            folders = results.get('files', [])
            return folders

        except HttpError as error:
            print(f"Error listing folders: {error}")
            return []

    def list_files_in_folder(self, folder_id: str, recursive: bool = True) -> List[Dict]:
        """
        List all files in a specific folder.

        Args:
            folder_id: Google Drive folder ID
            recursive: If True, include files from subfolders

        Returns:
            List of file metadata dictionaries
        """
        all_files = []

        try:
            # Get files directly in this folder
            query = f"'{folder_id}' in parents and trashed=false"

            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, parents)",
                pageSize=100
            ).execute()

            items = results.get('files', [])

            for item in items:
                if item['mimeType'] == self.MIME_TYPE_FOLDER:
                    # If recursive, process subfolders
                    if recursive:
                        subfolder_files = self.list_files_in_folder(item['id'], recursive=True)
                        all_files.extend(subfolder_files)
                else:
                    # Add file to list
                    all_files.append(item)

            return all_files

        except HttpError as error:
            print(f"Error listing files in folder {folder_id}: {error}")
            return []

    def is_supported_file(self, mime_type: str) -> bool:
        """
        Check if file type is supported for certificate processing.

        Args:
            mime_type: MIME type of file

        Returns:
            True if supported, False otherwise
        """
        return mime_type in self.SUPPORTED_MIME_TYPES

    def download_file(self, file_id: str, file_name: str, destination_path: Path) -> bool:
        """
        Download a file from Google Drive.

        Args:
            file_id: Google Drive file ID
            file_name: Name of the file
            destination_path: Local path to save file

        Returns:
            True if download successful, False otherwise
        """
        try:
            # Create parent directory if needed
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            # Request file content
            request = self.service.files().get_media(fileId=file_id)

            # Download in chunks
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    # Only print progress for large files
                    if status.total_size and status.total_size > 1024 * 1024:  # > 1MB
                        print(f"  Downloading {file_name}: {progress}%", end='\r')

            # Write to file
            with open(destination_path, 'wb') as f:
                f.write(fh.getvalue())

            return True

        except HttpError as error:
            print(f"✗ Error downloading {file_name}: {error}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error downloading {file_name}: {e}")
            return False

    def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        """
        Get detailed metadata for a specific file.

        Args:
            file_id: Google Drive file ID

        Returns:
            File metadata dictionary or None
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, parents, owners"
            ).execute()
            return file
        except HttpError as error:
            print(f"Error getting file metadata: {error}")
            return None

    def download_customer_folder(self, folder_id: str, folder_name: str) -> Dict:
        """
        Download all files from a customer folder.

        Args:
            folder_id: Google Drive folder ID
            folder_name: Name of the folder (customer name)

        Returns:
            Dictionary with download statistics and file metadata
        """
        print(f"\n📁 Processing customer folder: {folder_name}")

        # Create customer directory
        customer_dir = self.download_dir / folder_name
        customer_dir.mkdir(parents=True, exist_ok=True)

        # Get all files in folder
        files = self.list_files_in_folder(folder_id, recursive=True)

        download_stats = {
            'folder_name': folder_name,
            'folder_id': folder_id,
            'total_files': len(files),
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'file_metadata': []
        }

        for file in files:
            file_name = file['name']
            file_id = file['id']
            mime_type = file['mimeType']

            # Check if file type is supported
            if not self.is_supported_file(mime_type):
                print(f"  ⊘ Skipping unsupported: {file_name} ({mime_type})")
                download_stats['skipped'] += 1
                continue

            # Determine file path
            destination = customer_dir / file_name

            # Download file
            print(f"  ↓ Downloading: {file_name}")
            success = self.download_file(file_id, file_name, destination)

            if success:
                download_stats['downloaded'] += 1

                # Store metadata
                metadata = {
                    'file_id': file_id,
                    'file_name': file_name,
                    'local_path': str(destination),
                    'mime_type': mime_type,
                    'size': file.get('size', 0),
                    'created_time': file.get('createdTime'),
                    'modified_time': file.get('modifiedTime')
                }
                download_stats['file_metadata'].append(metadata)
            else:
                download_stats['failed'] += 1

        # Summary
        print(f"\n  ✓ Downloaded: {download_stats['downloaded']}")
        print(f"  ⊘ Skipped: {download_stats['skipped']}")
        print(f"  ✗ Failed: {download_stats['failed']}")

        return download_stats

    def download_all_customer_folders(self, parent_folder_id: Optional[str] = None) -> List[Dict]:
        """
        Download files from all customer folders in Drive.

        Args:
            parent_folder_id: ID of parent folder containing customer folders (None = root)

        Returns:
            List of download statistics for each customer folder
        """
        print("=" * 70)
        print("  DOWNLOADING CUSTOMER FOLDERS FROM GOOGLE DRIVE")
        print("=" * 70)

        # List all customer folders
        folders = self.list_folders(parent_folder_id)

        if not folders:
            print("\n✗ No folders found.")
            return []

        print(f"\nFound {len(folders)} customer folders\n")

        all_stats = []

        for folder in folders:
            folder_name = folder['name']
            folder_id = folder['id']

            stats = self.download_customer_folder(folder_id, folder_name)
            all_stats.append(stats)

        # Overall summary
        print("\n" + "=" * 70)
        print("  DOWNLOAD SUMMARY")
        print("=" * 70)
        total_downloaded = sum(s['downloaded'] for s in all_stats)
        total_skipped = sum(s['skipped'] for s in all_stats)
        total_failed = sum(s['failed'] for s in all_stats)

        print(f"\nTotal Customers: {len(all_stats)}")
        print(f"Total Downloaded: {total_downloaded}")
        print(f"Total Skipped: {total_skipped}")
        print(f"Total Failed: {total_failed}")

        return all_stats

    def search_folder_by_name(self, folder_name: str) -> Optional[Dict]:
        """
        Search for a folder by name.

        Args:
            folder_name: Name to search for

        Returns:
            Folder metadata or None
        """
        try:
            query = f"mimeType='{self.MIME_TYPE_FOLDER}' and name contains '{folder_name}' and trashed=false"

            results = self.service.files().list(
                q=query,
                fields="files(id, name, createdTime, modifiedTime)",
                pageSize=10
            ).execute()

            folders = results.get('files', [])

            if folders:
                return folders[0]  # Return first match
            return None

        except HttpError as error:
            print(f"Error searching for folder: {error}")
            return None

    def get_folder_structure(self, folder_id: str, indent: int = 0) -> None:
        """
        Print folder structure recursively.

        Args:
            folder_id: Google Drive folder ID
            indent: Current indentation level
        """
        try:
            # Get items in this folder
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                pageSize=100
            ).execute()

            items = results.get('files', [])

            for item in items:
                prefix = "  " * indent
                if item['mimeType'] == self.MIME_TYPE_FOLDER:
                    print(f"{prefix}📁 {item['name']}/")
                    self.get_folder_structure(item['id'], indent + 1)
                else:
                    print(f"{prefix}📄 {item['name']}")

        except HttpError as error:
            print(f"Error getting folder structure: {error}")
