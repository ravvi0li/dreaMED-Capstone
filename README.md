# dreaMED - Drug Side Effect Predictor

A full-stack web application that uses machine learning to predict potential adverse drug reactions based on drug characteristics (ATC codes and drug names).

## Features

- **Multi-Label Classification**: Predicts multiple side effects simultaneously
- **Interactive Web Interface**: User-friendly search and prediction system
- **Model Comparison**: Evaluates Logistic Regression, Random Forest, and MLP
- **Real-time Inference**: Instant predictions with probability scores
- **Interpretability**: Feature importance analysis and layman-friendly explanations
- **Visualizations**: Interactive charts for model performance and insights

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **ML Libraries**: scikit-learn, pandas, numpy
- **Visualization**: Chart.js, matplotlib, seaborn

## Process
- prepared the Python environment and installed all the necessary dependencies.

- ran the ETL pipeline, processed the drug information and loaded into the database. stored the drug names, ATC classifications and their associated side effects.

- trained three machine learning models: logistic regression, random forest and multi-layer perceptron. The models learned from the available drug features and were evaluated to compare their predictive performance.

- the trained models were saved and the Flask application was launched. the system was accessed via localhost

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


## 🎯 Usage Example

1. **Search for a drug**: Type a drug name (e.g., "aspirin", "ibuprofen")
2. **View predictions**: See predicted side effects with probability scores
3. **Understand risks**: Read layman-friendly explanations
4. **Explore insights**: Check model comparison and feature importance charts
``


Built with ❤️ using Flask, scikit-learn, and Bootstrap
