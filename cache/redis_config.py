from dotenv import load_dotenv
import os
import httpx
from urllib.parse import quote
import json
from datetime import datetime

from utils.logger import setup_logger

load_dotenv()

logger = setup_logger("marketing-app")


class FirestoreJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Firestore datetime objects and other non-serializable types"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        if hasattr(obj, 'isoformat') and callable(getattr(obj, 'isoformat')):
            try:
                return obj.isoformat()
            except:
                pass
        
        if hasattr(obj, '__class__') and 'SERVER_TIMESTAMP' in str(type(obj)):
            return None
        
        try:
            return str(obj)
        except:
            return super().default(obj)


def json_dumps_firestore(obj):
    """JSON dumps with Firestore datetime support"""
    return json.dumps(obj, cls=FirestoreJSONEncoder, default=str)


UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

DEFAULT_TTL = 172800  # 2 days in seconds

_httpx_client = None


def get_httpx_client():
    """Get or create singleton httpx async client with connection pooling"""
    global _httpx_client
    if _httpx_client is None:
        limits = httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20
        )
        _httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=2.0),
            limits=limits,
            follow_redirects=True
        )
    return _httpx_client


async def close_httpx_client():
    """Close the httpx client (call on app shutdown)"""
    global _httpx_client
    if _httpx_client is not None:
        try:
            await _httpx_client.aclose()
            _httpx_client = None
            logger.info("Redis httpx client closed successfully")
        except Exception as e:
            logger.warning(f"Error closing Redis httpx client (this is normal during shutdown): {str(e)}")
            _httpx_client = None


async def redis_set(key, value, ttl=None):
    """
    Set a key-value pair in Redis with optional TTL.
    """
    try:
        if not UPSTASH_URL or not UPSTASH_TOKEN:
            logger.warning("Redis credentials not configured, skipping cache set")
            return False
        
        ttl = ttl if ttl is not None else DEFAULT_TTL
        
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, cls=FirestoreJSONEncoder)
        elif isinstance(value, str):
            value_str = value
        else:
            value_str = str(value)
        
        # Use pipeline for all operations
        if ttl > 0:
            command = ["SETEX", key, str(ttl), value_str]
        else:
            command = ["SET", key, value_str]
        
        client = get_httpx_client()
        
        response = await client.post(
            f"{UPSTASH_URL}/pipeline",
            headers={
                "Authorization": f"Bearer {UPSTASH_TOKEN}",
                "Content-Type": "application/json"
            },
            json=[command]
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Handle response format
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            if isinstance(first_result, dict):
                return first_result.get("result") == "OK"
            elif first_result == "OK":
                return True
        
        logger.warning(f"Unexpected SET response format: {result}")
        return False
        
    except httpx.HTTPStatusError as e:
        try:
            error_body = e.response.text
            logger.error(f"Redis SET HTTP error for key '{key}': {e.response.status_code} - {error_body}")
        except:
            logger.error(f"Redis SET HTTP error for key '{key}': {e.response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in redis_set for key '{key}': {str(e)}")
        return False


async def redis_get(key):
    """
    Get a value from Redis by key.
    """
    try:
        if not UPSTASH_URL or not UPSTASH_TOKEN:
            logger.warning("Redis credentials not configured, skipping cache get")
            return None
        
        encoded_key = quote(str(key), safe='')
        
        client = get_httpx_client()
        response = await client.get(
            f"{UPSTASH_URL}/get/{encoded_key}",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        response.raise_for_status()
        result = response.json()
        
        value = result.get("result")
        if value is None:
            return None
        
        # Try to parse as JSON, return as string if not valid JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        logger.error(f"Redis GET error for key '{key}': {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in redis_get for key '{key}': {str(e)}")
        return None


async def redis_delete(key):
    """
    Delete a key from Redis.
    """
    try:
        if not UPSTASH_URL or not UPSTASH_TOKEN:
            logger.warning("Redis credentials not configured, skipping cache delete")
            return False
        
        encoded_key = quote(str(key), safe='')
        
        client = get_httpx_client()
        response = await client.post(
            f"{UPSTASH_URL}/del/{encoded_key}",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        response.raise_for_status()
        result = response.json()
        
        return result.get("result", 0) >= 1
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return False
        logger.error(f"Redis DELETE error for key '{key}': {e.response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in redis_delete for key '{key}': {str(e)}")
        return False


# ==================== Redis List Operations ====================

async def redis_list_push(key, value):
    """
    Add an item to the end of a Redis list (RPUSH).
    """
    try:
        if not UPSTASH_URL or not UPSTASH_TOKEN:
            logger.warning("Redis credentials not configured, skipping list push")
            return False
        
        # Convert value to JSON with Firestore datetime support
        json_value = json_dumps_firestore(value)
        
        # Use pipeline endpoint for consistency
        command = ["RPUSH", key, json_value]
        
        client = get_httpx_client()
        response = await client.post(
            f"{UPSTASH_URL}/pipeline",
            headers={
                "Authorization": f"Bearer {UPSTASH_TOKEN}",
                "Content-Type": "application/json"
            },
            json=[command]
        )
        response.raise_for_status()
        result = response.json()
        
        # Handle response format - RPUSH returns the list length
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            if isinstance(first_result, dict):
                return first_result.get("result") is not None
            elif isinstance(first_result, int):
                return True
        
        return False
        
    except httpx.HTTPStatusError as e:
        try:
            error_body = e.response.text
            logger.error(f"Redis LIST PUSH HTTP error for key '{key}': {e.response.status_code} - {error_body}")
        except:
            logger.error(f"Redis LIST PUSH HTTP error for key '{key}': {e.response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in redis_list_push for key '{key}': {str(e)}")
        return False


async def redis_list_get_all(key):
    """
    Get all items from a Redis list (LRANGE 0 -1).
    
    CRITICAL FIX: Upstash returns raw strings, NOT URL-encoded strings.
    We should NOT use unquote() on the items.
    """
    try:
        if not UPSTASH_URL or not UPSTASH_TOKEN:
            logger.warning("Redis credentials not configured, skipping list get")
            return []
        
        # Use pipeline for consistency
        command = ["LRANGE", key, "0", "-1"]
        
        client = get_httpx_client()
        response = await client.post(
            f"{UPSTASH_URL}/pipeline",
            headers={
                "Authorization": f"Bearer {UPSTASH_TOKEN}",
                "Content-Type": "application/json"
            },
            json=[command]
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract items from response
        items = []
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            if isinstance(first_result, dict):
                items = first_result.get("result", [])
            elif isinstance(first_result, list):
                items = first_result
        
        if not items:
            return []
        
        # CRITICAL FIX: Items are already raw strings from Upstash
        # Do NOT use unquote() - just parse JSON directly
        decoded_items = []
        for item in items:
            try:
                # Item is already a plain string - parse JSON directly
                decoded_items.append(json.loads(item))
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to decode list item from key '{key}': {str(e)[:100]}")
                continue
        
        return decoded_items
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return []
        try:
            error_body = e.response.text
            logger.error(f"Redis LIST GET ALL HTTP error for key '{key}': {e.response.status_code} - {error_body}")
        except:
            logger.error(f"Redis LIST GET ALL HTTP error for key '{key}': {e.response.status_code}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in redis_list_get_all for key '{key}': {str(e)}")
        return []


async def redis_list_set_all(key, items, ttl=None):
    """
    Replace entire list with new items. Deletes old list and creates new one.
    Uses multi-command pipeline for atomicity.
    """
    try:
        if not UPSTASH_URL or not UPSTASH_TOKEN:
            logger.warning("Redis credentials not configured, skipping list set all")
            return False
        
        ttl = ttl if ttl is not None else DEFAULT_TTL
        
        # Build pipeline commands
        commands = []
        
        # 1. Delete old list
        commands.append(["DEL", key])
        
        # 2. Push all items (if any)
        if items:
            for item in items:
                json_value = json_dumps_firestore(item)
                commands.append(["RPUSH", key, json_value])
        
        # 3. Set TTL if provided
        if ttl > 0 and items:
            commands.append(["EXPIRE", key, str(ttl)])
        
        client = get_httpx_client()
        
        # Execute all commands in one pipeline request
        response = await client.post(
            f"{UPSTASH_URL}/pipeline",
            headers={
                "Authorization": f"Bearer {UPSTASH_TOKEN}",
                "Content-Type": "application/json"
            },
            json=commands
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Verify pipeline execution succeeded
        if isinstance(result, list) and len(result) > 0:
            return True
        
        return False
        
    except httpx.HTTPStatusError as e:
        try:
            error_body = e.response.text
            logger.error(f"Redis LIST SET ALL HTTP error for key '{key}': {e.response.status_code} - {error_body}")
        except:
            logger.error(f"Redis LIST SET ALL HTTP error for key '{key}': {e.response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in redis_list_set_all for key '{key}': {str(e)}")
        return False


async def redis_list_remove_by_value(key, value):
    """
    Remove all occurrences of a value from a Redis list (LREM).
    """
    try:
        if not UPSTASH_URL or not UPSTASH_TOKEN:
            logger.warning("Redis credentials not configured, skipping list remove")
            return 0
        
        # Convert value to JSON for comparison (must match how it was stored)
        json_value = json_dumps_firestore(value)
        
        # Use pipeline endpoint
        command = ["LREM", key, "0", json_value]
        
        client = get_httpx_client()
        response = await client.post(
            f"{UPSTASH_URL}/pipeline",
            headers={
                "Authorization": f"Bearer {UPSTASH_TOKEN}",
                "Content-Type": "application/json"
            },
            json=[command]
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract count from response
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            if isinstance(first_result, dict):
                return first_result.get("result", 0)
            elif isinstance(first_result, int):
                return first_result
        
        return 0
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return 0
        try:
            error_body = e.response.text
            logger.error(f"Redis LIST REMOVE HTTP error for key '{key}': {e.response.status_code} - {error_body}")
        except:
            logger.error(f"Redis LIST REMOVE HTTP error for key '{key}': {e.response.status_code}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error in redis_list_remove_by_value for key '{key}': {str(e)}")
        return 0