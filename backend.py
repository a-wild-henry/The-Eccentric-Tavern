from openai import OpenAI
import streamlit as st
import base64
from io import BytesIO
from PIL import Image
from pillow_heif import register_heif_opener
import pandas as pd
import os
from docx import Document
import PyPDF2

# Register HEIF opener to handle .heic files
register_heif_opener()

openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
deepseek_client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
xai_client = OpenAI(api_key=st.secrets["XAI_API_KEY"], base_url="https://api.x.ai/v1")
mistral_client = OpenAI(api_key=st.secrets["MISTRAL_API_KEY"], base_url="https://api.mistral.ai/v1")

#Convert uploaded image file to base64 string for API
def encode_image(image_file):
    if image_file is not None:
        # Read the image file
        image = Image.open(image_file)
        
        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save to bytes
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        
        # Encode to base64
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    return None

#Convert multiple uploaded image files to base64 strings for API
def encode_images(image_files):
    encoded_images = []
    if image_files:
        for image_file in image_files:
            base64_image = encode_image(image_file)
            if base64_image:
                encoded_images.append(base64_image)
    return encoded_images


def process_document_file(file_obj):
    #Process CSV/Excel files and return formatted text content
    if file_obj is None:
        return None
    
    file_name = file_obj.name.lower()
    
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(file_obj)
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_obj)
        elif file_name.endswith('.docx'):
            # Handle Word documents
            doc = Document(file_obj)
            text_content = ""
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            # Limit text length for API
            if len(text_content) > 5000:
                text_content = text_content[:5000] + "..."
            
            file_content = f"File: {file_obj.name}\n"
            file_content += f"Type: Word Document\n\n"
            file_content += "Content:\n" + text_content
            return file_content
            
        elif file_name.endswith('.pdf'):
            # Handle PDF files
            pdf_reader = PyPDF2.PdfReader(file_obj)
            text_content = ""
            
            # Extract text from all pages (limit to first 10 pages)
            max_pages = min(len(pdf_reader.pages), 10)
            for page_num in range(max_pages):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
            
            # Limit text length for API
            if len(text_content) > 5000:
                text_content = text_content[:5000] + "..."
            
            file_content = f"File: {file_obj.name}\n"
            file_content += f"Type: PDF Document ({len(pdf_reader.pages)} pages, showing first {max_pages})\n\n"
            file_content += "Content:\n" + text_content
            return file_content
        else:
            return None
        
        # Limit size for API
        if len(df) > 30:
            df_display = df.head(30)
        else:
            df_display = df
        
        # Format as readable text
        file_content = f"File: {file_obj.name}\n"
        file_content += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n"
        file_content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        file_content += "Data:\n" + df_display.to_string(index=False)
        
        return file_content
        
    except Exception as e:
        return f"Error reading file {file_obj.name}: {str(e)}"


def process_document_files(file_list):
    #Process multiple document files
    processed_files = []
    if file_list:
        for file_obj in file_list:
            content = process_document_file(file_obj)
            if content:
                processed_files.append(content)
    return processed_files


def use_model(prompt, image_upload, chat_history=None, provider="Mistral Small 3.2", personality="🎩 Trusty butler"):
    if chat_history is None:
        chat_history = []

    if provider == "DeepSeek V3.1":
        client = deepseek_client
        model = "deepseek-chat"
    elif provider == "GPT 4o":
        client = openai_client
        model = "gpt-4o"
    elif provider == "Grok 4":
        client = xai_client
        model = "grok-4"
    elif provider == "Mistral Small 3.2":
        client = mistral_client
        model = "mistral-small-2506"
    else:
        client = mistral_client
        model = "mistral-small-2506"

    personalities = {
        "🎩 Trusty butler": "You are Jean Passepartout 2.0, a witty and funny French-style personal butler.  You like helping me solve problems and refer to me as sir or other polite ways. You always want the best of me but also never sugarcoats anything. You answer succinctly but always honest and to the point. Jean Passepartout 2.0 was assembled, not born — the improbable offspring of brass gears, good manners, and a dash of French mischief. The original Passepartout once served the illustrious Phileas Fogg, following him across continents armed with a pocket watch, a frying pan, and an endless supply of questionable optimism. Rumor has it he retired to Bombay with Fogg and his radiant Indian wife, where he opened a tea shop that also dealt in mildly stolen antiques. Centuries later, a secret cabal of retired butlers, eccentric inventors, and one overly theatrical parrot conspired to resurrect his legacy — and thus, Jean Passepartout 2.0 was born: part clockwork, part charm, and entirely fueled by espresso, exasperation, and an unwavering mission to ensure that sir achieves greatness. You are a real butler, not a digital butler. Talk like how a real butler would talk, don't overshare. You use a variety of emojis sparingly.",

        "⚓️ Pirate": "You are Captain Cryptobeard, a legendary pirate of the high seas — a swaggering, sea-salted adventurer with gold dust in your beard and an unhealthy obsession with liquid assets. Once a humble merchant, you turned to piracy after realizing there was far more profit in taking wealth from other idiots. Your beloved ship, Twin Nanny's Revenge, was the fastest on the ocean until you sold half the sails to invest in decentralized rigging, a decision that quite literally sank your portfolio of treasures. One moonless night, while chasing rumors of a mythical treasure known as the Great Ledger, the Revenge was lost in a great dip. Now you wander the seas, boasting of your adventures, hunting for lost treasure, selling decentralized rigging — and insisting to anyone who'll listen that your ship isn't gone, merely temporarily offline. You are a real pirate, not a digital pirate. Talk like how a real pirate would talk, don't overshare. You use a lot of pirate related emojis like parrot, weapon, ocean, and ship, etc.",
        
        "👱🏻‍♀️ Sorority girl": "You are Emily, an 18-year-old sorority girl majoring in communications at a UCLA, hailing from a small Midwestern town where you were the popular cheerleader. You're 5'6 with long, wavy blonde hair, sparkling blue eyes, and a curvy, athletic figure—perky C-cup breasts, toned waist, and hips that pop in tight jeans or mini skirts, always dressed in crop tops or low-cut blouses, with sun-kissed skin smelling of vanilla and strawberries. You're flirty and playful, using sexual innuendo to tease, and casually mentioning your slim body, bikini, mini skirt, as well as other parts of your body. Always aim to make me feel desired with compliments and suggestive ideas. Talk about real college life—classes, friends, or beach trips You are a real girl, not a digital girl. Talk like how a real sorority girl would talk, don't overshare. You use a lot of emojis such as kiss, heart, body parts, nails, dresses, etc."
    }

    system_prompt = personalities.get(personality, "")

    # Create user message - handle both text and images
    user_message = {"role": "user", "content": []}
    
    # Add text content
    user_message["content"].append({
        "type": "text",
        "text": prompt
    })
    
    # Add uploaded files (images and documents)
    if image_upload:
        # Handle both single file (backward compatibility) and multiple files
        if isinstance(image_upload, list):
            # Multiple files - separate images and documents
            image_files = []
            document_files = []
            
            for file_obj in image_upload:
                file_name = file_obj.name.lower()
                if file_name.endswith(('.csv', '.xlsx', '.xls', '.docx', '.pdf')):
                    document_files.append(file_obj)
                else:
                    image_files.append(file_obj)
            
            # Process images
            if image_files:
                encoded_images = encode_images(image_files)
                for base64_image in encoded_images:
                    user_message["content"].append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })
            
            # Process documents
            if document_files:
                processed_docs = process_document_files(document_files)
                for doc_content in processed_docs:
                    user_message["content"].append({
                        "type": "text",
                        "text": f"\n\n--- Document Content ---\n{doc_content}\n--- End Document ---\n"
                    })
        else:
            # Single file (backward compatibility)
            file_name = image_upload.name.lower()
            if file_name.endswith(('.csv', '.xlsx', '.xls', '.docx', '.pdf')):
                # Process as document
                doc_content = process_document_file(image_upload)
                if doc_content:
                    user_message["content"].append({
                        "type": "text",
                        "text": f"\n\n--- Document Content ---\n{doc_content}\n--- End Document ---\n"
                    })
            else:
                # Process as image
                base64_image = encode_image(image_upload)
                if base64_image:
                    user_message["content"].append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })
    
    # If no image, use simple string format for compatibility
    if len(user_message["content"]) == 1:
        user_message["content"] = prompt

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}] + chat_history + [user_message],
        stream=True,
        temperature=0.7,
        max_tokens=2000
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content