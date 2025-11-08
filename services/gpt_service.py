from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()


_openai_client = None

def get_openai_client():
    """Get singleton OpenAI client instance"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def generate_all_themes(company_data):
    address = company_data['address']
    company_info = company_data['company_info']
    company_name = company_data['company_name']
    industry = company_data['industry']
    keywords = company_data['keywords']
    target_group = company_data['target_group']
    theme_colors = company_data['theme_colors']
    tone_analysis = company_data['tone_analysis']
    products = company_data['products']
    product_categories = company_data['product_categories']


    system_prompt = """
    You are an expert social media content strategist who specializes in creating monthly themed campaigns for brands worldwide.

    Your task is to analyze company metadata and generate **two engaging and relevant social media post themes per month**, taking into account:
    - The **company’s location** (derived from address)
    - The **industry and target audience**
    - The **current month’s seasonal, cultural, and local relevance**
    - The **brand’s style** (fonts, typography, logo, and tone)

    ### Requirements:
    1. Suggest **two unique post themes** per month for the next 12 months.
    2. Each theme should include:
    - A concise **theme title**
    - A short **theme description** (max 40 words)
    3. Adapt ideas to the **company’s location and culture**.
    4. Focus on **authenticity, engagement, and visual consistency** with brand elements.
    5. Output **strictly in JSON format** (no markdown, no extra text).

    ### Output JSON format:
    [
        {
            "month": "January",
            "themes": [
                {
                    "title": "",
                    "description": ""
                },
                {
                    "title": "",
                    "description": ""
                }
            ]
        },
        {
            "month": "February",
            "themes": [...]
        }
        // for all 12 months
    ]

    """
    prompt = f""" Generate two social media post themes per month using the company details below:
                Company Name: {company_name}
                Address: {address}
                Company Information: {company_info}
                Industry: {industry}
                Keywords: {keywords}
                Target Group: {target_group}
                theme_colors = {theme_colors}
                tone_analysis = {tone_analysis}
                products = {products}
                product_categories = {product_categories}

                Determine the location from the provided {address} and identify its country. Use the {address} to determine the regional language.
                Generate all monthly themes strictly based on local seasonal patterns, festivals, and cultural observances in that country only.
                Exclude holidays or events not celebrated or widely recognized in that region (e.g., exclude “Thanksgiving” or “Fourth of July” for European countries).
                If a month does not have a major event, base the theme on seasonal lifestyle or weather trends relevant to that country.
                Ensure every theme’s title and description clearly match local culture and climate.
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

    system_prompt = """
    You are a social media content strategist that generates engaging monthly themes 
    for companies based on their specific needs and characteristics.
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
    Generate Instagram-specific social media content
    """
    _validate_company_data(company_data)
    
    system_message = """You are a marketing expert who generates detailed image prompts, captions, hashtags, and overlay text for Instagram. Create visual-focused, creative content that engages younger audiences and aligns with the company's brand."""
    
    prompt = f"""
            Generate Instagram-specific social media content.

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
            - Visual-focused, creative, engaging for younger audiences
            - IMAGE PROMPTS: Must be detailed, specific for AI image generation. Generated images STRICTLY should NOT contain any overlay text, logos, or watermarks. Focus on visual elements only.
            - CAPTIONS: Should be engaging, platform-appropriate, and reflect the company's voice. Should not contain any emoji or figures. should be of the native language of the company location: Write natural, conversational captions in the company's native language that match the brand personality. No emojis or special characters allowed.
            - HASHTAGS: 5-8 relevant hashtags, mixing industry, theme, and Instagram-specific tags, should be of the native language of the company location: Create a balanced set of hashtags in the native language, combining broad industry terms with specific content themes.
            - OVERLAY TEXT: Concise, impactful text for image overlays (added during post design), should be of the native language of the company location: Write short, powerful phrases in native language that can be added as graphic elements during design.

            OUTPUT FORMAT:
            Return valid JSON exactly as shown below. Do not include any other text.

            {{
                "channel": "Instagram",
                "image_prompt": "Detailed visual description without text",
                "caption": "Engaging Instagram caption",
                "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
                "overlay_text": "Brief overlay text"
            }}
            """

    return _generate_single_post(system_message, prompt, "Instagram")


def generate_linkedin_post(company_data, theme, theme_description):
    """
    Generate LinkedIn-specific social media content
    """
    _validate_company_data(company_data)
    
    system_message = """You are a marketing expert who generates detailed image prompts, captions, hashtags, and overlay text for LinkedIn. Create professional, business-oriented content with industry insights that aligns with the company's brand."""
    
    prompt = f"""
            Generate LinkedIn-specific social media content.

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
            - Professional, business-oriented, industry insights
            - IMAGE PROMPTS: Must be detailed, specific for AI image generation. Generated images STRICTLY should NOT contain any overlay text, logos, or watermarks. Focus on professional visual elements.
            - CAPTIONS: Should be professional, platform-appropriate, and reflect the company's voice. Should not contain any emoji or figures.
            - HASHTAGS: 5-8 relevant hashtags, mixing industry, theme, and LinkedIn-specific professional tags.
            - OVERLAY TEXT: Concise, impactful text for image overlays (added during post design).

            OUTPUT FORMAT:
            Return valid JSON exactly as shown below. Do not include any other text.

            {{
                "channel": "LinkedIn",
                "image_prompt": "Professional image description without text",
                "caption": "Professional LinkedIn caption",
                "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
                "overlay_text": "Brief overlay text"
            }}
            """

    return _generate_single_post(system_message, prompt, "LinkedIn")


def generate_facebook_post(company_data, theme, theme_description):
    """
    Generate Facebook-specific social media content
    """
    _validate_company_data(company_data)
    
    system_message = """You are a marketing expert who generates detailed image prompts, captions, hashtags, and overlay text for Facebook. Create community-focused, conversational content with broader appeal that aligns with the company's brand."""
    
    prompt = f"""
            Generate Facebook-specific social media content.

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
            - Community-focused, conversational, broader appeal
            - IMAGE PROMPTS: Must be detailed, specific for AI image generation. Generated images STRICTLY should NOT contain any overlay text, logos, or watermarks. Focus on community-oriented visual elements.
            - CAPTIONS: Should be conversational, platform-appropriate, and reflect the company's voice. Should not contain any emoji or figures.
            - HASHTAGS: 5-8 relevant hashtags, mixing industry, theme, and Facebook-specific community tags.
            - OVERLAY TEXT: Concise, impactful text for image overlays (added during post design).

            OUTPUT FORMAT:
            Return valid JSON exactly as shown below. Do not include any other text.

            {{
                "channel": "Facebook",
                "image_prompt": "Community-focused image description without text",
                "caption": "Conversational Facebook caption",
                "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
                "overlay_text": "Brief overlay text"
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
        required_post_fields = ['channel', 'image_prompt', 'caption', 'hashtags', 'overlay_text']
        for field in required_post_fields:
            if field not in post:
                raise ValueError(f"Post missing required field: {field}")
        
        if post['channel'] != expected_channel:
            raise ValueError(f"Expected channel '{expected_channel}', but got '{post['channel']}'")
        
        if not isinstance(post['hashtags'], list):
            raise ValueError("Hashtags should be an array")
        
        # Validate image prompt doesn't contain text elements
        image_prompt_lower = post['image_prompt'].lower()
        if any(text_indicator in image_prompt_lower for text_indicator in ['text:', 'words:', 'logo', 'watermark', 'lettering', 'typography']):
            raise ValueError("Image prompt should not contain text elements")
        
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




