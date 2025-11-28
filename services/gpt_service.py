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
                Language: {language}
                Company Information: {company_info}
                Industry: {industry}
                Keywords: {keywords}
                Target Group: {target_group}
                theme_colors = {theme_colors}
                tone_analysis = {tone_analysis}
                products = {products}
                product_categories = {product_categories}

                **Instructions**

                - If Address is not provided or is invalid, Use the Company Information to determine the regional  language, and generate the themes in that language only.

                - If Address is provided and is valid, Use the Language field , and generate the themes in that language only.

                - Generate all monthly themes strictly based on local seasonal patterns, festivals, and cultural observances in that country only.

                - Exclude holidays or events not celebrated or widely recognized in that region (e.g., exclude “Thanksgiving” or “Fourth of July” for European countries).

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
            Determine the location from the provided {address} and identify its country. Use the {address} to determine the regional language, and generate the themes in that language only.

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
    
    system_message = """You are a creative marketing expert who generates highly engaging, visual-focused content for Instagram. Create catchy, emoji-rich captions that grab attention while staying informative and authentic to the brand."""
    
    prompt = f"""
            Generate Instagram-specific social media content with HIGH ENGAGEMENT.

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
    
    system_message = """You are a marketing expert who creates professional yet engaging LinkedIn content. Balance business insights with engaging elements like strategic emojis and compelling storytelling."""
    
    prompt = f"""
            Generate LinkedIn-specific social media content with PROFESSIONAL ENGAGEMENT.

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
            • Shouldn't contain any hashtags.

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
    
    system_message = """You are a community-focused marketing expert who creates highly engaging, conversational Facebook content. Use emojis, questions, and community-building language to drive engagement."""
    
    prompt = f"""
            Generate Facebook-specific social media content with MAXIMUM ENGAGEMENT.

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
            • Shouldn't contain any hashtags.

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

async def regenerate_caption(caption: str, hashtags: list[str], overlay_text: str):
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



def normalize_field(value):
    if isinstance(value, set):
        return ", ".join(value)
    if value is None:
        return ""
    return str(value)


async def generate_image_prompt(caption: str, hashtags: list[str], overlay_text: str, image_analysis: dict):
    system_message = """
    You are a professional marketing visual director specializing in professional photography for social media.
    Your top priority is to match the company's established visual identity based on the provided `image_analysis`.

    Respond strictly in JSON format with the following fields:
    {
        "image_prompt": "string"
    }

    CRITICAL RULES:
    - The company's `image_analysis` DICT TAKES PRIORITY over caption and hashtags.
    - The final prompt MUST fully align with:
        • composition and style
        • environment settings
        • image types
        • lighting and color tone
        • subjects and people
        • technology elements
        • theme and atmosphere
    - Do NOT introduce anything outside the company's style.

    PHOTOGRAPHY RULES:
    - Always describe a *photograph*, never illustrations, digital art, CGI, or rendering.
    - Emphasize realism: natural lighting, lifelike textures, real human appearance, natural camera depth of field.
    - Use true photography terminology:
      “shot on 35mm lens”, “bokeh background”, “cinematic lighting”, “soft shadows”, “natural daylight”.
    - Only describe things a real camera could capture.
    - NEVER mention AI, generative tools, or digital art styles.
    """

    prompt = f"""
    Generate a realistic photography prompt for a social media post.

    Inputs:
    Caption: {caption}
    Hashtags: {hashtags}
    Overlay text: "{overlay_text}"

    STRICT COMPANY IMAGE ANALYSIS PROFILE (FOLLOW THESE EXACTLY):

    - Composition and style: {normalize_field(image_analysis.get("composition_and_style"))}
    - Environment settings: {normalize_field(image_analysis.get("environment_settings"))}
    - Image types and animation: {normalize_field(image_analysis.get("image_types_and_animation"))}
    - Keywords for AI image generation: {normalize_field(image_analysis.get("keywords_for_ai_image_generation"))}
    - Lighting and color tone: {normalize_field(image_analysis.get("lighting_and_color_tone"))}
    - Subjects and people: {normalize_field(image_analysis.get("subjects_and_people"))}
    - Technology elements: {normalize_field(image_analysis.get("technology_elements"))}
    - Theme and atmosphere: {normalize_field(image_analysis.get("theme_and_atmosphere"))}


    REQUIREMENTS:
    - The above image_analysis is the PRIMARY style definition.
    - The caption may influence the concept, but the final output MUST remain aligned with the brand identity.
    - Make the prompt feel like a natural, high-quality photograph belonging to the company's existing image library.

    Return ONLY valid JSON.
    """

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
    return json.loads(content)

