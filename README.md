# Pharmacovigilance AI - Drug Side Effect Predictor

A full-stack web application that uses machine learning to predict potential adverse drug reactions based on drug characteristics (ATC codes and drug names).

## 🌟 Features

- **Multi-Label Classification**: Predicts multiple side effects simultaneously
- **Interactive Web Interface**: User-friendly search and prediction system
- **Model Comparison**: Evaluates Logistic Regression, Random Forest, and MLP
- **Real-time Inference**: Instant predictions with probability scores
- **Interpretability**: Feature importance analysis and layman-friendly explanations
- **Visualizations**: Interactive charts for model performance and insights

## 📊 Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Bootstrap 5
- **ML Libraries**: scikit-learn, pandas, numpy
- **Visualization**: Chart.js, matplotlib, seaborn

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or navigate to the repository**
   ```bash
   cd "Raveena Capstone"
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set your SECRET_KEY
   ```

### Database Setup

1. **Run the ETL pipeline to create and populate the database**
   ```bash
   python scripts/load_data.py
   ```

   This will:
   - Create the SQLite database (`pharma.db`)
   - Load drug names, ATC codes, and side effects
   - Create necessary indexes for fast queries

   Expected output:
   ```
   ✓ Database schema created
   ✓ Loaded 1,431 drug names
   ✓ Loaded 1,561 ATC code mappings
   ✓ Loaded X unique side effects
   ✓ Loaded X drug-side effect mappings
   ```

### Model Training

2. **Train the ML models**
   ```bash
   python scripts/train_model.py
   ```

   This will:
   - Load data from the database
   - Engineer features from ATC codes and drug names
   - Train three models (Logistic Regression, Random Forest, MLP)
   - Evaluate and compare models
   - Save trained models to `models/` directory

   Expected output:
   ```
   ✓ Loaded X drugs with side effects
   ✓ Created X features
   ✓ Train set: X samples
   ✓ Test set: X samples
   📊 Model Performance:
      - Logistic Regression: F1=0.XX
      - Random Forest: F1=0.XX
      - MLP: F1=0.XX
   ✓ Models saved to models/
   ```

   **Optional**: You can also explore the training process in Jupyter:
   ```bash
   jupyter notebook notebooks/model_training.ipynb
   ```

### Running the Application

3. **Start the Flask development server**
   ```bash
   python wsgi.py
   ```

   Or using Flask CLI:
   ```bash
   export FLASK_APP=wsgi.py
   flask run
   ```

4. **Access the application**
   - Open your browser and navigate to: `http://localhost:5000`

## 📁 Project Structure

```
Raveena Capstone/
│
├── data/                          # Raw data files (TSV/CSV)
│   ├── drug_atc.tsv
│   ├── drug_names (1).tsv
│   ├── drugbank vocabulary.csv
│   └── meddra_all_se (3) 2.tsv
│
├── models/                        # Trained ML models
│   ├── best_model.pkl
│   ├── logistic_regression.pkl
│   ├── random_forest.pkl
│   ├── mlp.pkl
│   ├── label_binarizer.pkl
│   ├── feature_names.pkl
│   ├── model_metrics.json
│   └── feature_importance.json
│
├── notebooks/                     # Jupyter notebooks
│   └── model_training.ipynb
│
├── scripts/                       # Data processing & training
│   ├── load_data.py              # ETL pipeline
│   └── train_model.py            # Model training
│
├── app/                           # Flask application
│   ├── __init__.py               # App factory
│   ├── routes.py                 # API endpoints
│   ├── models.py                 # Database models
│   ├── utils.py                  # Helper functions
│   └── ml_inference.py           # Model inference
│
├── static/                        # Frontend assets
│   ├── css/style.css
│   ├── js/app.js
│   └── images/
│
├── templates/                     # HTML templates
│   └── index.html
│
├── config.py                      # Configuration
├── wsgi.py                        # WSGI entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── .gitignore
└── README.md
```

## 🔌 API Endpoints

### Prediction
- `POST /api/predict` - Predict side effects for a drug
  ```json
  Request: {"drug_name": "aspirin"}
  Response: {
    "drug": "aspirin",
    "predictions": [...],
    "summary": "...",
    "model": "Random Forest"
  }
  ```

### Search
- `GET /api/drugs/search?q=<query>` - Search for drugs (autocomplete)

### Statistics
- `GET /api/stats` - Get model and database statistics
- `GET /api/side-effects/top` - Get most common side effects

### Visualizations
- `GET /api/visualizations/model-comparison` - Model performance data
- `GET /api/visualizations/feature-importance` - Feature importance data

## 🎯 Usage Example

1. **Search for a drug**: Type a drug name (e.g., "aspirin", "ibuprofen")
2. **View predictions**: See predicted side effects with probability scores
3. **Understand risks**: Read layman-friendly explanations
4. **Explore insights**: Check model comparison and feature importance charts

## 📈 Model Performance

The application trains and compares three models:

| Model                | Precision | Recall | F1-Score | Interpretability |
|---------------------|-----------|--------|----------|------------------|
| Logistic Regression | ✓         | ✓      | ✓        | ✅ High          |
| Random Forest       | ✓         | ✓      | ✓        | ✅ High          |
| MLP (Neural Net)    | ✓         | ✓      | ✓        | ⚠️ Low           |

The best-performing model is automatically selected for predictions.

## 🔧 Configuration

### Environment Variables (.env)
```bash
FLASK_ENV=development          # development or production
SECRET_KEY=your-secret-key     # Change in production
DATABASE_URL=sqlite:///pharma.db  # Or PostgreSQL URL
```

### Hyperparameters (scripts/train_model.py)
```python
TOP_N_SIDE_EFFECTS = 50  # Number of side effects to predict
TEST_SIZE = 0.2          # Train-test split ratio
RANDOM_STATE = 42        # Reproducibility seed
```

## 🚢 Deployment

### Production Setup

1. **Set environment to production**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=<strong-random-key>
   ```

2. **Use Gunicorn for serving**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
   ```

3. **Optional: Use PostgreSQL**
   ```bash
   export DATABASE_URL=postgresql://user:pass@host/dbname
   ```

### Docker (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
```

Build and run:
```bash
docker build -t pharma-app .
docker run -p 5000:5000 pharma-app
```

## 🧪 Testing

Run unit tests:
```bash
pytest tests/
```

Test API endpoints:
```bash
# Health check
curl http://localhost:5000/api/health

# Predict
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"drug_name": "aspirin"}'
```

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. It should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for medical guidance.

## 📚 Data Sources

- **SIDER**: Side Effect Resource database
- **DrugBank**: Comprehensive drug information database
- **ATC Classification**: WHO Anatomical Therapeutic Chemical system
- **MedDRA**: Medical Dictionary for Regulatory Activities

## 👥 Contributors

Raveena Capstone Project - 2025

## 📄 License

This project is for educational purposes.

## 🤝 Support

For issues or questions, please open an issue in the repository.

---

Built with ❤️ using Flask, scikit-learn, and Bootstrap
