import os
import logging
from PIL import Image
from io import BytesIO
from google import genai
import requests
import base64
from typing import Dict, Any, Tuple, Optional
from config.gemini_config import get_gemini_api_key

logger = logging.getLogger(__name__)


client = genai.Client(api_key=get_gemini_api_key())


ASPECT_RATIOS = {
    'instagram': '1:1',  
    'facebook': '1.91:1',  
    'linkedin': '1.91:1',  
}


async def generate_image(planner_info: Dict[str, Any]) -> Optional[Tuple[bytes, str]]:
    try:
        image_prompt = planner_info["image_prompt"]
        channel = planner_info["channel"].lower()
        
        aspect_ratio = ASPECT_RATIOS.get(channel, '1:1')

        enhanced_prompt = f"""
        Generate a professional, high-quality, photorealistic image for a {channel} post.
        Subject: {image_prompt}.
        Use cinematic lighting, vibrant colors, and visually appealing composition suitable for a marketing campaign.
        The image must have an aspect ratio of {aspect_ratio}.
        Do not include any text, words, letters, logos, watermarks, or overlays — only visuals.
        """
        if channel == 'instagram':
            pass
        elif channel == 'linkedin':
            enhanced_prompt += " The style should be corporate and sophisticated."
        elif channel == 'facebook':
            pass

        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[enhanced_prompt],
        )

        # Extract image data; if it's already bytes, use as-is. If it's a string, decode as base64.
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                mime_type = getattr(part.inline_data, "mime_type", None) or "image/png"
                data_field = part.inline_data.data

                # If SDK returns bytes/bytearray, assume it's raw image bytes
                if isinstance(data_field, (bytes, bytearray)):
                    image_bytes = bytes(data_field)
                else:
                    # If it's a string, attempt strict base64 decode
                    if isinstance(data_field, str):
                        try:
                            image_bytes = base64.b64decode(data_field, validate=True)
                        except Exception:
                            # If not valid base64, treat as UTF-8 bytes (best effort)
                            image_bytes = data_field.encode("utf-8")
                    else:
                        # Unknown type; coerce via bytes()
                        image_bytes = bytes(data_field)
                return image_bytes, mime_type

        raise ValueError("No image data found in the response.")

    except Exception as e:
        logger.error(f"Error generating image with Gemini API for channel '{channel}': {str(e)}")
        return None

