# Getting Started Guide

## Quick Setup (Recommended)

The easiest way to get started is using the automated setup script:

```bash
cd "Raveena Capstone"
./start.sh
```

This script will:
1. Create a virtual environment
2. Install all dependencies
3. Set up the database
4. Train the ML models
5. Start the Flask server

**⚠️ Note**: Model training may take 5-10 minutes depending on your system.

---

## Manual Setup (Step-by-Step)

If you prefer to set up manually or the script doesn't work, follow these steps:

### Step 1: Set Up Virtual Environment

```bash
# Navigate to project directory
cd "Raveena Capstone"

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Set Up Database

```bash
python scripts/load_data.py
```

Expected output:
```
✓ Database schema created
✓ Loaded 1,431 drug names
✓ Loaded 1,561 ATC code mappings
✓ Loaded X unique side effects
```

### Step 4: Train Models

```bash
python scripts/train_model.py
```

Expected output:
```
✓ Loaded X drugs with side effects
✓ Created X features
Training models...
✓ Models saved to models/
```

### Step 5: Configure Environment

```bash
cp .env.example .env
# Edit .env and set SECRET_KEY for production
```

### Step 6: Run Application

```bash
python wsgi.py
```

Visit: http://localhost:5000

---

## Using the Application

### 1. Search for a Drug
- Type a drug name in the search box (e.g., "aspirin")
- Use autocomplete suggestions for faster input

### 2. View Predictions
- Click "Predict" to get side effect predictions
- See probability scores and severity levels
- Read layman-friendly explanations

### 3. Explore Insights
- Scroll down to view model comparison charts
- Check feature importance analysis
- Browse top side effects in the database

---

## API Usage Examples

### Get Drug Predictions

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"drug_name": "aspirin"}'
```

### Search for Drugs

```bash
curl http://localhost:5000/api/drugs/search?q=ibuprofen
```

### Get Statistics

```bash
curl http://localhost:5000/api/stats
```

---

## Troubleshooting

### Problem: Models not loading

**Solution**: Ensure you've run the training script:
```bash
python scripts/train_model.py
```

### Problem: Database empty

**Solution**: Run the ETL pipeline:
```bash
python scripts/load_data.py
```

### Problem: Import errors

**Solution**: Ensure virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problem: Port 5000 already in use

**Solution**: Use a different port:
```bash
export FLASK_RUN_PORT=8000
python wsgi.py
```

---

## Development Tips

### Re-training Models

If you want to re-train with different parameters:

1. Edit `scripts/train_model.py` and modify:
   - `TOP_N_SIDE_EFFECTS` (default: 50)
   - `TEST_SIZE` (default: 0.2)
   
2. Run training:
   ```bash
   python scripts/train_model.py
   ```

### Adding New Features

To add new drug features:

1. Edit `scripts/train_model.py` in the `create_features()` method
2. Re-train models
3. Restart Flask server

### Database Updates

To update the database with new data:

1. Replace TSV/CSV files in the root directory
2. Delete `pharma.db`
3. Run ETL pipeline:
   ```bash
   python scripts/load_data.py
   ```

---

## Production Deployment

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### Environment Variables

Set these in production:
```bash
export FLASK_ENV=production
export SECRET_KEY=<strong-random-key>
```

### Using PostgreSQL

```bash
export DATABASE_URL=postgresql://user:pass@host/dbname
```

---

## Next Steps

1. ✅ Complete setup and verify application works
2. 📊 Explore the model training notebook: `notebooks/model_training.ipynb`
3. 🔍 Test different drugs and analyze predictions
4. 📈 Review model comparison and feature importance
5. 🚀 Deploy to production (Heroku, AWS, etc.)

---

## Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review logs in the terminal
3. Verify all dependencies are installed
4. Ensure data files are in the correct location

---

**Happy Predicting! 🧬💊**
