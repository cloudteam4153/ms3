import os
from typing import Optional, List, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()


class ClassificationClient:
    """
    HTTP client for interacting with the Classification microservice (ms4).
    Pulls classifications and creates tasks/followups based on labels.
    """
    
    def __init__(self):
        self.base_url = os.getenv(
            'CLASSIFICATION_SERVICE_URL',
            'https://ms4-classification-uq2tkhfvqa-uc.a.run.app'
        )
        self.base_url = self.base_url.rstrip('/')
        self.timeout = 30.0
    
    async def get_classifications(
        self,
        user_id: Optional[str] = None,
        label: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get classifications from ms4-classification service.
        
        Args:
            user_id: Filter by user ID
            label: Filter by label (todo, followup, noise)
            
        Returns:
            List of classification dictionaries
        """
        url = f"{self.base_url}/classifications"
        params = {}
        
        if user_id:
            params['user_id'] = user_id
        if label:
            params['label'] = label
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error fetching classifications: HTTP {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Error fetching classifications: {e}")
            return []

