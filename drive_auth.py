"""
Track B - Milestone 2: Google Drive Authentication
Handles OAuth 2.0 authentication for Google Drive API access.
"""

import os
import pickle
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes required for read-only Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class DriveAuthenticator:
    """
    Manages Google Drive OAuth 2.0 authentication.
    Handles token storage, refresh, and service creation.
    """

    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.pickle"):
        """
        Initialize authenticator.

        Args:
            credentials_path: Path to OAuth client credentials JSON file
            token_path: Path to store/load authentication token
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.creds: Optional[Credentials] = None
        self.service = None

    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API.
        Uses existing token if available, otherwise initiates OAuth flow.

        Returns:
            True if authentication successful, False otherwise
        """
        # Load existing token if available
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Refresh expired token
                try:
                    self.creds.refresh(Request())
                    print("Token refreshed successfully")
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    self.creds = None

            # If still no valid credentials, run OAuth flow
            if not self.creds:
                if not self.credentials_path.exists():
                    print(f"Error: Credentials file not found: {self.credentials_path}")
                    print("\nTo get credentials:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a project (or select existing)")
                    print("3. Enable Google Drive API")
                    print("4. Create OAuth 2.0 credentials (Desktop app)")
                    print("5. Download JSON and save as 'credentials.json'")
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                    print("Authentication successful!")
                except Exception as e:
                    print(f"Authentication failed: {e}")
                    return False

            # Save credentials for next time
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
                print(f"Token saved to: {self.token_path}")

        return True

    def get_drive_service(self):
        """
        Get authenticated Google Drive service.

        Returns:
            Google Drive API service object

        Raises:
            ValueError: If not authenticated
        """
        if not self.creds:
            raise ValueError("Not authenticated. Call authenticate() first.")

        if not self.service:
            try:
                self.service = build('drive', 'v3', credentials=self.creds)
            except HttpError as error:
                print(f"Error creating Drive service: {error}")
                raise

        return self.service

    def test_connection(self) -> bool:
        """
        Test Drive API connection by listing root folders.

        Returns:
            True if connection works, False otherwise
        """
        try:
            service = self.get_drive_service()
            results = service.files().list(
                pageSize=10,
                fields="files(id, name, mimeType)"
            ).execute()

            items = results.get('files', [])
            print(f"✓ Connection successful. Found {len(items)} items in Drive.")
            return True

        except HttpError as error:
            print(f"✗ Connection test failed: {error}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return False

    def revoke_credentials(self):
        """
        Revoke credentials and delete token file.
        Useful for testing or switching accounts.
        """
        if self.token_path.exists():
            self.token_path.unlink()
            print(f"Token deleted: {self.token_path}")

        self.creds = None
        self.service = None
        print("Credentials revoked. Run authenticate() to re-authorize.")


def setup_drive_auth() -> Optional[DriveAuthenticator]:
    """
    Helper function to set up Drive authentication.
    Returns authenticated DriveAuthenticator or None if failed.
    """
    auth = DriveAuthenticator()

    print("Authenticating with Google Drive...")
    if not auth.authenticate():
        return None

    print("Testing connection...")
    if not auth.test_connection():
        return None

    return auth


if __name__ == '__main__':
    """
    Test authentication standalone.
    Usage: python drive_auth.py
    """
    print("=" * 70)
    print("  Google Drive Authentication Test")
    print("=" * 70)

    auth = setup_drive_auth()

    if auth:
        print("\n✓ Authentication complete and ready to use!")
    else:
        print("\n✗ Authentication failed. Please check your credentials.")
