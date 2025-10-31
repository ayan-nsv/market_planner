import os
import logging
from PIL import Image
from io import BytesIO
from google import genai
import requests
import base64
from typing import Dict, Any
from config.gemini_config import get_gemini_api_key

logger = logging.getLogger(__name__)


client = genai.Client(api_key=get_gemini_api_key())


ASPECT_RATIOS = {
    'instagram': '1:1',  
    'facebook': '1.91:1',  
    'linkedin': '1.91:1',  
}


async def generate_image(planner_info: Dict[str, Any]) -> bytes:
    try:
        image_prompt = planner_info["image_prompt"]
        channel = planner_info["channel"].lower()
        
        aspect_ratio = ASPECT_RATIOS.get(channel, '1:1')

        enhanced_prompt = f"""
            Generate a professional and engaging social media image for a {channel} post.
            A high-quality, photorealistic image of: {image_prompt}.
            The image should be captured with professional cinematic lighting and vibrant colors to make it stand out.
            The composition should be visually appealing and suitable for a marketing campaign.
            The image must have an aspect ratio of {aspect_ratio}.
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

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return part.inline_data.data

        raise ValueError("No image data found in the response.")

    except Exception as e:
        logger.error(f"Error generating image with Gemini API for channel '{channel}': {str(e)}")
        return None

