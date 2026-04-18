# 🛡️ AutoShield — AI Car Insurance System v2.0

> ML-powered car insurance claim prediction & fraud detection.
> XGBoost numeric model + AlexNet image model, served via FastAPI, visualised in Streamlit.

---

## 📁 Project Structure

```
autoshield/
│
├── backend/                    # FastAPI API server
│   ├── __init__.py
│   ├── main.py                 # Route definitions
│   ├── schemas.py              # Pydantic request/response models
│   └── model_utils.py          # Model loading & prediction logic
│
├── frontend/
│   └── app.py                  # Streamlit UI (calls backend API)
│
├── models/                     # ← place your .pkl and .pth files here
│   ├── car_claim_numeric_model.pkl
│   └── best_image_model.pth    (optional)
│
├── data/
│   └── train.csv               # ← place your training CSV here
│
├── .streamlit/
│   └── config.toml             # Dark theme config
│
├── train_model.py              # Standalone model training script
├── start_dev.sh                # One-command local dev launcher
├── requirements.txt            # All dependencies (local dev)
├── requirements-backend.txt    # Backend only (Render / Railway)
├── requirements-frontend.txt   # Frontend only (Streamlit Cloud)
├── Procfile                    # Render / Heroku process definition
├── render.yaml                 # Render deployment spec
├── runtime.txt                 # Python version pin
└── .env.example                # Environment variable template
```

---

## ⚡ Quick Start (Local)

### 1. Clone & install

```bash
git clone https://github.com/your-username/autoshield.git
cd autoshield
pip install -r requirements.txt
```

### 2. Add your files

```
models/car_claim_numeric_model.pkl   ← your trained XGBoost pipeline
models/best_image_model.pth          ← AlexNet weights (optional)
data/train.csv                       ← original training CSV
```

### 3. (Re)train the model (optional)

```bash
python train_model.py
# → saves models/car_claim_numeric_model.pkl
```

### 4. Start both servers

```bash
bash start_dev.sh
```

Or start them individually:

```bash
# Terminal 1 — Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
BACKEND_URL=http://localhost:8000 streamlit run frontend/app.py
```

| Service      | URL                         |
|--------------|-----------------------------|
| Streamlit UI | http://localhost:8501        |
| FastAPI API  | http://localhost:8000        |
| Swagger docs | http://localhost:8000/docs   |
| ReDoc        | http://localhost:8000/redoc  |

---

## 🌐 API Reference

### `GET /health`
Returns model load status.

```json
{
  "status": "ok",
  "numeric_model_loaded": true,
  "image_model_loaded": false
}
```

---

### `POST /predict/numeric`
Predict claim probability from policyholder details.

**Request body (JSON)**

```json
{
  "age_of_policyholder": 35,
  "age_of_car": 3,
  "fuel_type": "Petrol",
  "airbags": 4,
  "policy_tenure": 0.6,
  "ncap_rating": 3
}
```

**Response**

```json
{
  "claim_probability": 0.187,
  "approval_probability": 0.813,
  "risk_level": "Low Risk",
  "approval_likelihood": "High",
  "decision": "Auto Approve",
  "explanation": "Your profile looks safe. Claim is likely to be approved quickly."
}
```

---

### `POST /predict/image`
Detect fraud from a car damage image.

```bash
curl -X POST http://localhost:8000/predict/image \
  -F "file=@damage_photo.jpg"
```

**Response**

```json
{
  "label": "Normal",
  "confidence": 0.912
}
```

---

### `POST /predict/combined`
Multipart form — numeric fields + optional image.

```bash
curl -X POST http://localhost:8000/predict/combined \
  -F "age_of_policyholder=35" \
  -F "age_of_car=3" \
  -F "fuel_type=Petrol" \
  -F "airbags=4" \
  -F "policy_tenure=0.6" \
  -F "ncap_rating=3" \
  -F "file=@damage_photo.jpg"
```

---

## 🚀 Deployment

### Option A — Backend on Render + Frontend on Streamlit Cloud *(recommended)*

**Backend → Render**

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service**.
3. Select your repo, set:
   - **Build command**: `pip install -r requirements-backend.txt`
   - **Start command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `PYTHON_VERSION = 3.11.9`
5. Note your service URL, e.g. `https://autoshield-api.onrender.com`

Or use the included `render.yaml` for automatic configuration.

**Frontend → Streamlit Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io).
2. Connect your GitHub repo.
3. Set **Main file path** → `frontend/app.py`
4. Set **Requirements file** → `requirements-frontend.txt`
5. Under **Advanced → Secrets**, add:
   ```toml
   BACKEND_URL = "https://autoshield-api.onrender.com"
   ```

---

### Option B — Single server (Render)

Use the `Procfile`:

```
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Run the Streamlit frontend separately or serve it as a second Render service.

---

### Option C — Railway

```bash
railway init
railway up
```

Set `BACKEND_URL` as a Railway environment variable.

---

### Option D — Docker (Fly.io / any VPS)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements-backend.txt
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t autoshield .
docker run -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  autoshield
```

---

## ⚙️ Environment Variables

| Variable      | Default                   | Description                           |
|---------------|---------------------------|---------------------------------------|
| `BACKEND_URL` | `http://localhost:8000`   | FastAPI URL (used by Streamlit)       |
| `LOG_LEVEL`   | `INFO`                    | Python logging level                  |

Copy `.env.example` → `.env` and fill in your values for local development.

---

## 🧪 Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Numeric prediction
curl -X POST http://localhost:8000/predict/numeric \
  -H "Content-Type: application/json" \
  -d '{"age_of_policyholder":35,"age_of_car":3,"fuel_type":"Petrol","airbags":4,"policy_tenure":0.6,"ncap_rating":3}'
```

Or open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `FileNotFoundError: car_claim_numeric_model.pkl` | Run `python train_model.py` or copy the `.pkl` into `models/` |
| `Cannot reach backend` in Streamlit | Ensure FastAPI is running; check `BACKEND_URL` env var |
| Image model disabled | Place `best_image_model.pth` in `models/` — numeric prediction still works without it |
| `SMOTE` error during training | Dataset may be too small or have only one class; check class distribution in `train.csv` |
| Streamlit Cloud import errors | Ensure `requirements-frontend.txt` is set as the requirements file |

---

## 📄 License

MIT — see `LICENSE` for details.
