import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gtts import gTTS
from datetime import datetime

VOICE_OUTPUT_DIR = "output/voice_notes"
os.makedirs(VOICE_OUTPUT_DIR, exist_ok=True)


def build_hindi_script(state: dict) -> str:
    disease = state.get("disease", "अज्ञात बीमारी")
    confidence = state.get("confidence", 0)
    location = state.get("farmer_location", "आपके क्षेत्र")
    treatment = state.get("treatment", {})
    schemes = state.get("schemes", [])
    supplier = state.get("supplier_details", {})

    script = "नमस्ते किसान भाई। किसानमाइंड से आपके लिए जरूरी जानकारी।\n\n"

    disease_hindi = treatment.get("disease_hindi", disease)
    confidence_percent = int(confidence * 100)

    if treatment.get("severity") == "none":
        script += f"खुशखबरी! आपकी फसल की जांच हुई। "
        script += f"आपकी फसल स्वस्थ है। कोई बीमारी नहीं मिली।\n\n"
    else:
        script += f"आपकी फसल की जांच में {disease_hindi} पाई गई है। "
        script += f"हमें {confidence_percent} प्रतिशत विश्वास है।\n\n"

    severity = treatment.get("severity", "unknown")
    if severity == "high":
        script += "⚠️ यह बीमारी बहुत गंभीर है। तुरंत कदम उठाएं।\n\n"
    elif severity == "medium":
        script += "यह बीमारी मध्यम स्तर की है। जल्दी इलाज करें।\n\n"

    if treatment.get("severity") != "none":
        organic = treatment.get("organic_treatment", [])
        chemical = treatment.get("chemical_treatment", {})

        if organic:
            script += f"जैविक उपाय: {organic[0]}\n\n"

        if chemical.get("medicine") not in ["No treatment needed",
                                             "Consult local agronomist before applying chemicals",
                                             "No direct chemical cure for virus"]:
            script += f"दवाई: {chemical.get('medicine', '')}। "
            script += f"मात्रा: {chemical.get('dosage', '')} पानी में मिलाकर छिड़काव करें।\n\n"

        avoid = treatment.get("avoid", [])
        if avoid:
            script += f"सावधानी: {avoid[0]}\n\n"

    if supplier and supplier.get("found") and supplier.get("distance_km", 0) > 0:
        script += f"नजदीकी दवाई की दुकान: {supplier['supplier_name']}। "
        script += f"दूरी: {supplier['distance_km']} किलोमीटर। "
        script += f"फोन: {supplier['phone']}।\n\n"

    if schemes:
        scheme_map = {
            "pm_kisan": "पीएम किसान योजना",
            "pmfby": "प्रधानमंत्री फसल बीमा योजना",
            "kisan_credit_card": "किसान क्रेडिट कार्ड"
        }
        scheme_names = [scheme_map.get(s, s) for s in schemes]
        script += f"आप इन सरकारी योजनाओं के लिए पात्र हैं: "
        script += f"{', '.join(scheme_names)}। "
        script += f"अपने नजदीकी CSC केंद्र पर जाकर आवेदन करें।\n\n"

    script += "किसानमाइंड हमेशा आपके साथ है। धन्यवाद।"

    return script.strip()


def text_to_speech(text: str, farmer_phone: str) -> str:
    phone_clean = farmer_phone.replace("+", "").replace(" ", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reply_{phone_clean}_{timestamp}.mp3"
    output_path = os.path.join(VOICE_OUTPUT_DIR, filename)

    print(f"🎙️  Converting text to Hindi speech...")
    print(f"   Script length: {len(text)} characters")

    tts = gTTS(text=text, lang='hi', slow=False)
    tts.save(output_path)

    print(f"✅ Voice note saved: {output_path}")
    return output_path


def generate_voice_note(state: dict) -> dict:
    try:
        hindi_script = build_hindi_script(state)

        print(f"\n🎙️  Hindi Script Preview:")
        print("─" * 40)
        print(hindi_script)
        print("─" * 40)

        farmer_phone = state.get("farmer_phone", "unknown")
        voice_path = text_to_speech(hindi_script, farmer_phone)

        return {
            "voice_note_path": voice_path,
            "hindi_script": hindi_script,
            "status": "success"
        }

    except Exception as e:
        print(f"❌ VoiceAgent error: {e}")
        return {
            "voice_note_path": None,
            "hindi_script": "",
            "status": f"failed: {str(e)}"
        }


def play_voice_note(voice_path: str):
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(voice_path)
        pygame.mixer.music.play()

        print("▶️  Playing voice note... (press Ctrl+C to stop)")
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    except Exception as e:
        print(f"Could not play audio: {e}")
        print(f"Open this file manually to listen: {voice_path}")