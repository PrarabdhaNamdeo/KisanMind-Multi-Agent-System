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
│   └── retriever.py        # Semantic search
├── ml/                  # Machine learning
│   └── disease_classifier.py  # RandomForest backup model
├── dashboard/           # Streamlit UI
│   └── app.py              # Main web interface
├── data/
│   ├── PlantVillage/       # Training dataset (15 disease classes)
│   ├── chroma_db/          # Vector store
│   └── schemes/            # Government scheme PDFs
└── output/              # Generated voice notes
```

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/PrarabdhaNamdeo/KisanMind.git
cd KisanMind
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup MySQL Database
```sql
CREATE DATABASE kisanmind;

CREATE TABLE suppliers (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    address VARCHAR(200),
    phone VARCHAR(20),
    district VARCHAR(50),
    distance_km FLOAT
);

CREATE TABLE supplier_inventory (
    id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_id INT,
    medicine_name VARCHAR(100),
    in_stock BOOLEAN,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE farmer_queries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_phone VARCHAR(20),
    disease VARCHAR(100),
    confidence FLOAT,
    location VARCHAR(100),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Configure API Keys

Update in `agents/vision_agent.py`:
```python
GEMINI_API_KEY = "your_gemini_api_key_here"
```

Update MySQL credentials in `agents/supplier_agent.py` and `dashboard/app.py`:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "kisanmind"
}
```

### 5. Ingest Government Schemes
```bash
python rag/ingest.py
```

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

## 📄 License

MIT License - See LICENSE file for details

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