# 🚀 Deployment Guide

## Local Development

### 1. Clone Repository
```bash
git clone https://github.com/PrarabdhaNamdeo/KisanMind.git
cd KisanMind
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```env
GEMINI_API_KEY=your_actual_gemini_key
MYSQL_PASSWORD=your_actual_mysql_password
```

### 4. Setup MySQL Database
```bash
mysql -u root -p < database/schema.sql
```

### 5. Ingest Government Schemes
```bash
python rag/ingest.py
```

### 6. Run Application
```bash
streamlit run dashboard/app.py
```

---

## Streamlit Cloud Deployment

### 1. Push to GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Select `dashboard/app.py` as main file
4. Click "Advanced settings"

### 3. Add Secrets
In Streamlit dashboard, go to Settings → Secrets and add:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"

MYSQL_HOST = "your_remote_mysql_host"
MYSQL_USER = "your_mysql_user"
MYSQL_PASSWORD = "your_mysql_password"
MYSQL_DATABASE = "kisanmind"
```

### 4. Deploy
Click "Deploy" and wait for the app to build.

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `MYSQL_HOST` | MySQL server hostname | Yes |
| `MYSQL_USER` | MySQL username | Yes |
| `MYSQL_PASSWORD` | MySQL password | Yes |
| `MYSQL_DATABASE` | Database name (default: kisanmind) | Yes |

---

## Troubleshooting

### Gemini API Error
- Verify API key is correct
- Check API quota at [Google AI Studio](https://makersuite.google.com/)

### MySQL Connection Error
- Ensure MySQL server is running
- Verify credentials in `.env`
- Check firewall settings

### ChromaDB Not Found
- Run `python rag/ingest.py` first
- Check `data/chroma_db/` directory exists

---

## Security Notes

⚠️ **Never commit `.env` file to Git**
⚠️ **Use Streamlit Secrets for production**
⚠️ **Keep API keys private**
