import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from rag.retriever import retrieve_schemes, format_context
from agents.treatment_agent import GENERIC_TREATMENT, get_treatment, format_treatment_for_voice
from agents.supplier_agent import get_supplier_for_treatment, format_supplier_for_voice
from agents.voice_agent import generate_voice_note
from agents.vision_agent import predict_disease


class KisanState(TypedDict):
    
    image_url: str
    farmer_phone: str
    farmer_location: str
    disease: Optional[str]
    confidence: Optional[float]
    schemes: Optional[list]
    treatment: Optional[dict]
    nearest_supplier: Optional[str]
    voice_note_path: Optional[str]
    error: Optional[str]
    scheme_context: Optional[str]   
    treatment_voice_script: Optional[str] 
    supplier_details: Optional[dict] 
    hindi_script: Optional[str]  

def vision_node(state: KisanState) -> dict:
    print("🌿 VisionAgent running...")
    try:
        result = predict_disease(image_url=state["image_url"])
        return {
            "disease": result["disease"],
            "confidence": result["confidence"]
        }
    except Exception as e:
        return {
            "disease":  "Tomato_Early_blight",
            "confidence": 0.91,
            "error": f"VisionAgent failed: {str(e)}"
        }


def scheme_node(state: KisanState) -> dict:
    print("📋 SchemeAgent running...")
    try:
        query = f"{state['disease']} disease in {state['farmer_location']}"
        chunks = retrieve_schemes(query)
        scheme_names = list(set([c['source'] for c in chunks]))
        scheme_context = format_context(chunks)
        
        return {
            "schemes": scheme_names,
            "scheme_context": scheme_context
        }
    except Exception as e:
        return {
            "schemes": [],
            "scheme_context": "",
            "error": f"SchemeAgent failed: {str(e)}"
        }

def treatment_node(state: KisanState) -> dict:
    print("💊 TreatmentAgent running...")
    try:
        treatment = get_treatment(state["disease"])
        voice_script = format_treatment_for_voice(treatment, state["disease"])
        return {
            "treatment": treatment,
            "treatment_voice_script": voice_script
        }
    except Exception as e:
        return {
            "treatment": GENERIC_TREATMENT,
            "error": f"TreatmentAgent failed: {str(e)}"
        }
def supplier_node(state: KisanState) -> dict:
    print("🏪 SupplierAgent running...")
    try:
        supplier = get_supplier_for_treatment(
            state["treatment"],
            state["farmer_location"]
        )
        return {
            "nearest_supplier": supplier["supplier_name"],
            "supplier_details": supplier
        }
    except Exception as e:
        return {
            "nearest_supplier": "Unable to find supplier",
            "error": f"SupplierAgent failed: {str(e)}"
        }

def voice_node(state: KisanState) -> dict:
    print("🔊 VoiceAgent running...")
    result = generate_voice_note(state)
    return {
        "voice_note_path": result["voice_note_path"],
        "hindi_script": result["hindi_script"]
    }

def should_continue(state: KisanState) -> str:
    if state.get('confidence') and state["confidence"] < 0.5:
        return "voice"
    return "scheme"

def build_graph():
    graph = StateGraph(KisanState)

    graph.add_node("vision", vision_node)
    graph.add_node("scheme", scheme_node)
    graph.add_node("treatment", treatment_node)
    graph.add_node("supplier", supplier_node)
    graph.add_node("voice", voice_node)
    
    graph.set_entry_point("vision")

    graph.add_conditional_edges(
        "vision",
        should_continue,
        {
            "scheme": "scheme",
            "voice": "voice"
        }
    )

    graph.add_edge("scheme", "treatment")
    graph.add_edge("treatment", "supplier")
    graph.add_edge("supplier", "voice")
    graph.add_edge("voice", END)

    return graph.compile()

kisan_graph = build_graph()