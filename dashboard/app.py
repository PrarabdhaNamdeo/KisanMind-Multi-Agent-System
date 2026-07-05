__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from datetime import datetime
from PIL import Image
import tempfile
import time

st.set_page_config(
    page_title="KisanMind",
    page_icon="🌱",
    layout="wide"
)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "kisanmind")
}

def log_to_db(phone, disease, confidence, location):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO farmer_queries
            (farmer_phone, disease, confidence, location)
            VALUES (%s, %s, %s, %s)
        """, (phone, disease, confidence, location))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        st.warning(f"Could not log to DB: {e}")

def show_agent_status(container, active_agent: int, results: dict = {}):
    agents = [
        ("🌿", "VisionAgent",    "Analyzing crop image with Gemini 2.5 Flash"),
        ("📋", "SchemeAgent",    "Searching government scheme database (RAG)"),
        ("💊", "TreatmentAgent", "Fetching treatment plan"),
        ("🏪", "SupplierAgent",  "Finding nearest dealer via MySQL"),
        ("🔊", "VoiceAgent",     "Generating Hindi voice note"),
    ]

    status_html = ""
    for i, (icon, name, desc) in enumerate(agents, 1):
        if i < active_agent:
            extra = ""
            if i == 1 and "disease" in results:
                extra = f" → <b>{results['disease']}</b> ({results.get('confidence', 0)*100:.0f}%)"
            elif i == 2 and "schemes" in results:
                extra = f" → {', '.join(results['schemes'])}"
            elif i == 3 and "treatment" in results:
                extra = f" → {results['treatment']}"
            elif i == 4 and "supplier" in results:
                extra = f" → {results['supplier']}"
            elif i == 5:
                extra = " → MP3 generated!"

            status_html += f"""
            <div style='padding:8px; margin:4px 0; border-radius:8px;
                        background:#1a3a1a; border-left:4px solid #00ff00;'>
                ✅ {icon} <b>{name}</b> — Complete{extra}
            </div>"""

        elif i == active_agent:
            status_html += f"""
            <div style='padding:8px; margin:4px 0; border-radius:8px;
                        background:#1a1a3a; border-left:4px solid #4488ff;'>
                ⚡ {icon} <b>{name}</b> — Running... <i>{desc}</i>
            </div>"""

        else:
            status_html += f"""
            <div style='padding:8px; margin:4px 0; border-radius:8px;
                        background:#2a2a2a; border-left:4px solid #555;
                        opacity:0.5;'>
                ⏳ {icon} <b>{name}</b> — Waiting
            </div>"""

    container.markdown(status_html, unsafe_allow_html=True)

st.sidebar.title("🌱 KisanMind")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", ["🌾 Farmer Demo", "📊 Admin Dashboard"])

if page == "🌾 Farmer Demo":

    st.title("🌾 KisanMind — Crop Disease Detector")
    st.markdown("Upload a crop photo to get instant disease diagnosis, treatment plan, and government scheme info.")
    st.markdown("---")

    col_upload, col_config = st.columns(2)

    with col_upload:
        st.subheader("📸 Upload Crop Photo")
        uploaded_file = st.file_uploader(
            "Choose a crop image",
            type=["jpg", "jpeg", "png"],
            help="Upload a clear photo of the affected crop leaves"
        )
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded crop photo", use_container_width=True)

    with col_config:
        st.subheader("📍 Farmer Details")

        farmer_phone = st.text_input(
            "Farmer Phone Number",
            value="+917607128504"
        )

        districts = [
            "Vidisha, Madhya Pradesh",
            "Bhopal, Madhya Pradesh",
            "Narsinghpur, Madhya Pradesh",
            "Jabalpur, Madhya Pradesh",
            "Sagar, Madhya Pradesh",
            "Indore, Madhya Pradesh",
            "Gwalior, Madhya Pradesh",
            "Ujjain, Madhya Pradesh"
        ]
        farmer_location = st.selectbox("Farmer Location", districts)

        st.markdown("---")
        st.subheader("🧪 Or Test with Known Disease")
        st.markdown("*Skip image upload — directly test with a disease name:*")

        test_disease = st.selectbox(
            "Select Disease to Test",
            [
                "-- Use uploaded image --",
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
        )

    st.markdown("---")
    run_button = st.button("🚀 Analyze Crop", type="primary", use_container_width=True)

    if run_button:

        if uploaded_file is None and test_disease == "-- Use uploaded image --":
            st.error("❌ Please either upload an image OR select a disease to test!")
            st.stop()

        st.markdown("### 🤖 AI Agents Running...")
        status_container = st.empty()
        partial_results = {}

        from agents.vision_agent import predict_disease as gemini_predict
        from agents.treatment_agent import get_treatment, format_treatment_for_voice
        from agents.supplier_agent import get_supplier_for_treatment
        from agents.voice_agent import generate_voice_note
        from rag.retriever import retrieve_schemes, format_context

        show_agent_status(status_container, 1, partial_results)

        if test_disease != "-- Use uploaded image --":

            vision_result = {"disease": test_disease, "confidence": 0.91}
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                vision_result = gemini_predict(image_path=tmp_path)
            except Exception as e:
                st.error(f"❌ Gemini Vision failed: {e}")
                os.unlink(tmp_path)
                st.stop()
            os.unlink(tmp_path)

        partial_results["disease"] = vision_result["disease"]
        partial_results["confidence"] = vision_result["confidence"]
        show_agent_status(status_container, 2, partial_results)
        time.sleep(0.5)

        query = f"{vision_result['disease']} in {farmer_location}"
        try:
            chunks = retrieve_schemes(query)
            scheme_names = list(set([c['source'] for c in chunks]))
            scheme_context = format_context(chunks)
        except Exception as e:
            scheme_names = ["pm_kisan"]
            scheme_context = ""

        partial_results["schemes"] = scheme_names
        show_agent_status(status_container, 3, partial_results)
        time.sleep(0.5)

        treatment = get_treatment(vision_result["disease"])
        voice_script = format_treatment_for_voice(treatment, vision_result["disease"])

        partial_results["treatment"] = treatment.get("disease_hindi", "")
        show_agent_status(status_container, 4, partial_results)
        time.sleep(0.5)

        supplier = get_supplier_for_treatment(treatment, farmer_location)

        partial_results["supplier"] = supplier.get("supplier_name", "N/A")
        show_agent_status(status_container, 5, partial_results)
        time.sleep(0.5)

        full_state = {
            "image_url": "",
            "farmer_phone": farmer_phone,
            "farmer_location": farmer_location,
            "disease": vision_result["disease"],
            "confidence": vision_result["confidence"],
            "schemes": scheme_names,
            "scheme_context": scheme_context,
            "treatment": treatment,
            "treatment_voice_script": voice_script,
            "supplier_details": supplier,
            "nearest_supplier": supplier.get("supplier_name"),
            "voice_note_path": None,
            "hindi_script": None,
            "error": None
        }
        voice_result = generate_voice_note(full_state)

        show_agent_status(status_container, 6, partial_results)

        result = {
            **full_state,
            "voice_note_path": voice_result.get("voice_note_path"),
            "hindi_script": voice_result.get("hindi_script"),
        }

        log_to_db(
            phone=farmer_phone,
            disease=vision_result["disease"],
            confidence=vision_result["confidence"],
            location=farmer_location
        )
        st.cache_data.clear()

        st.success("✅ Analysis Complete!")
        st.markdown("---")

        treatment = result.get("treatment") or {}
        supplier = result.get("supplier_details") or {}
        severity = treatment.get("severity", "unknown")

        if not treatment:
            st.error("❌ Could not process. Try selecting a disease from the dropdown.")
            st.stop()

        severity_color = {"high": "🔴", "medium": "🟡", "none": "🟢", "unknown": "⚪"}.get(severity, "⚪")

        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("🦠 Disease", treatment.get("disease_hindi", result.get("disease", "Unknown")))
        with r2:
            conf = result.get("confidence", 0)
            st.metric("🎯 Confidence", f"{conf*100:.0f}%")
        with r3:
            st.metric(f"{severity_color} Severity", severity.upper())
        with r4:
            schemes = result.get("schemes", [])
            st.metric("📋 Schemes Found", len(schemes))

        st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs(["💊 Treatment", "🏪 Supplier", "📋 Govt Schemes", "🎙️ Hindi Voice"])

        with tab1:
            st.subheader("Treatment Plan")
            st.markdown(f"**Disease:** {treatment.get('description', 'N/A')}")

            st.markdown("**🌿 Organic Treatment:**")
            for tip in treatment.get("organic_treatment", []):
                st.markdown(f"- {tip}")

            chem = treatment.get("chemical_treatment", {})
            if chem.get("medicine") not in ["No treatment needed", None]:
                st.markdown("**💊 Chemical Treatment:**")
                st.info(f"""
**Medicine:** {chem.get('medicine')}

**Dosage:** {chem.get('dosage')}

**Frequency:** {chem.get('frequency')}

**Stop before harvest:** {chem.get('when_to_stop')}
                """)

            st.markdown("**⚠️ Avoid:**")
            for tip in treatment.get("avoid", []):
                st.markdown(f"- {tip}")

        with tab2:
            st.subheader("Nearest Supplier")
            if supplier and supplier.get("found") and supplier.get("distance_km", 0) > 0:
                st.success(f"""
**🏪 {supplier['supplier_name']}**

📍 {supplier['address']}

📞 {supplier['phone']}

📏 {supplier['distance_km']} km away
                """)
                if supplier.get("all_nearby"):
                    st.markdown("**Other nearby suppliers:**")
                    for s in supplier["all_nearby"][1:]:
                        st.markdown(f"- {s['name']} — {s['address']} ({s['distance_km']} km)")
            else:
                st.info("No medicine needed or no supplier found nearby.")

        with tab3:
            st.subheader("Government Schemes You're Eligible For")
            scheme_details = {
                "pmfby": {
                    "name": "PM Fasal Bima Yojana",
                    "benefit": "Crop insurance coverage for disease losses",
                    "apply": "pmfby.gov.in or nearest bank"
                },
                "pm_kisan": {
                    "name": "PM-Kisan Samman Nidhi",
                    "benefit": "₹6,000/year direct income support",
                    "apply": "pmkisan.gov.in or nearest CSC center"
                },
                "kisan_credit_card": {
                    "name": "Kisan Credit Card",
                    "benefit": "Credit up to ₹3 lakh at 4% interest",
                    "apply": "Any nationalized bank"
                }
            }
            for scheme_key in result.get("schemes", []):
                details = scheme_details.get(scheme_key, {})
                if details:
                    st.success(f"""
**{details['name']}**

💰 {details['benefit']}

📝 Apply at: {details['apply']}
                    """)

        with tab4:
            st.subheader("Hindi Voice Script")
            st.text_area(
                "This is what the farmer hears:",
                value=result.get("hindi_script", ""),
                height=300
            )
            voice_path = result.get("voice_note_path")
            if voice_path and os.path.exists(voice_path):
                st.markdown("**🎵 Play Voice Note:**")
                with open(voice_path, "rb") as f:
                    st.audio(f.read(), format="audio/mp3")

else:

    @st.cache_data(ttl=30)
    def load_queries():
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            df = pd.read_sql("""
                SELECT farmer_phone, disease, confidence,
                       location, timestamp
                FROM farmer_queries
                ORDER BY timestamp DESC
            """, conn)
            conn.close()
            return df
        except:
            return pd.DataFrame({
                "farmer_phone": ["+917607128504"],
                "disease": ["Tomato_Early_blight"],
                "confidence": [0.91],
                "location": ["Vidisha, Madhya Pradesh"],
                "timestamp": [datetime.now()]
            })

    def get_disease_display_name(disease):
        mapping = {
            "Tomato_Early_blight": "Tomato Early Blight",
            "Tomato_Late_blight": "Tomato Late Blight",
            "Potato___Early_blight": "Potato Early Blight",
            "Potato___Late_blight": "Potato Late Blight",
            "Tomato_healthy": "Healthy Tomato",
            "Potato___healthy": "Healthy Potato",
            "Pepper__bell___Bacterial_spot": "Pepper Bacterial Spot",
            "Pepper__bell___healthy": "Healthy Pepper",
            "Tomato_Bacterial_spot": "Tomato Bacterial Spot",
            "Tomato_Leaf_Mold": "Tomato Leaf Mold",
            "Tomato_Septoria_leaf_spot": "Tomato Septoria Spot",
            "Tomato_Spider_mites_Two_spotted_spider_mite": "Spider Mites",
            "Tomato__Target_Spot": "Tomato Target Spot",
            "Tomato__Tomato_YellowLeaf__Curl_Virus": "Yellow Leaf Curl",
            "Tomato__Tomato_mosaic_virus": "Mosaic Virus"
        }
        return mapping.get(disease, disease)

    st.title("📊 KisanMind Admin Dashboard")
    st.markdown("Real-time crop disease monitoring for Madhya Pradesh")
    st.markdown("---")

    df = load_queries()
    df["disease_clean"] = df["disease"].apply(get_disease_display_name)
    df["district"] = df["location"].apply(
        lambda x: x.split(",")[0].strip() if isinstance(x, str) else "Unknown"
    )
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date
    today = datetime.now().date()
    df_today = df[df["date"] == today]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🌾 Queries Today", len(df_today), f"+{len(df_today)} today")
    with col2:
        st.metric("📱 Total Ever", len(df))
    with col3:
        avg = df_today["confidence"].mean() if not df_today.empty else 0
        st.metric("🎯 Avg Confidence", f"{avg*100:.1f}%")
    with col4:
        high = ["Tomato_Late_blight", "Potato___Late_blight",
                "Tomato__Tomato_YellowLeaf__Curl_Virus"]
        alerts = len(df_today[df_today["disease"].isin(high)])
        st.metric("🚨 Alerts", alerts)

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("🦠 Most Common Diseases")
        counts = df["disease_clean"].value_counts().reset_index()
        counts.columns = ["Disease", "Count"]
        fig = px.bar(counts.head(8), x="Count", y="Disease",
                     orientation="h", color="Count",
                     color_continuous_scale="RdYlGn_r")
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("📍 Queries by District")
        dist = df["district"].value_counts().reset_index()
        dist.columns = ["District", "Queries"]
        fig2 = px.pie(dist, values="Queries", names="District")
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Recent Queries")
    display = df[["timestamp", "district", "disease_clean",
                   "confidence", "farmer_phone"]].head(20).copy()
    display.columns = ["Time", "District", "Disease", "Confidence", "Phone"]
    display["Confidence"] = display["Confidence"].apply(lambda x: f"{x*100:.1f}%")
    display["Phone"] = display["Phone"].apply(
        lambda x: str(x)[:6] + "****" if len(str(x)) > 6 else x
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()