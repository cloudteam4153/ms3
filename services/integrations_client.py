import os
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()


class IntegrationsClient:
    """
    HTTP client for interacting with the Integrations microservice.
    Retrieves full message content using message_id.
    """
    
    def __init__(self):
        self.base_url = os.getenv(
            'INTEGRATIONS_SERVICE_URL',
            'https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app'
        )
        # Remove trailing slash if present
        self.base_url = self.base_url.rstrip('/')
        self.timeout = 10.0  # 10 second timeout
    
    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a full message from the integrations service by message_id.
        
        Args:
            message_id: The UUID of the message to retrieve
            
        Returns:
            Dictionary containing message data, or None if not found/error
        """
        url = f"{self.base_url}/messages/{message_id}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    print(f"Message {message_id} not found in integrations service")
                    return None
                else:
                    print(f"Error fetching message {message_id}: HTTP {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            print(f"Timeout while fetching message {message_id} from integrations service")
            return None
        except httpx.RequestError as e:
            print(f"Request error while fetching message {message_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching message {message_id}: {e}")
            return None
    
    def get_message_sync(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous version of get_message (for non-async contexts).
        Note: This blocks the thread, prefer async version when possible.
        
        Args:
            message_id: The UUID of the message to retrieve
        """
        url = f"{self.base_url}/messages/{message_id}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    print(f"Message {message_id} not found in integrations service")
                    return None
                else:
                    print(f"Error fetching message {message_id}: HTTP {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            print(f"Timeout while fetching message {message_id} from integrations service")
            return None
        except httpx.RequestError as e:
            print(f"Request error while fetching message {message_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching message {message_id}: {e}")
            return None
