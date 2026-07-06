# 🌱 KisanMind - AI-Powered Crop Disease Detection System

An intelligent agricultural assistant built with LangGraph that helps farmers identify crop diseases, get treatment recommendations, find nearby suppliers, and access government schemes - all in Hindi voice output.

## 🎯 Problem Statement

Indian farmers face crop losses due to late disease detection and lack of accessible agricultural guidance. KisanMind solves this by providing instant AI-powered diagnosis through a simple Streamlit interface.

## ✨ Features

- **🔍 Disease Detection**: Gemini 2.5 Flash Vision API identifies 15+ crop diseases
- **💊 Treatment Plans**: Structured organic and chemical treatment recommendations
- **🏪 Supplier Finder**: MySQL-powered nearest dealer lookup with real-time inventory
- **📋 Government Schemes**: RAG-based eligibility check for PMFBY, PM-Kisan, KCC
- **🎙️ Hindi Voice Output**: gTTS converts guidance to MP3 for low-literacy farmers
- **📊 Admin Dashboard**: Real-time disease monitoring and analytics

## 🏗️ Architecture

```
Multi-Agent LangGraph Pipeline:
VisionAgent → SchemeAgent → TreatmentAgent → SupplierAgent → VoiceAgent
```

### Agent Breakdown

| Agent | Technology | Purpose |
|-------|-----------|---------|
| **VisionAgent** | Gemini 2.5 Flash | Crop disease classification from images |
| **SchemeAgent** | ChromaDB + RAG | Semantic search over government scheme PDFs |
| **TreatmentAgent** | Python Dict | Deterministic treatment plan lookup (zero hallucination) |
| **SupplierAgent** | MySQL | Geo-spatial dealer finder with stock availability |
| **VoiceAgent** | gTTS | Hindi text-to-speech generation |

## 🛠️ Tech Stack

**AI/ML**
- Google Gemini 2.5 Flash (Vision)
- LangChain + LangGraph (Multi-agent orchestration)
- ChromaDB (Vector store)
- HuggingFace Embeddings (`all-MiniLM-L6-v2`)
- Scikit-learn RandomForest (Backup classifier)

**Backend**
- Python 3.10+
- MySQL (Supplier database)
- Streamlit (Web UI)

**Libraries**
- `google-generativeai`, `langchain`, `langgraph`
- `chromadb`, `sentence-transformers`
- `gtts` (Text-to-speech), `pillow` (Image processing)
- `plotly` (Dashboard visualizations)

## 📁 Project Structure

```
KisanMind/
├── agents/              # Multi-agent system
│   ├── vision_agent.py      # Gemini Vision classifier
│   ├── treatment_agent.py   # Treatment knowledge base
│   ├── supplier_agent.py    # MySQL dealer finder
│   └── voice_agent.py       # Hindi TTS generator
├── graph/               # LangGraph orchestrator
│   └── orchestrator.py      # State machine coordination
├── rag/                 # Government schemes RAG
│   ├── ingest.py           # PDF → ChromaDB ingestion
│   └── retriever.py        # Semantic search (auto-builds vector store on first run)
├── dashboard/           # Streamlit UI
│   └── app.py              # Main web interface
├── data/
│   ├── chroma_db/          # Vector store (auto-generated, not committed)
│   └── schemes/            # Government scheme PDFs
├── setup_db.py          # One-time script: creates MySQL tables + seed data
├── add_more_suppliers.py # Adds suppliers for additional districts
└── output/              # Generated voice notes
```

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/PrarabdhaNamdeo/KisanMind-Multi-Agent-System.git
cd KisanMind-Multi-Agent-System
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Copy the example environment file and fill in your own values — the app loads all secrets from `.env` via `python-dotenv`, so nothing needs to be hardcoded in the source files:

```bash
cp .env.example .env
```

Then edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password_here
MYSQL_DATABASE=kisanmind
# Set to true only for local MySQL without SSL. Leave false for cloud-hosted MySQL (e.g. Aiven).
MYSQL_SSL_DISABLED=false
```

`.env` is already listed in `.gitignore`, so your credentials won't be committed.

> **Using a cloud MySQL provider (e.g. Aiven, PlanetScale, Railway)?** Use the host, port, user, password, and database name from your provider's dashboard instead of the localhost defaults above. Cloud MySQL providers typically require SSL and a custom port rather than the default 3306.

### 4. Setup MySQL Database

Instead of running SQL manually, two scripts handle this for you — they read your `.env` credentials and connect using the same `mysql-connector-python` dependency already in `requirements.txt`:

```bash
python setup_db.py
```

This creates the `suppliers`, `supplier_inventory`, and `farmer_queries` tables (if they don't already exist) and seeds sample suppliers/inventory for Bhopal and Indore so the app returns real results out of the box. Safe to run more than once — it skips seeding if data already exists.

To add sample suppliers for the remaining districts (Vidisha, Narsinghpur, Jabalpur, Sagar, Gwalior, Ujjain):

```bash
python add_more_suppliers.py
```

This is also safe to re-run — it checks by supplier name before inserting, so it won't create duplicates.

> Both scripts contain no credentials themselves — they read everything from your `.env` file at runtime, so they're safe to keep in version control.

### 5. Ingest Government Schemes (optional)
```bash
python rag/ingest.py
```
This is optional — `rag/retriever.py` automatically builds the vector store on first use if it doesn't already exist. Running this manually just lets you pre-build it and confirm the PDFs ingest correctly before starting the app.

### 6. Run Application
```bash
streamlit run dashboard/app.py
```

Visit `http://localhost:8501`

## 💡 Usage

### Farmer Demo Mode
1. Upload crop image or select disease from dropdown
2. Enter farmer location (district, state)
3. Click "Analyze Crop"
4. View results in tabs:
   - Treatment plan (organic + chemical)
   - Nearest supplier with distance
   - Eligible government schemes
   - Hindi voice script + MP3 playback

### Admin Dashboard
- Real-time disease monitoring across districts
- Disease frequency charts
- Farmer query analytics
- Confidence score tracking

## 🎓 Supported Diseases (15 Classes)

**Tomato** (9): Early Blight, Late Blight, Bacterial Spot, Leaf Mold, Septoria Leaf Spot, Spider Mites, Target Spot, Yellow Leaf Curl Virus, Mosaic Virus, Healthy

**Potato** (3): Early Blight, Late Blight, Healthy

**Pepper** (2): Bacterial Spot, Healthy

## 🔬 How It Works

### 1. Disease Detection
- Gemini Vision receives crop image
- Returns JSON with disease name (from 15 valid classes), confidence score, reasoning
- Falls back to `Tomato_Early_blight` if unknown disease

### 2. Treatment Lookup
- O(1) dictionary lookup in `TREATMENT_DB`
- Returns structured plan: organic methods, chemical treatment, precautions
- Zero hallucination (deterministic data structure)

### 3. Supplier Search
```sql
SELECT * FROM suppliers s 
JOIN supplier_inventory si ON s.supplier_id = si.supplier_id
WHERE s.district = ? AND si.medicine_name LIKE ? AND si.in_stock = TRUE
ORDER BY s.distance_km ASC
```

### 4. Scheme Retrieval
- Query embedded using `all-MiniLM-L6-v2`
- ChromaDB returns top-3 semantically similar PDF chunks
- Schemes: PMFBY, PM-Kisan, Kisan Credit Card

### 5. Voice Generation
- Compiles results into narrative Hindi script
- gTTS converts to MP3 (saved in `output/voice_notes/`)

## 📊 Dashboard Features

- **Farmer Demo**: Interactive disease detection UI
- **Agent Status**: Live progress tracking with color-coded indicators
- **Admin Analytics**: Disease heatmaps, district-wise queries
- **Historical Data**: Query logs with anonymized phone numbers

## 🎯 Key Design Decisions

**Why Gemini over RandomForest?**
- RandomForest on 64×64 flattened pixels loses spatial structure
- Gemini handles real-world photo variations (lighting, backgrounds)
- Better generalization without local GPU training

**Why deterministic treatment DB over LLM?**
- Agricultural advice must be accurate (no hallucination risk)
- O(1) lookup faster than API calls
- Guaranteed correct dosages and precautions

**Why ChromaDB for schemes?**
- Government PDFs change frequently
- Semantic search finds relevant schemes better than keyword matching
- No fine-tuning needed

**Why MySQL for suppliers?**
- Structured relational data (suppliers + inventory)
- Complex queries (JOIN + spatial filtering + stock check)
- ACID guarantees for transactional integrity

## 🚧 Future Enhancements

- [ ] Multilingual support (Tamil, Telugu, Bengali)
- [ ] Mobile app (React Native)
- [ ] Offline mode with edge deployment
- [ ] Integration with state agricultural departments
- [ ] Farmer community forum
- [ ] Weather-based disease prediction
- [ ] Drone integration for large farms

## 👨‍💻 Author

**Prarabdha Namdeo**
- GitHub: [@PrarabdhaNamdeo](https://github.com/PrarabdhaNamdeo)
- LinkedIn: [prarabdha-namdeo](https://linkedin.com/in/prarabdha-namdeo-79177b370)
- Email: prarabdha910@gmail.com

## 🙏 Acknowledgments

- PlantVillage Dataset for training data
- Google Gemini for vision API access
- LangChain community for multi-agent frameworks
- Government of India for agricultural scheme documentation

---
