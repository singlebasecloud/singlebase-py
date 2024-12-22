from . import lib
import requests
import aiohttp
import asyncio
from typing import Union, Optional

class SinglebaseError(Exception):
    """Custom exception for Singlebase specific errors."""
    pass

class Result(object):
    """
    Represents the result of an API operation.
    
    Attributes:
        data (dict): The response data from the API
        meta (dict): Metadata associated with the response
        ok (bool): Whether the operation was successful
        error (str): Error message if operation failed
        status_code (int): HTTP status code of the response
    """
    def __init__(self, **kw):
        self.data = kw.get("data") or {}
        self.meta = kw.get("meta") or {}
        self.ok = kw.get("ok") if "ok" in kw else True
        self.error = kw.get("error") or None 
        self.status_code = kw.get("status_code") or 200

    def to_dict(self) -> dict:
        """
        Convert the result object to a dictionary.
        
        Returns:
            dict: Dictionary representation of the result
        """
        return {
            "data": self.data,
            "meta": self.meta,
            "ok": self.ok,
            "error": self.error,
            "status_code": self.status_code
        }

class ResultOK(Result):
    """Represents a successful API operation result."""
    pass

class ResultError(Result):
    """Represents a failed API operation result."""
    pass

class Client(object):
    """
    Client for interacting with the Singlebase API.
    Supports both synchronous and asynchronous operations.

    Attributes:
        auth: Synchronous authentication operations
        db: Synchronous database operations with format (action: str, collection: str, payload: dict)
        storage: Synchronous storage operations
        genai: Synchronous AI generation operations
        vectordb: Synchronous vector database operations
        
        auth_async: Asynchronous authentication operations
        db_async: Asynchronous database operations
        storage_async: Asynchronous storage operations
        genai_async: Asynchronous AI generation operations
        vectordb_async: Asynchronous vector database operations
    
    Examples:
        # Initialize the client
        client = Client(
            api_url="https://cloud.singlebaseapis.com/api/",
            api_key="your-api-key"
        )

        # Synchronous database operations
        # Fetch users over 18
        result = client.db("fetch", "users", {
            "query": {"age": {"$gt": 18}}
        })
        
        # Insert a new user
        result = client.db("insert", "users", {
            "document": {
                "name": "John Doe",
                "age": 25,
                "email": "john@example.com"
            }
        })

        # Asynchronous database operations
        async with Client(
            api_url="https://cloud.singlebaseapis.com/api/",
            api_key="your-api-key"
        ) as client:
            # Fetch users asynchronously
            result = await client.db_async("fetch", "users", {
                "query": {"age": {"$gt": 18}}
            })

        # Other API operations
        # Authentication
        auth_result = client.auth("login", {
            "email": "user@example.com",
            "password": "secretpass"
        })

        # Storage operations
        storage_result = client.storage("upload", {
            "file": "path/to/file.pdf"
        })

        # AI Generation
        genai_result = client.genai("generate", {
            "prompt": "Write a story about..."
        })

        # Vector database operations
        vector_result = client.vectordb("search", {
            "query": "similar documents to..."
        })
    """

    def __init__(self, api_url: str, api_key: str) -> None:
        """
        Initialize a new Singlebase client.
        
        Args:
            api_url (str): The base URL for the Singlebase API
            api_key (str): API key for authentication
        """
        self._api_url = api_url
        self._api_key = api_key
        self._session = None

        # Initialize sync methods
        self.auth = self._make_factory('auth')
        self.db = self._make_db_factory()  # Special handling for db operations
        self.storage = self._make_factory('storage')
        self.genai = self._make_factory('genai')
        self.vectordb = self._make_factory('vectordb')

        # Initialize async methods
        self.auth_async = self._make_factory('auth', is_async=True)
        self.db_async = self._make_db_factory(is_async=True)  # Special handling for async db operations
        self.storage_async = self._make_factory('storage', is_async=True)
        self.genai_async = self._make_factory('genai', is_async=True)
        self.vectordb_async = self._make_factory('vectordb', is_async=True)

    def _make_db_factory(self, is_async: bool = False):
        """
        Creates a database operation factory that can be either synchronous or asynchronous.
        
        Args:
            is_async (bool): Whether to create an async factory
        
        Returns:
            callable: A function that dispatches database requests with action, collection, and payload
        """
        request_method = self.request_async if is_async else self.request
        
        def db_operation(action: str, collection: str, payload: dict = {}):
            """
            Execute a database operation.
            
            Args:
                action (str): The database action to perform (e.g., "fetch", "insert", "update")
                collection (str): The collection to operate on
                payload (dict, optional): Additional payload data for the operation
                
            Returns:
                Result: The API response wrapped in a Result object
            """
            combined_payload = {
                "action": f"db.{action}",
                "collection": collection,
                **payload
            }
            return request_method(combined_payload)
        return db_operation

    def _make_factory(self, base: str, is_async: bool = False):
        """
        Creates an operation factory for a specific API base that can be either synchronous or asynchronous.
        
        Args:
            base (str): The base endpoint name
            is_async (bool): Whether to create an async factory
            
        Returns:
            callable: A function that dispatches requests to the specified base endpoint
        """
        request_method = self.request_async if is_async else self.request
        return lambda action, payload={}: request_method({"action": f"{base}.{action}", **payload})

    async def __aenter__(self):
        """Set up async context manager."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context manager."""
        if self._session:
            await self._session.close()

    def request(self, payload: dict, headers: dict = {}) -> Result:
        """
        Synchronously dispatch a request to the API.
        
        Args:
            payload (dict): The request payload
            headers (dict, optional): Additional headers to include
            
        Returns:
            Result: The API response wrapped in a Result object
            
        Raises:
            SinglebaseError: If the action is missing from the payload
        """
        try:
            if "action" not in payload:
                raise SinglebaseError("Request missing @action")

            _headers = {
                **headers,
                "x-api-key": self._api_key,
                "x-sbc-sdk-client": "singlebase-py"
            }
            r = requests.post(self._api_url, json=payload, headers=_headers)
            resp = lib.json_loads(r.text)
            if r.status_code == requests.codes.ok:
                return ResultOK(data=resp.get("data"), meta=resp.get("meta"), status_code=200, ok=True)
            else:
                return ResultError(error=resp.get("error"), status_code=r.status_code, ok=False)
        except Exception as e:
            return ResultError(error=f"EXCEPTION: {e}", status_code=500, ok=False)

    async def request_async(self, payload: dict, headers: dict = {}) -> Result:
        """
        Asynchronously dispatch a request to the API.
        
        Args:
            payload (dict): The request payload
            headers (dict, optional): Additional headers to include
            
        Returns:
            Result: The API response wrapped in a Result object
            
        Raises:
            SinglebaseError: If the action is missing from the payload
        """
        try:
            if "action" not in payload:
                raise SinglebaseError("Request missing @action")

            _headers = {
                **headers,
                "x-api-key": self._api_key,
                "x-sbc-sdk-client": "singlebase-py"
            }

            if not self._session:
                self._session = aiohttp.ClientSession()

            async with self._session.post(self._api_url, json=payload, headers=_headers) as response:
                resp_text = await response.text()
                resp = lib.json_loads(resp_text)
                
                if response.status == 200:
                    return ResultOK(data=resp.get("data"), meta=resp.get("meta"), status_code=200, ok=True)
                else:
                    return ResultError(error=resp.get("error"), status_code=response.status, ok=False)
        except Exception as e:
            return ResultError(error=f"EXCEPTION: {e}", status_code=500, ok=False)

async def upload_presigned_file_async(filepath: str, data: dict) -> bool:
    """
    Asynchronously upload a file using presigned URL data.
    
    Args:
        filepath (str): Path to the file to upload
        data (dict): Presigned URL data containing 'url' and 'fields'
        
    Returns:
        bool: True if upload was successful
        
    Raises:
        aiohttp.ClientError: If the upload fails
    """
    async with aiohttp.ClientSession() as session:
        async with open(filepath, 'rb') as f2u:
            form = aiohttp.FormData()
            for key, value in data['fields'].items():
                form.add_field(key, value)
            form.add_field('file', f2u, filename=filepath)
            
            async with session.post(data['url'], data=form) as response:
                response.raise_for_status()
                return True

def upload_presigned_file(filepath: str, data: dict) -> bool:
    """
    Synchronously upload a file using presigned URL data.
    
    Args:
        filepath (str): Path to the file to upload
        data (dict): Presigned URL data containing 'url' and 'fields'
        
    Returns:
        bool: True if upload was successful
        
    Raises:
        requests.exceptions.RequestException: If the upload fails
    """
    with open(filepath, 'rb') as f2u:
        files = {'file': (filepath, f2u)}
        resp = requests.post(data['url'], data=data['fields'], files=files)
        resp.raise_for_status()
        return True