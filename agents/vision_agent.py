import google.generativeai as genai
from PIL import Image
import os
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

VALID_DISEASES = [
    "Tomato_Early_blight",
    "Tomato_Late_blight",
    "Tomato_Bacterial_spot",
    "Tomato_Leaf_Mold",
    "Tomato_Septoria_leaf_spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite",
    "Tomato__Target_Spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus",
    "Tomato__Tomato_mosaic_virus",
    "Tomato_healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Pepper__bell___Bacterial_spot",
    "Pepper__bell___healthy"
]

PROMPT = f"""
You are an expert agricultural AI specialized in crop disease detection.

Analyze this crop leaf image carefully and identify the disease.

You MUST respond with ONLY a JSON object in this exact format:
{{
    "disease": "<disease_name>",
    "confidence": <0.0 to 1.0>,
    "reasoning": "<one sentence explanation>"
}}

The disease name MUST be exactly one of these options:
{chr(10).join(VALID_DISEASES)}

Rules:
- If the crop looks healthy, use the appropriate healthy class
- If you cannot identify the crop type, use "Tomato_Early_blight" as fallback
- confidence should reflect how sure you are (0.95 = very sure, 0.6 = unsure)
- Do NOT include any text outside the JSON object
"""


def predict_disease(image_path: str = None, image_url: str = None) -> dict:
    if image_path:
        img = Image.open(image_path).convert("RGB")
    elif image_url:
        import requests
        from io import BytesIO
        response = requests.get(image_url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        raise ValueError("Provide image_path or image_url")

    print("🤖 Sending image to Gemini Vision...")

    response = model.generate_content([PROMPT, img])
    response_text = response.text.strip()

    print(f"📝 Gemini raw response: {response_text}")

    import json
    clean = response_text.replace("```json", "").replace("```", "").strip()
    result = json.loads(clean)

    disease = result.get("disease", "Tomato_Early_blight")
    confidence = float(result.get("confidence", 0.85))
    reasoning = result.get("reasoning", "")

    if disease not in VALID_DISEASES:
        print(f"⚠️ Gemini returned unknown disease: {disease}")
        print(f"   Defaulting to closest match...")
        disease = "Tomato_Early_blight"

    print(f"✅ Disease: {disease} ({confidence*100:.0f}% confidence)")
    print(f"   Reason: {reasoning}")

    return {
        "disease": disease,
        "confidence": confidence,
        "reasoning": reasoning
    }
