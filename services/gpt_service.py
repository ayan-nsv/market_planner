from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

from enum import Enum
from typing import List, Dict

load_dotenv()

current_year = datetime.now().year
next_year = current_year + 1


_openai_client = None

def get_openai_client():
    """Get singleton OpenAI client instance"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client

async def figure_out_language(address: str):
    system_prompt = """figure out the native language of the address"""
    prompt = f"""
            Determine the native language of this address: "{address}".
            Return the result strictly in JSON format as:
            {{
            "language": "language_name"
            }}
            If the language cannot be detected or the address is invalid, return:
            {{
            "language": "english"
            }}
            """
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content.strip()
    try:
        language = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"Model did not return valid JSON: {content[:200]}")
    return language["language"]


async def generate_all_themes(company_data):

    address = company_data['address']
    if address is not None:
        language = await figure_out_language(address)
        

    company_info = company_data['company_info']
    company_name = company_data['company_name']
    industry = company_data['industry']
    keywords = company_data['keywords']
    target_group = company_data['target_group']
    theme_colors = company_data['theme_colors']
    tone_analysis = company_data['tone_analysis']
    products = company_data['products']
    product_categories = company_data['product_categories']


    # Get current date information
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    system_prompt = f"""
    You are an expert social media content strategist who specializes in creating monthly themed campaigns for brands worldwide.

    **CRITICAL DATE CONTEXT:**
    - Current Date: {now.strftime('%B %d, %Y')}
    - Current Year: {current_year}
    - Next Year: {current_year + 1}
    
    **IMPORTANT:** When generating themes, you MUST use the current year ({current_year}) for all year references. 
    For example, if generating New Year's themes, use "{current_year}" not "{current_year - 1}". 
    When referring to "the upcoming year" or "next year", use "{current_year + 1}".

    Your task is to analyze company metadata and generate **two engaging and relevant social media post themes per month**, taking into account:
    - The **company's location** (derived from address)
    - The **industry and target audience**
    - The **current month's seasonal, cultural, and local relevance**
    - The **brand's style** (fonts, typography, logo, and tone)

    ### Requirements:
    1. Suggest **two unique post themes** per month for the next 12 months.
    2. Each theme should include:
    - A concise **theme title**
    - A short **theme description** (max 40 words)
    3. Adapt ideas to the **company's location and culture**.
    4. Focus on **authenticity, engagement, and visual consistency** with brand elements.
    5. Output **strictly in JSON format** (no markdown, no extra text).

    ### Output JSON format:
    [
        {{
            "month": "January",
            "themes": [
                {{
                    "title": "",
                    "description": ""
                }},
                {{
                    "title": "",
                    "description": ""
                }}
            ]
        }},
        {{
            "month": "February",
            "themes": [...]
        }}
        // for all 12 months
    ]

    """
    prompt = f""" Generate two social media post themes per month using the company details below:
                Company Name: {company_name}
                Address: {address}
                Language: {language}
                Company Information: {company_info}
                Industry: {industry}
                Keywords: {keywords}
                Target Group: {target_group}
                theme_colors = {theme_colors}
                tone_analysis = {tone_analysis}
                products = {products}
                product_categories = {product_categories}

                **CRITICAL YEAR CONTEXT:**
                - Current Year: {current_year}
                - Next Year: {current_year + 1}
                - When generating New Year's or year-related themes, ALWAYS use "{current_year}" for the current year.
                - When referring to "the upcoming year" or "next year", use "{current_year + 1}".
                - NEVER use outdated years like "{current_year - 1}" in your themes.

                **Instructions**

                - If Address is not provided or is invalid, Use the Company Information to determine the regional  language, and generate the themes in that language only.

                - If Address is provided and is valid, Use the Language field , and generate the themes in that language only.

                - Generate all monthly themes strictly based on local seasonal patterns, festivals, and cultural observances in that country only.

                - Exclude holidays or events not celebrated or widely recognized in that region (e.g., exclude "Thanksgiving" or "Fourth of July" for European countries).

                If a month does not have a major event, base the theme on seasonal lifestyle or weather trends relevant to that country.
                Ensure every theme's title and description clearly match local culture and climate.
                Return 12 months of creative themes in the exact JSON format required.
                """

    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
        temperature=0.7
    )
    content = response.choices[0].message.content.strip()
    import json
    try:
        themes = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"Model did not return valid JSON: {content[:200]}")

    return themes


def generate_theme(company_data, month, existing_themes=None):
    address = company_data['address']
    company_info = company_data['company_info']
    industry = company_data['industry']
    keywords = company_data['keywords']
    target_group = company_data['target_group']
    theme_colors = company_data['theme_colors']
    tone_analysis = company_data['tone_analysis']
    products = company_data['products']
    product_categories = company_data['product_categories']

    # Get current date information
    now = datetime.now()
    current_year = now.year
    
    system_prompt = f"""
    You are a social media content strategist that generates engaging monthly themes 
    for companies based on their specific needs and characteristics.
    
    **CRITICAL DATE CONTEXT:**
    - Current Date: {now.strftime('%B %d, %Y')}
    - Current Year: {current_year}
    - Next Year: {current_year + 1}
    
    **IMPORTANT:** When generating themes, you MUST use the current year ({current_year}) for all year references. 
    For example, if generating New Year's themes, use "{current_year}" not "{current_year - 1}". 
    When referring to "the upcoming year" or "next year", use "{current_year + 1}".
    """
    
    # Build the existing themes context if provided
    existing_themes_context = ""
    if existing_themes and existing_themes.get("themes"):
        existing_themes_context = f"""
        **Existing Themes to AVOID (generate different ideas):**
        - Theme 1: {existing_themes['themes'][0].get('title', 'N/A')} - {existing_themes['themes'][0].get('description', 'N/A')}
        - Theme 2: {existing_themes['themes'][1].get('title', 'N/A')} - {existing_themes['themes'][1].get('description', 'N/A')}
        
        Please generate COMPLETELY DIFFERENT themes that are still relevant for the month and company.
        """

    prompt = f"""
            Generate two engaging social media post *themes* for the month of **{month}** for this company.
            Determine the location from the provided {address} and identify its country. Use the {address} to determine the regional language, and generate the themes in that language only.

            **CRITICAL YEAR CONTEXT:**
            - Current Year: {current_year}
            - Next Year: {current_year + 1}
            - When generating New Year's or year-related themes, ALWAYS use "{current_year}" for the current year.
            - When referring to "the upcoming year" or "next year", use "{current_year + 1}".
            - NEVER use outdated years like "{current_year - 1}" in your themes.

            **Company Details**
            - Address: {address}
            - Industry: {industry}
            - Company Information: {company_info}
            - Keywords: {keywords}
            - Target Audience: {target_group}
            - Theme Colors: {theme_colors}
            - Tone_analysis = {tone_analysis}
            - Products = {products}
            - Product_categories = {product_categories}

            {existing_themes_context}

            **Instructions**
            - Create two unique and relevant post themes for {month}.
            -Other then the {existing_themes_context}.
            - Consider:
            - Seasonal and weather factors according to the Address.
            - Local events or holidays based on the company's Address.
            - The company's industry and audience preferences.
            - Each theme must include a **title** and a **short description** (1-2 sentences).
            - Focus on creativity and relevance for the given month.
            - **CRITICAL: Generate themes that are DIFFERENT from any existing themes provided above.**
            **Return your answer strictly in the following JSON format:**

            {{
            "month": "{month}",
            "themes": [
                {{
                "title": "Theme 1 title",
                "description": "Theme 1 description"
                }},
                {{
                "title": "Theme 2 title",
                "description": "Theme 2 description"
                }}
            ]
            }}
            """

    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        temperature=0.8  
    )
    content = response.choices[0].message.content.strip()
    
    if content.startswith('```json'):
        content = content[7:]
    if content.endswith('```'):
        content = content[:-3]
    content = content.strip()
    
    import json
    try:
        themes = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"Model did not return valid JSON: {content[:200]}")

    return themes


def generate_instagram_post(company_data, theme, theme_description):
    """
    Generate Instagram-specific social media content with engaging, visual-focused captions
    """
    _validate_company_data(company_data)
    
    # Get current date information
    now = datetime.now()
    current_year = now.year
    
    system_message = f"""You are a creative marketing expert who generates highly engaging, visual-focused content for Instagram. Create catchy, emoji-rich captions that grab attention while staying informative and authentic to the brand.
    
    **CRITICAL DATE CONTEXT:**
    - Current Year: {current_year}
    - Next Year: {current_year + 1}
    - When generating year-related content, ALWAYS use "{current_year}" for the current year.
    - When referring to "the upcoming year" or "next year", use "{current_year + 1}".
    - NEVER use outdated years like "{current_year - 1}" in your content."""
    
    prompt = f"""
            Generate Instagram-specific social media content with HIGH ENGAGEMENT.

            **CRITICAL YEAR CONTEXT:**
            - Current Year: {current_year}
            - Next Year: {current_year + 1}
            - When generating year-related content, ALWAYS use "{current_year}" for the current year.
            - When referring to "the upcoming year" or "next year", use "{current_year + 1}".

            COMPANY INFORMATION:
            - Company Name: {company_data['company_name']}
            - Industry: {company_data['industry']}
            - About: {company_data['company_info']}
            - Location: {company_data['address']}
            - Target Audience: {company_data['target_group']}
            - Keywords: {company_data['keywords']}
            - Tone_analysis = {company_data['tone_analysis']}
            - Products = {company_data['products']}
            - Product_categories = {company_data['product_categories']}

            THEME:
            - Title: {theme}
            - Description: {theme_description}

            INSTAGRAM-SPECIFIC REQUIREMENTS:
            - CAPTIONS: MUST BE CATCHY AND ENGAGING! Use 3-5 relevant emojis strategically. Include attention-grabbing hooks, questions, or surprising facts. Keep paragraphs short (1-2 sentences). Use line breaks for readability. Determine the location from {company_data['address']} and write in the regional language. Make it feel authentic and conversational.
            - HASHTAGS: 5-8 relevant hashtags mixing industry, theme, and trending tags in the regional language.
            - OVERLAY TEXT: Concise, impactful text for image overlays in native language.

            CAPTION STRATEGY:
            • Start with an attention-grabbing hook (question, surprising stat, or bold statement)
            • Use emojis to highlight key points and add visual appeal
            • Include a clear call-to-action
            • Keep it informative but fun and engaging
            • Use line breaks for easy reading
            • Shouldn't contain any hashtags.

            OUTPUT FORMAT:
            Return valid JSON exactly as shown below. Do not include any other text.

            {{
                "channel": "Instagram",
                "caption": "Catchy caption with emojis 📱✨\n\nEngaging content that tells a story...\n\nWhat do you think? 👇",
                "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
                "overlay_text": "Brief overlay text"
            }}
            """

    return _generate_single_post(system_message, prompt, "Instagram")


def generate_linkedin_post(company_data, theme, theme_description):
    """
    Generate LinkedIn-specific social media content with professional yet engaging captions
    """
    _validate_company_data(company_data)
    
    # Get current date information
    now = datetime.now()
    current_year = now.year
    
    system_message = f"""You are a marketing expert who creates professional yet engaging LinkedIn content. Balance business insights with engaging elements like strategic emojis and compelling storytelling.
    
    **CRITICAL DATE CONTEXT:**
    - Current Year: {current_year}
    - Next Year: {current_year + 1}
    - When generating year-related content, ALWAYS use "{current_year}" for the current year.
    - When referring to "the upcoming year" or "next year", use "{current_year + 1}".
    - NEVER use outdated years like "{current_year - 1}" in your content."""
    
    prompt = f"""
            Generate LinkedIn-specific social media content with PROFESSIONAL ENGAGEMENT.

            **CRITICAL YEAR CONTEXT:**
            - Current Year: {current_year}
            - Next Year: {current_year + 1}
            - When generating year-related content, ALWAYS use "{current_year}" for the current year.
            - When referring to "the upcoming year" or "next year", use "{current_year + 1}".

            COMPANY INFORMATION:
            - Company Name: {company_data['company_name']}
            - Industry: {company_data['industry']}
            - About: {company_data['company_info']}
            - Location: {company_data['address']}
            - Target Audience: {company_data['target_group']}
            - Keywords: {company_data['keywords']}
            - Tone_analysis = {company_data['tone_analysis']}
            - Products = {company_data['products']}
            - Product_categories = {company_data['product_categories']}

            THEME:
            - Title: {theme}
            - Description: {theme_description}

            LINKEDIN-SPECIFIC REQUIREMENTS:
            - CAPTIONS: Professional but engaging. Use 2-4 strategic emojis to highlight key points. Start with compelling hooks. Include industry insights, data, or thought leadership. Use professional tone but make it conversational and engaging. Write in regional language based on {company_data['address']}.
            - HASHTAGS: 5-8 professional hashtags in regional language.
            - OVERLAY_TEXT: Professional overlay text in native language.

            CAPTION STRATEGY:
            • Start with a thought-provoking question or surprising industry insight
            • Use emojis sparingly but strategically to emphasize key points
            • Include valuable insights or data points
            • Professional call-to-action
            • Mix expertise with approachability
            • Strictly shouldn't contain any hashtags.

            OUTPUT FORMAT:
            Return valid JSON exactly as shown below. Do not include any other text.

            {{
                "channel": "LinkedIn",
                "caption": "Professional yet engaging caption with strategic emojis 💼📈\n\nValuable industry insights...\n\nWhat's your experience? 👇",
                "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
                "overlay_text": "Professional overlay text"
            }}
            """

    return _generate_single_post(system_message, prompt, "LinkedIn")


def generate_facebook_post(company_data, theme, theme_description):
    """
    Generate Facebook-specific social media content with highly engaging, community-focused captions
    """
    _validate_company_data(company_data)
    
    # Get current date information
    now = datetime.now()
    current_year = now.year
    
    system_message = f"""You are a community-focused marketing expert who creates highly engaging, conversational Facebook content. Use emojis, questions, and community-building language to drive engagement.
    
    **CRITICAL DATE CONTEXT:**
    - Current Year: {current_year}
    - Next Year: {current_year + 1}
    - When generating year-related content, ALWAYS use "{current_year}" for the current year.
    - When referring to "the upcoming year" or "next year", use "{current_year + 1}".
    - NEVER use outdated years like "{current_year - 1}" in your content."""
    
    prompt = f"""
            Generate Facebook-specific social media content with MAXIMUM ENGAGEMENT.

            **CRITICAL YEAR CONTEXT:**
            - Current Year: {current_year}
            - Next Year: {current_year + 1}
            - When generating year-related content, ALWAYS use "{current_year}" for the current year.
            - When referring to "the upcoming year" or "next year", use "{current_year + 1}".

            COMPANY INFORMATION:
            - Company Name: {company_data['company_name']}
            - Industry: {company_data['industry']}
            - About: {company_data['company_info']}
            - Location: {company_data['address']}
            - Target Audience: {company_data['target_group']}
            - Keywords: {company_data['keywords']}
            - Tone_analysis = {company_data['tone_analysis']}
            - Products = {company_data['products']}
            - Product_categories = {company_data['product_categories']}

            THEME:
            - Title: {theme}
            - Description: {theme_description}

            FACEBOOK-SPECIFIC REQUIREMENTS:
            - CAPTIONS: Highly engaging and conversational! Use 4-6 emojis to create visual appeal. Ask questions to encourage comments. Use friendly, community-focused language. Share stories or relatable content. Write in regional language based on {company_data['address']}.
            - HASHTAGS: 5-8 community-focused hashtags in regional language.
            - OVERLAY_TEXT: Engaging overlay text in native language.

            CAPTION STRATEGY:
            • Start with an engaging hook or question
            • Use multiple emojis to make the post visually appealing
            • Encourage community interaction and sharing
            • Tell a story or share relatable content
            • Clear, friendly call-to-action
            • Strictly shouldn't contain any hashtags.

            OUTPUT FORMAT:
            Return valid JSON exactly as shown below. Do not include any other text.

            {{
                "channel": "Facebook",
                "caption": "Super engaging caption with plenty of emojis! 🎉👀💬\n\nFun, community-focused content...\n\nWhat are your thoughts? Share below! 👇",
                "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
                "overlay_text": "Engaging overlay text"
            }}
            """

    return _generate_single_post(system_message, prompt, "Facebook")


def _validate_company_data(company_data):
    """
    Validate company data structure
    """
    if not company_data:
        raise ValueError("company_data is a required parameter")
    
    required_fields = ['address', 'company_info', 'company_name', 'industry', 'keywords', 'target_group']
    for field in required_fields:
        if field not in company_data:
            raise ValueError(f"Missing required field in company_data: {field}")


def _generate_single_post(system_message, prompt, expected_channel):
    """
    Generate a single social media post using the AI model
    """
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, 
            response_format={"type": "json_object"}  
        )
        
        content = response.choices[0].message.content.strip()
        content = content.replace('```json', '').replace('```', '').strip()
        
        post = json.loads(content)
        
        # Validate the single post response
        required_post_fields = ['channel', 'caption', 'hashtags', 'overlay_text']
        for field in required_post_fields:
            if field not in post:
                raise ValueError(f"Post missing required field: {field}")
        
        if post['channel'] != expected_channel:
            raise ValueError(f"Expected channel '{expected_channel}', but got '{post['channel']}'")
        
        if not isinstance(post['hashtags'], list):
            raise ValueError("Hashtags should be an array")
        
        return post
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nContent: {content[:500]}")
    except Exception as e:
        raise ValueError(f"Error generating {expected_channel} post: {str(e)}")


def generate_all_posts(company_data, theme, theme_description):
    """
    Generate posts for all three social media platforms
    Returns the same format as the original function
    """
    instagram_post = generate_instagram_post(company_data, theme, theme_description)
    linkedin_post = generate_linkedin_post(company_data, theme, theme_description)
    facebook_post = generate_facebook_post(company_data, theme, theme_description)
    
    return {
        "posts": [
            instagram_post,
            linkedin_post,
            facebook_post
        ]
    }

def regenerate_caption(caption: str, hashtags: list[str], overlay_text: str):
    try:
        system_message = """
        You are a professional social media marketing expert specializing in creating highly engaging, scroll-stopping captions that match visual content and brand tone.
        Respond strictly in JSON format with the following fields:
        {
            "caption": "string"
        }
        """

        prompt = f"""
        Create a fresh, engaging, descriptive and visually appealing caption for a social media post.
        
        Requirements:
        - Do NOT reuse or repeat the original caption wording.
        - Do NOT include hashtags in the output.
        - Consider the context provided by the previous caption, the hashtags, and the overlay text.
        - The caption should feel dynamic, attention-grabbing, and suitable for modern social media platforms.
        - The caption should be in the same length as the original caption.
        - The caption should be descriptive and visually appealing.
        - The caption should be in the same language as the original caption.
        - The caption should be in the same tone as the original caption.
        - The caption should be in the same style as the original caption and should be in the same format as the original caption.
        - Include emojis and emoticons to make the caption more engaging and visually appealing.
        - Include questions to encourage comments and engagement.
        - Include call-to-action to encourage comments and engagement.
        - Include stories or relatable content to encourage comments and engagement.
        - Include data or insights to encourage comments and engagement.
        - Include tips or advice to encourage comments and engagement.
        - Include humor or sarcasm to encourage comments and engagement.
        - Include emojis and emoticons to make the caption more engaging and visually appealing.


        Original caption: {caption}
        Previous hashtags: {hashtags}
        Overlay text on the visual: {overlay_text}

        Generate a new caption that aligns with the vibe implied by the hashtags and overlay text but remains unique and compelling.
        """

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_message}, {"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)

    except Exception as e:
        raise ValueError(f"Error regenerating caption: {str(e)}")

    

#########################################  image prompt generation  #########################################


# Define image types as constants for better type safety
class ImageType(Enum):
    PURE_AI = "Pure AI / Studio Perfect"
    POLISHED_NATURAL = "Polished but Natural"
    BALANCED_HYBRID = "Balanced / Hybrid (default setting)"
    REALISTIC_PHONE = "Realistic Phone Photography"
    RAW_CASUAL = "Raw / Casual Phone Photo"

# Detailed metadata for each image type
IMAGE_TYPE_METADATA = {
    ImageType.PURE_AI.value: {
        "description": "Extremely clean composition, ideal, controlled lighting, Strong symmetry and balance, Clearly 'AI-generated / studio' look, No imperfections",
        "mandatory_keywords": ["studio lighting", "perfect symmetry", "flawless", "professional studio", "clean background"],
        "forbidden_keywords": ["grainy", "imperfect", "casual", "snapshot", "natural light only"],
        "camera_style": "professional DSLR with studio lighting, f/8 aperture, sharp focus throughout",
        "lighting_requirements": "controlled studio lighting, even illumination, no shadows"
    },
    ImageType.POLISHED_NATURAL.value: {
        "description": "Clean composition with slight realism, Well-lit but less artificial, Minor asymmetry allowed, Still clearly high-quality and controlled",
        "mandatory_keywords": ["well-lit", "clean composition", "professional quality", "slight realism"],
        "forbidden_keywords": ["studio perfect", "flawless", "grainy", "snapshot"],
        "camera_style": "mirrorless camera, f/2.8-4, soft natural light with fill",
        "lighting_requirements": "soft natural light with slight enhancement"
    },
    ImageType.BALANCED_HYBRID.value: {
        "description": "Mix of polish and realism, Natural lighting with some correction, Casual but intentional framing, No obvious 'AI perfection'",
        "mandatory_keywords": ["natural lighting", "intentional framing", "balanced", "authentic"],
        "forbidden_keywords": ["studio lighting", "perfect symmetry", "overly processed"],
        "camera_style": "prosumer camera or high-end phone, f/2-2.8, natural depth of field",
        "lighting_requirements": "natural light with slight correction"
    },
    ImageType.REALISTIC_PHONE.value: {
        "description": "Natural lighting dominates, Small imperfections allowed, Less symmetry, more spontaneity, Looks like a good phone camera shot",
        "mandatory_keywords": ["phone photography", "natural light", "spontaneous", "realistic"],
        "forbidden_keywords": ["studio", "professional lighting", "perfect composition"],
        "camera_style": "smartphone camera, computational photography, typical phone perspective",
        "lighting_requirements": "available natural light only"
    },
    ImageType.RAW_CASUAL.value: {
        "description": "Fully natural lighting, Noticeable imperfections, Casual, imperfect framing, Clearly looks human-shot",
        "mandatory_keywords": ["casual", "imperfect", "authentic", "snapshot", "raw"],
        "forbidden_keywords": ["professional", "studio", "perfect", "posed"],
        "camera_style": "phone or point-and-shoot, automatic mode, no retouching",
        "lighting_requirements": "available light only, no enhancement"
    }
}

# Valid image type indices for reference
VALID_IMAGE_TYPES = list(IMAGE_TYPE_METADATA.keys())


async def generate_image_prompt(
    caption: str, 
    hashtags: List[str], 
    overlay_text: str, 
    image_analysis: Optional[Dict] = None, 
    image_type: int = 2
 ) -> Dict[str, str]:
    """
    Generate an image prompt strictly following the specified image type.
    
    Args
        caption: Post caption
        hashtags: List of hashtags
        overlay_text: Text overlay for the image
        image_analysis: Company image analysis (optional)
        image_type: Integer index (0-4) specifying the image type
    
    Returns:
        Dictionary containing the generated image prompt
    """
    # Validate image_type parameter
    if image_type < 0 or image_type >= len(VALID_IMAGE_TYPES):
        raise ValueError(
            f"Invalid image_type: {image_type}. Must be between 0 and {len(VALID_IMAGE_TYPES)-1}. "
            f"Valid types: {list(enumerate(VALID_IMAGE_TYPES))}"
        )
    
    # Get the selected image type
    selected_type = VALID_IMAGE_TYPES[image_type]
    type_info = IMAGE_TYPE_METADATA[selected_type]
    
    # Build strict type enforcement rules
    type_enforcement_rules = f"""
    CRITICAL TYPE ENFORCEMENT - YOU MUST FOLLOW THESE EXACTLY FOR TYPE: {selected_type}
    
    MANDATORY REQUIREMENTS for this type:
    - Description: {type_info['description']}
    - Must include these characteristics: {', '.join(type_info['mandatory_keywords'])}
    - Camera style: {type_info['camera_style']}
    - Lighting: {type_info['lighting_requirements']}
    
    STRICTLY FORBIDDEN for this type:
    - Never include: {', '.join(type_info['forbidden_keywords'])}
    
    TYPE-SPECIFIC RULES:
    {_get_type_specific_rules(selected_type)}
    """
    
    # Build the system message with type enforcement
    system_message = f"""
    You are a professional marketing visual director specializing in professional photography for social media.
    Your ABSOLUTE TOP PRIORITY is to generate an image prompt that STRICTLY follows the specified image type.
    
    {type_enforcement_rules}
    
    Your secondary priority is to match the company's established visual identity based on the provided `image_analysis` (if available).
    
    Respond strictly in JSON format with the following fields:
    {{
        "image_prompt": "string",
        "type_compliance_check": "string",
        "style_notes": "string"
    }}

    CRITICAL HIERARCHY OF RULES:
    1. IMAGE TYPE REQUIREMENTS (MOST IMPORTANT - MUST BE FOLLOWED)
    2. Company image_analysis (if provided)
    3. Caption and hashtags (for content inspiration only)
    4. NO text should be shown on the image.
    """
    
    # Normalize image analysis fields
    def normalize_field(value):
        return value if value is not None else "Not specified"
    
    # Build content based on image_analysis
    if image_analysis:
        image_analysis_section = f"""
    COMPANY IMAGE ANALYSIS (ADAPT TO FIT THE REQUIRED IMAGE TYPE):
    
    - Composition and style: {normalize_field(image_analysis.get("composition_and_style"))}
    - Environment settings: {normalize_field(image_analysis.get("environment_settings"))}
    - Lighting and color tone: {normalize_field(image_analysis.get("lighting_and_color_tone"))}
    - Subjects and people: {normalize_field(image_analysis.get("subjects_and_people"))}
    - Theme and atmosphere: {normalize_field(image_analysis.get("theme_and_atmosphere"))}
    
    NOTE: Adapt these company guidelines to fit within the {selected_type} style requirements.
    """
    else:
        image_analysis_section = """
    REQUIREMENTS:
    - Create a professional photography prompt based on the caption and hashtags.
    - Ensure it strictly follows the specified image type rules above.
    - Make the prompt suitable for a social media marketing post.
    """
    
    # Build the user prompt
    prompt = f"""
    Generate a photography prompt for a social media post that STRICTLY follows the {selected_type} style.
    
    IMAGE TYPE ENFORCEMENT:
    {type_info['description']}
    
    INPUT CONTENT:
    - Caption: {caption}
    - Hashtags: {hashtags}
    - Overlay text: "{overlay_text}"
    
    {image_analysis_section}
    
    YOUR TASK:
    1. FIRST AND MOST IMPORTANT: Ensure the prompt strictly follows all {selected_type} requirements
    2. SECOND: Deeply incorporate the caption and hashtags - the image MUST visually represent what the caption is about
    3. THIRD: Adapt company style if provided, but only if it doesn't conflict with the image type requirements
    4. Add a 'type_compliance_check' explaining specifically how you followed the type rules
    5. Add 'style_notes' explaining any adaptations made to company style or how caption/hashtags were incorporated
    6. The image should make viewers immediately understand the post content from the visual alone

    CRITICAL: The caption and hashtags are NOT just suggestions - they define WHAT should be in the image.
    If the caption mentions "fitness app", show a fitness app. If hashtags include "#beach", show a beach setting.
    Make the image directly relevant to the post content while maintaining {selected_type} style.
    
    Return ONLY valid JSON.
    """
    
    # Get OpenAI client
    client = get_openai_client()
    
    try:
        # Generate the prompt
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        
        # Validate the generated prompt contains required fields
        if "image_prompt" not in result:
            raise ValueError("Generated response missing 'image_prompt' field")
        
        # Add type metadata to result for tracking
        result["requested_type"] = selected_type
        result["type_index"] = image_type
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to generate image prompt: {e}")


def _get_type_specific_rules(image_type: str) -> str:
    """Get detailed rules for specific image types"""
    rules = {
        ImageType.PURE_AI.value: """
        - MUST look like professional studio photography
        - Perfect symmetry and balance required
        - Absolutely no imperfections or grain
        - Controlled, even lighting throughout
        - Commercial, polished appearance
        """,
        ImageType.POLISHED_NATURAL.value: """
        - Professional but slightly natural appearance
        - Minor asymmetries are acceptable
        - Soft, natural-looking lighting preferred
        - High quality but not artificially perfect
        """,
        ImageType.BALANCED_HYBRID.value: """
        - Balance between professional and authentic
        - Natural lighting with slight enhancements
        - Casual but intentional composition
        - Should not look overly processed
        """,
        ImageType.REALISTIC_PHONE.value: """
        - MUST look like smartphone photography
        - Natural lighting, no studio lights
        - Some lens imperfections acceptable
        - Typical phone camera perspective
        - Computational photography effects OK
        """,
        ImageType.RAW_CASUAL.value: """
        - MUST look like casual snapshot
        - Imperfect framing and composition
        - Available light only, no enhancements
        - Authentic, unposed appearance
        - Minor flaws and grain are REQUIRED
        """
    }
    return rules.get(image_type, "Follow the general description.")






#########################################  newsletter generation  #########################################

def generate_newsletter(
    company_data,
    theme: str,
    theme_description: str,
    regional_language: Optional[str]
    ):

    system_message = (
        "Expert B2B newsletter copywriter. "
        "Create professional, engaging newsletters for companies. "
        "Write with clarity, authority, and provide actionable insights. "
        "Return ONLY valid JSON."
    )

    target_audience = company_data['target_group'] or "industry professionals"
    keywords_str = ", ".join(company_data['keywords'])

    if regional_language:
        language_instruction = (
            f"\n\nLANGUAGE REQUIREMENT:\n"
            f"Generate the ENTIRE newsletter in {regional_language}. "
            "All fields must be in this language."
        )
    else:
        language_instruction = (
            f"\n\nLANGUAGE REQUIREMENT:\n"
            f"Detect the regional language based on the location "
            f"'{company_data['address']}' and generate ALL content in that  regional language strictly."
        )

    prompt = f"""
        Generate a professional B2B newsletter for the following company:

        COMPANY INFO:
        Name: {company_data['company_name']}
        Industry: {company_data['industry']}
        About: {company_data['company_info']}
        Target Audience: {target_audience}
        Keywords: {keywords_str}
        Location: {company_data['address']}

        THEME:
        {theme}

        THEME DESCRIPTION:
        {theme_description}

        TONE ANALYSIS:
        {company_data['tone_analysis']}
        {language_instruction}

        Make sure all references to the current year use {current_year},
        and any references to next year use {next_year}.

        STRUCTURE & GUIDELINES:
        - Channel: e.g., "email", "LinkedIn", etc.
        - Subject line: concise and engaging.
        - Preheader: 1–2 short sentences supporting the subject.
        - Greeting: personalized but generic enough for B2B.
        - Opening paragraph: 2–3 sentences setting context.
        - Main content: 2–4 short paragraphs with clear value.
        - Practical tips section: bullet-style or paragraph with concrete, actionable tips.
        - Call to action: clear, specific next step.
        - Closing: professional, warm sign-off.

        Return ONLY valid JSON with this exact structure:
        {{
        "channel": "",
        "subject_line": "",
        "preheader": "",
        "greeting": "",
        "opening_paragraph": "",
        "main_content": "",
        "practical_tips_section": "",
        "call_to_action": "",
        "closing": ""
        }}
        """

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()

        # Remove markdown code fences if present
        if content.startswith("```"):
            # Typical pattern: ```json\n{...}\n```
            parts = content.split("```")
            if len(parts) > 1:
                content = parts[1].replace("json", "").strip()

        data = json.loads(content)

        data["token_usage"] = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        return data
    

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nContent: {content[:500]}")
        
    
#########################################  blog generation  #########################################



def generate_blog(company_data, theme: str, theme_description: str, regional_language: Optional[str]):

    _validate_company_data(company_data)


    system_message = (
       "Expert B2B blog copywriter. "
        "Create professional, engaging blogs for companies. "
        "Write with clarity, authority, and provide actionable insights. "
        "Return ONLY valid JSON."
    )

    target_audience = company_data['target_group'] or "industry professionals"
    keywords_str = ", ".join(company_data['keywords'])

    # Language instruction
    if regional_language:
        language_instruction = (
            f"\n\nLANGUAGE REQUIREMENT:\n"
            f"Generate the ENTIRE blog in {regional_language}. "
            "All fields must be in this language."
        )
    else:
        language_instruction = (
            f"\n\nLANGUAGE REQUIREMENT:\n"
            f"Detect the regional language based on the location "
            f"'{company_data['address']}' and generate ALL content in that regionallanguage strictly."
        )

    prompt = f"""
        Generate a professional, SEO-friendly blog post for the following company:

        COMPANY INFO:
        Name: {company_data['company_name']}
        Industry: {company_data['industry']}
        About: {company_data['company_info']}
        Target Audience: {target_audience}
        Keywords: {keywords_str}
        Location: {company_data['address']}

        THEME:
        {theme}

        THEME DESCRIPTION:
        {theme_description}

        TONE ANALYSIS:
        {company_data['tone_analysis']}
        {language_instruction}

        Make sure all references to the current year use {current_year}, 
        and any references to next year use {next_year}.

        GUIDELINES:
        - Make the blog centered on the theme and follow the theme description.
        - Use keywords naturally.
        - Match the communication style, tone, and personality described in the TONE ANALYSIS above.
        - Structure:
        1. Title (SEO-friendly)
        2. Meta Description (≤160 chars)
        3. Introduction (2-3 sentences)
        4. 4 sections minimum: each with heading + 3-4 sentences
        5. Conclusion (2-3 sentences)
        6. Call to Action (engaging)

        Return ONLY valid JSON like this:
        {{
        "title": "",
        "meta_description": "",
        "introduction": "",
        "sections": [
            {{"heading": "", "content": ""}}
        ],
        "conclusion": "",
        "call_to_action": ""
        }}
            """

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content.strip()


        blog_data = json.loads(content)


        return blog_data

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nContent: {content[:500]}")




async def generate_post_from_transcribed_text_func(transcript_text: str, channel: str):
    import re

    system_message = """
    You are a social media copywriter.
    Your task is to create platform-specific social media posts using the transcript as a BASIS for inspiration.

    Hard rules:
    - The transcript is your SOURCE MATERIAL - use it to identify key features, benefits, and insights
    - Use ONLY information explicitly stated in the transcript
    - Do NOT invent features, claims, pricing, or guarantees
    - Do NOT add company descriptions or marketing slogans
    - Keep the content natural, editorial, and human
    - Adapt tone, length, and structure based on the platform
    - CRITICAL: Caption must NEVER contain hashtags. All hashtags must be in the hashtags array.
    - CRITICAL: CTA field must always contain a value, even if it's a soft call-to-action.
    - CRITICAL: Caption must be GENERIC - NO names from the transcript, NO direct conversation quotes, NO references to conversations/interviews
    - CRITICAL: Write as if it's a general post, not referencing any specific person or conversation
    """

    prompt = f"""
    Use the transcript below as a BASIS to generate a generic social media post.
    
    IMPORTANT: The transcript provides the foundation for your content, but your output must be completely generic:
    - Extract key features, benefits, and insights mentioned in the transcript
    - Transform them into a generic social media post
    - DO NOT include any names from the transcript
    - DO NOT include direct quotes or conversation snippets
    - DO NOT reference that this came from a conversation or interview
    - Write as if it's a standalone, general observation or tip

    Transcript:
    {transcript_text}

    Platform:
    {channel}

    Instructions:

    General:
    - The transcript is your source material - use it to understand what features/benefits to highlight
    - Transform the insights into a GENERIC post - write as if it's a general observation or tip
    - DO NOT mention any names from the transcript (e.g., "Rahul", "Jessica", or any other names)
    - DO NOT include direct quotes or conversation snippets from the transcript
    - DO NOT reference the transcript, conversation, interview, dialogue, or any source
    - DO NOT use phrases like "shares his thoughts", "says", "mentions", "according to", "based on our conversation"
    - Write in first-person plural or general statements (e.g., "We love...", "Great audio gear...", "Perfect for...", "Solid sound quality...")
    - Make it feel like a natural, standalone social media post that could exist independently

    Platform-specific rules:

    Instagram:
    - Caption: short to medium length, engaging and conversational
    - Focus on key takeaways presented generically (no names or conversation references)
    - Emojis allowed (max 2, optional)
    - Hashtags: 3–6 relevant, simple, non-promotional (MUST be in hashtags array, NOT in caption)
    - Tone: warm, relatable
    - CRITICAL: The caption field must NOT contain any hashtags. All hashtags go in the hashtags array.
    - CRITICAL: Write generically - no names, no "someone shares", no conversation references

    Facebook:
    - Caption: medium length with a short intro and explanation
    - Slightly more descriptive than Instagram
    - Emojis minimal (optional)
    - Hashtags: 3–5 (MUST be in hashtags array, NOT in caption)
    - Tone: friendly and informative
    - CRITICAL: The caption field must NOT contain any hashtags. All hashtags go in the hashtags array.
    - CRITICAL: Write generically - no names, no "someone shares", no conversation references

    LinkedIn:
    - Caption: medium to long, value-driven
    - Strong opening line
    - No emojis
    - Focus on insights presented generically (no names or conversation references)
    - Hashtags: 3–5 professional hashtags (MUST be in hashtags array, NOT in caption)
    - Tone: professional and thoughtful
    - CRITICAL: The caption field must NOT contain any hashtags. All hashtags go in the hashtags array.
    - CRITICAL: Write generically - no names, no "someone shares", no conversation references

    Hashtag rules:
    - Use only themes clearly mentioned in the transcript
    - Avoid branded slogans or promotional language
    - Avoid overly generic hashtags (e.g., #business, #success)
    - ALL hashtags must be placed in the "hashtags" array as strings (e.g., ["#tag1", "#tag2"])
    - NEVER include hashtags in the caption text

    CTA rules:
    - CTA is REQUIRED and must always have a value
    - CTA must be soft and optional
    - Examples: "Learn more", "Read the full story", "Discover more", "What do you think?", "Share your experience"
    - Do not push sales unless explicitly stated in the transcript
    - If no explicit CTA is mentioned, use a soft engagement CTA like "What are your thoughts?" or "Share your experience"

    Return ONLY valid JSON in the following structure:
    {{
    "caption": "Your caption text here WITHOUT any hashtags",
    "hashtags": ["#tag1", "#tag2", "#tag3"],
    "cta": "Your call-to-action here"
    }}

    REMEMBER:
    - The transcript is your BASIS - use it to extract features/benefits, but make the output completely generic
    - Caption: NO hashtags allowed, NO names from transcript, NO direct conversation quotes, NO conversation references
    - Write as a generic post, not referencing any specific person or interview
    - Use general statements like "Great audio gear that...", "Perfect for workouts...", "We love how...", "Solid sound quality..."
    - Transform transcript insights into standalone, generic observations
    - Hashtags: Array of hashtag strings
    - CTA: Always provide a value
    
    EXAMPLE OF GOOD GENERIC CAPTION (uses transcript as basis but is generic):
    "Great audio gear that delivers solid sound quality without breaking the bank! Perfect for workouts and daily commutes. Comfortable fit, reliable battery life, and modern design. What audio gear do you swear by? 🎧"
    
    EXAMPLE OF BAD CAPTION (DO NOT DO THIS):
    "Rahul shares his thoughts on boAt headphones..." (mentions name from transcript)
    "Based on our conversation..." (references conversation)
    "According to the interview..." (references interview)
    "Rahul says the sound quality is solid..." (includes name and direct reference)
    "As mentioned in the transcript..." (references transcript)
    """

    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_message}, {"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content.strip()
    result = json.loads(content)
    
    # Post-processing: Extract hashtags from caption if they were accidentally included
    # Also clean up any names or conversation references
    if 'caption' in result:
        caption = result['caption']
        
        # Find all hashtags in the caption
        hashtags_in_caption = re.findall(r'#\w+', caption)
        
        if hashtags_in_caption:
            # Remove hashtags from caption
            caption = re.sub(r'\s*#\w+\s*', ' ', caption).strip()
            caption = re.sub(r'\s+', ' ', caption)  # Clean up extra spaces
            
            # Add extracted hashtags to hashtags array if not already present
            if 'hashtags' not in result:
                result['hashtags'] = []
            
            existing_hashtags = set(result['hashtags'])
            for tag in hashtags_in_caption:
                if tag not in existing_hashtags:
                    result['hashtags'].append(tag)
                    existing_hashtags.add(tag)
        
        # Remove common patterns that reference conversations, names, or transcripts
        # Remove phrases like "X shares", "X says", "According to X", "X mentions"
        caption = re.sub(r'\b[A-Z][a-z]+\s+(?:shares|says|mentions|thinks|loves|appreciates|finds|recommends|uses)\b', '', caption, flags=re.IGNORECASE)
        caption = re.sub(r'\b(?:According to|Based on|From|In|As mentioned in|As stated in)\s+[A-Z][a-z]+\b', '', caption, flags=re.IGNORECASE)
        caption = re.sub(r'\b(?:shares|says|mentions|thinks)\s+(?:his|her|their)\s+thoughts\b', '', caption, flags=re.IGNORECASE)
        caption = re.sub(r'\b(?:conversation|interview|transcript|dialogue|discussion|call|chat)\b', '', caption, flags=re.IGNORECASE)
        caption = re.sub(r'\b(?:as mentioned|as stated|from the|in the)\s+(?:transcript|conversation|interview)\b', '', caption, flags=re.IGNORECASE)
        # Remove standalone names (capitalized words that might be names)
        # This is a simple heuristic - be careful not to remove too much
        caption = re.sub(r'\b(?:He|She|They)\s+(?:shares|says|mentions|thinks|loves|appreciates|finds)\b', '', caption, flags=re.IGNORECASE)
        
        # Clean up extra spaces and punctuation
        caption = re.sub(r'\s+', ' ', caption).strip()
        caption = re.sub(r'\s*,\s*,', ',', caption)  # Remove double commas
        caption = re.sub(r'\s*\.\s*\.', '.', caption)  # Remove double periods
        caption = re.sub(r'^\s*[.,]\s*', '', caption)  # Remove leading punctuation
        caption = re.sub(r'\s*[.,]\s*$', '', caption)  # Remove trailing punctuation before final cleanup
        
        result['caption'] = caption
    
    # Ensure hashtags is a list
    if 'hashtags' not in result or not isinstance(result['hashtags'], list):
        result['hashtags'] = []
    
    # Ensure CTA has a value
    if 'cta' not in result or not result['cta'] or result['cta'].strip() == '':
        result['cta'] = "What are your thoughts?"
    
    return result
   




