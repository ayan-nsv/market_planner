import os
import logging
import asyncio
import re
from PIL import Image
from io import BytesIO
from google import genai
import requests
import base64
from typing import Dict, Any, Tuple, Optional
from config.gemini_config import get_gemini_api_key
from utils.logger import setup_logger

logger = setup_logger("marketing-app")


client = genai.Client(api_key=get_gemini_api_key())

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 120.0  # seconds


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

def _extract_retry_delay(error_message: str) -> float:
    """
    Extract retry delay from Gemini API error message.
    Looks for patterns like "Please retry in 32.926273298s"
    """
    # Try to find retry delay in seconds
    match = re.search(r'retry in ([\d.]+)s', error_message, re.IGNORECASE)
    if match:
        try:
            delay = float(match.group(1))
            # Add small buffer (10%) and cap at max delay
            return min(delay * 1.1, MAX_RETRY_DELAY)
        except ValueError:
            pass
    
    # Fallback: try to find delay in RetryInfo
    match = re.search(r'"retryDelay":\s*"(\d+)s"', error_message)
    if match:
        try:
            return min(float(match.group(1)) * 1.1, MAX_RETRY_DELAY)
        except ValueError:
            pass
    
    return INITIAL_RETRY_DELAY


def _is_rate_limit_error(error: Exception) -> bool:
    """Check if error is a rate limit/quota error"""
    error_str = str(error)
    return (
        "429" in error_str or
        "RESOURCE_EXHAUSTED" in error_str or
        "quota" in error_str.lower() or
        "rate limit" in error_str.lower()
    )


def _resize_image_with_pil(image_bytes: bytes, target_ratio: str, mime_type: str) -> Tuple[bytes, str]:
    """
    Resize image to target aspect ratio using PIL with smart padding/cropping.
    This is a fallback when AI-based reformatting doesn't work.
    """
    from PIL import Image, ImageOps
    from io import BytesIO
    
    try:
        # Parse target ratio
        ratio_parts = target_ratio.split(':')
        if len(ratio_parts) != 2:
            raise ValueError(f"Invalid target ratio format: {target_ratio}")
        target_ratio_value = float(ratio_parts[0]) / float(ratio_parts[1])
        
        # Open image - convert to RGB if needed for consistent handling
        img = Image.open(BytesIO(image_bytes))
        original_width, original_height = img.size
        original_ratio = original_width / original_height
        
        # Convert to RGB if image has transparency or is in a mode we can't handle
        if img.mode in ('RGBA', 'LA', 'P'):
            # Convert to RGB with white background
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            img = rgb_img
        elif img.mode not in ('RGB', 'L'):
            # Convert other modes to RGB
            img = img.convert('RGB')
        
        # Calculate new dimensions
        if original_ratio > target_ratio_value:
            # Image is wider than target - need to add height (pad top/bottom)
            new_width = original_width
            new_height = int(original_width / target_ratio_value)
            # Center the original image vertically
            paste_y = (new_height - original_height) // 2
            paste_x = 0
        else:
            # Image is taller than target - need to add width (pad left/right)
            new_height = original_height
            new_width = int(original_height * target_ratio_value)
            # Center the original image horizontally
            paste_x = (new_width - original_width) // 2
            paste_y = 0
        
        # Get edge color for padding (with fallback)
        try:
            edge_color = _get_edge_color(img)
        except Exception as e:
            logger.warning(f"Could not get edge color, using white: {str(e)}")
            edge_color = (255, 255, 255)
        
        # Create new image with target aspect ratio
        new_img = Image.new('RGB', (new_width, new_height), edge_color)
        new_img.paste(img, (paste_x, paste_y))
        
        # Save to bytes - always use PNG for reliability, or JPEG if original was JPEG
        output = BytesIO()
        output_format = 'PNG'  # Default to PNG for reliability
        if mime_type and 'jpeg' in mime_type.lower() or 'jpg' in mime_type.lower():
            output_format = 'JPEG'
            new_img.save(output, format='JPEG', quality=95, optimize=True)
        else:
            new_img.save(output, format='PNG', optimize=True)
        output.seek(0)
        
        # Update mime type based on output format
        output_mime_type = 'image/jpeg' if output_format == 'JPEG' else 'image/png'
        
        logger.info(
            f"PIL resize: {original_width}x{original_height} ({original_ratio:.3f}) -> "
            f"{new_width}x{new_height} ({new_width/new_height:.3f}, target: {target_ratio_value:.3f})"
        )
        
        return output.getvalue(), output_mime_type
        
    except Exception as e:
        logger.error(f"Error in PIL resize: {str(e)}", exc_info=True)
        raise


def _get_edge_color(img: Image.Image) -> tuple:
    """Get average color from image edges for seamless padding."""
    width, height = img.size
    edge_pixels = []
    
    # Ensure image is RGB mode
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Sample edge pixels (top, bottom, left, right)
    sample_size = min(10, max(1, width // 4), max(1, height // 4))
    step_x = max(1, width // sample_size) if sample_size > 0 else 1
    step_y = max(1, height // sample_size) if sample_size > 0 else 1
    
    try:
        for x in range(0, width, step_x):
            if height > 0:
                edge_pixels.append(img.getpixel((x, 0)))  # Top
                edge_pixels.append(img.getpixel((x, height - 1)))  # Bottom
        for y in range(0, height, step_y):
            if width > 0:
                edge_pixels.append(img.getpixel((0, y)))  # Left
                edge_pixels.append(img.getpixel((width - 1, y)))  # Right
    except Exception as e:
        logger.warning(f"Error sampling edge pixels: {str(e)}")
        # Fallback: sample corners
        edge_pixels = [
            img.getpixel((0, 0)),
            img.getpixel((width - 1, 0)),
            img.getpixel((0, height - 1)),
            img.getpixel((width - 1, height - 1))
        ]
    
    if not edge_pixels:
        return (255, 255, 255)  # Default to white if no pixels sampled
    
    # Calculate average (image is guaranteed to be RGB at this point)
    r = sum(p[0] for p in edge_pixels) // len(edge_pixels)
    g = sum(p[1] for p in edge_pixels) // len(edge_pixels)
    b = sum(p[2] for p in edge_pixels) // len(edge_pixels)
    return (r, g, b)


async def generate_reformatted_image(image_bytes_base64: str, target_ratio: str) -> Optional[Tuple[bytes, str]]:
    """
    Generate reformatted image with retry logic for rate limits.
    Falls back to PIL-based resizing if Gemini doesn't produce correct aspect ratio.
    """
    # Decode base64 to raw bytes - this is much more efficient than sending as text
    # Sending binary data via inline_data uses FAR fewer tokens than base64 text

    try:
        image_bytes_raw = base64.b64decode(image_bytes_base64, validate=True)
        image_size_mb = len(image_bytes_raw) / (1024 * 1024)
        logger.debug(f"Decoded image: {image_size_mb:.2f} MB raw bytes (vs ~{len(image_bytes_base64)/1024/1024:.2f} MB base64 text)")
    except Exception as e:
        logger.error(f"Failed to decode base64 image: {str(e)}")
        return None
    
    # Detect mime type from image bytes (simple heuristic based on magic numbers)
    mime_type = "image/jpeg"  # Default
    if len(image_bytes_raw) >= 4 and image_bytes_raw[:4] == b'\x89PNG':
        mime_type = "image/png"
    elif len(image_bytes_raw) >= 2 and image_bytes_raw[:2] == b'\xff\xd8':
        mime_type = "image/jpeg"
    elif len(image_bytes_raw) >= 6 and image_bytes_raw[:6] in (b'GIF87a', b'GIF89a'):
        mime_type = "image/gif"
    elif len(image_bytes_raw) >= 12 and image_bytes_raw[:4] == b'RIFF' and image_bytes_raw[8:12] == b'WEBP':
        mime_type = "image/webp"
    
    # Store original image bytes for fallback
    original_image_bytes = image_bytes_raw
    original_mime_type = mime_type
    
    # Create a more explicit prompt for image reformatting
    # The image and text should be in the same content object for better context
    prompt_text = f"""IMPORTANT: You must REFORMAT the provided image to have an aspect ratio of exactly {target_ratio}.

    STEP-BY-STEP INSTRUCTIONS:
    1. Look at the image provided below
    2. Calculate what dimensions are needed for aspect ratio {target_ratio}
    3. Use AI outpainting to intelligently extend the image borders (add content to sides/top/bottom as needed)
    4. DO NOT crop any part of the original image
    5. DO NOT stretch or distort the original image
    6. DO NOT generate a completely new image - you must work with the provided image
    7. The output image MUST have the exact aspect ratio of {target_ratio}
    8. Maintain all original colors, style, lighting, and visual elements from the provided image

    EXAMPLE: If the target ratio is "3:2" and the original is square (1:1), you need to add content to the left and right sides to make it wider, keeping the original centered.

    Target aspect ratio: {target_ratio}
    Now reformat the image below to match this ratio:"""
    
    retry_delay = INITIAL_RETRY_DELAY
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            # Put image and text in the same content object for better context understanding
            # This format ensures the model understands the image and instructions together
            contents_list = [
                {
                    "parts": [
                        {"text": prompt_text},
                        {"inline_data": {"mime_type": mime_type, "data": image_bytes_raw}}
                    ]
                }
            ]
            
            logger.debug(f"Requesting image reformatting to {target_ratio} (attempt {attempt + 1})")
            
            response = client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=contents_list,
            )

            # Extract image from response
            if response.candidates and len(response.candidates) > 0:
                for part in response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        result_mime_type = getattr(part.inline_data, "mime_type", None) or "image/png"
                        data_field = part.inline_data.data
                        
                        if isinstance(data_field, (bytes, bytearray)):
                            result_bytes = bytes(data_field)
                        else:
                            result_bytes = base64.b64decode(data_field, validate=True)
                        
                        # Verify the image dimensions match the target aspect ratio
                        try:
                            from PIL import Image
                            from io import BytesIO
                            img = Image.open(BytesIO(result_bytes))
                            width, height = img.size
                            actual_ratio = width / height
                            
                            # Parse target ratio (e.g., "3:2" -> 1.5, "2:3" -> 0.667, "1:1" -> 1.0)
                            ratio_parts = target_ratio.split(':')
                            if len(ratio_parts) == 2:
                                target_ratio_value = float(ratio_parts[0]) / float(ratio_parts[1])
                                ratio_diff = abs(actual_ratio - target_ratio_value) / target_ratio_value
                                
                                if ratio_diff > 0.05:  # Allow 5% tolerance
                                    logger.warning(
                                        f"Gemini-generated image aspect ratio {actual_ratio:.3f} doesn't match target {target_ratio} "
                                        f"(expected ~{target_ratio_value:.3f}, diff: {ratio_diff*100:.1f}%). "
                                        f"Falling back to PIL-based resizing."
                                    )
                                    # Fallback to PIL-based resizing using original image
                                    return _resize_image_with_pil(original_image_bytes, target_ratio, original_mime_type)
                                else:
                                    logger.info(
                                        f"Successfully reformatted image to {target_ratio} "
                                        f"(actual: {actual_ratio:.3f}, target: {target_ratio_value:.3f}, "
                                        f"size: {width}x{height}, file size: {len(result_bytes)/1024:.1f} KB)"
                                    )
                            else:
                                logger.info(f"Successfully generated reformatted image (size: {len(result_bytes)/1024:.1f} KB)")
                        except Exception as img_check_error:
                            logger.warning(f"Could not verify image aspect ratio: {str(img_check_error)}. Using Gemini result.")
                        
                        return result_bytes, result_mime_type

            raise ValueError("No image data found in the response.")

        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error and we have retries left
            if _is_rate_limit_error(e) and attempt < MAX_RETRIES:
                retry_delay = _extract_retry_delay(error_str)
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES + 1}). "
                    f"Retrying in {retry_delay:.2f} seconds... Error: {error_str[:200]}"
                )
                await asyncio.sleep(retry_delay)
                # Exponential backoff for subsequent retries
                retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                continue
            
            # For non-rate-limit errors or final attempt
            if attempt == MAX_RETRIES:
                logger.error(
                    f"Error generating reformatted image after {MAX_RETRIES + 1} attempts: {error_str}",
                    exc_info=True
                )
                # Fallback to PIL-based resizing when Gemini fails completely
                logger.info(f"Falling back to PIL-based resizing for target ratio {target_ratio}")
                try:
                    return _resize_image_with_pil(original_image_bytes, target_ratio, original_mime_type)
                except Exception as pil_error:
                    logger.error(f"PIL-based resizing also failed: {str(pil_error)}", exc_info=True)
                    return None
            else:
                logger.error(f"Error generating reformatted image (attempt {attempt + 1}): {error_str}")
            break
    
    # If we get here, all attempts failed and fallback also failed
    return None