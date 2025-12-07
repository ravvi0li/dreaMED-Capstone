"""
Flask Routes
API endpoints and web pages
"""

from flask import Blueprint, render_template, request, jsonify
from app.ml_inference import predict_risk, inference_engine
from app.utils import search_drugs, get_top_side_effects, get_database_stats
import json
from pathlib import Path

# Blueprints
api_bp = Blueprint('api', __name__)
main_bp = Blueprint('main', __name__)

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / 'models'

# ============================================================================
# WEB PAGES
# ============================================================================

@main_bp.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

# ============================================================================
# API ENDPOINTS
# ============================================================================

@api_bp.route('/predict', methods=['POST'])
def predict():
    """
    Predict side effects for a drug
    
    Request JSON:
        {
            "drug_name": "aspirin"
        }
    
    Response JSON:
        {
            "drug": "aspirin",
            "cid": "CID2244",
            "predictions": [
                {
                    "side_effect": "Nausea",
                    "probability": 0.85,
                    "severity": "high"
                },
                ...
            ],
            "summary": "Based on the properties of aspirin...",
            "model": "Random Forest",
            "total_predicted": 15
        }
    """
    data = request.get_json()
    
    if not data or 'drug_name' not in data:
        return jsonify({'error': 'Missing drug_name parameter'}), 400
    
    drug_name = data['drug_name']
    
    # Get prediction
    result = predict_risk(drug_name)
    
    if 'error' in result:
        return jsonify(result), 404
    
    return jsonify(result), 200

@api_bp.route('/drugs/search', methods=['GET'])
def search():
    """
    Search for drugs by name
    
    Query parameters:
        q: Search query
        limit: Maximum results (default: 10)
    
    Response JSON:
        {
            "query": "aspi",
            "results": [
                {
                    "cid": "CID2244",
                    "name": "aspirin",
                    "drugbank_id": "DB00945"
                },
                ...
            ],
            "count": 5
        }
    """
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    results = search_drugs(query, limit)
    
    return jsonify({
        'query': query,
        'results': results,
        'count': len(results)
    }), 200

@api_bp.route('/side-effects/top', methods=['GET'])
def top_side_effects():
    """
    Get most common side effects
    
    Query parameters:
        limit: Maximum results (default: 20)
    
    Response JSON:
        {
            "side_effects": [
                {
                    "name": "Nausea",
                    "count": 450
                },
                ...
            ],
            "count": 20
        }
    """
    limit = request.args.get('limit', 20, type=int)
    
    effects = get_top_side_effects(limit)
    
    return jsonify({
        'side_effects': effects,
        'count': len(effects)
    }), 200

@api_bp.route('/stats', methods=['GET'])
def stats():
    """
    Get model performance metrics and database statistics
    
    Response JSON:
        {
            "database": {
                "total_drugs": 1431,
                "total_side_effects": 5000,
                ...
            },
            "model": {
                "name": "Random Forest",
                "metrics": {
                    "precision_macro": 0.85,
                    "recall_macro": 0.80,
                    "f1_macro": 0.82,
                    "hamming_loss": 0.05
                },
                "n_features": 250,
                "n_labels": 50
            }
        }
    """
    # Database stats
    db_stats = get_database_stats()
    
    # Model stats
    model_stats = {
        'name': inference_engine.metrics_data['best_model'],
        'metrics': inference_engine.metrics_data['metrics'][inference_engine.metrics_data['best_model']],
        'n_features': inference_engine.metrics_data['n_features'],
        'n_labels': inference_engine.metrics_data['n_labels']
    }
    
    return jsonify({
        'database': db_stats,
        'model': model_stats
    }), 200

@api_bp.route('/visualizations/model-comparison', methods=['GET'])
def model_comparison():
    """
    Get model comparison data for visualization
    
    Response JSON:
        {
            "models": ["Logistic Regression", "Random Forest", "MLP"],
            "f1_scores": [0.75, 0.82, 0.78],
            "precision": [0.80, 0.85, 0.81],
            "recall": [0.70, 0.80, 0.76]
        }
    """
    metrics = inference_engine.metrics_data['metrics']
    
    models = list(metrics.keys())
    f1_scores = [metrics[m]['f1_macro'] for m in models]
    precision = [metrics[m]['precision_macro'] for m in models]
    recall = [metrics[m]['recall_macro'] for m in models]
    
    return jsonify({
        'models': models,
        'f1_scores': f1_scores,
        'precision': precision,
        'recall': recall
    }), 200

@api_bp.route('/visualizations/feature-importance', methods=['GET'])
def feature_importance():
    """
    Get feature importance data for visualization
    
    Response JSON:
        {
            "features": ["atc_l2_N02", "atc_l2_C01", ...],
            "importance": [0.15, 0.12, ...]
        }
    """
    # Load feature importance
    importance_file = MODELS_DIR / 'feature_importance.json'
    
    if not importance_file.exists():
        return jsonify({'error': 'Feature importance data not found'}), 404
    
    with open(importance_file, 'r') as f:
        importance_data = json.load(f)
    
    # Get Random Forest importance (or best model)
    model_name = inference_engine.metrics_data['best_model']
    if model_name not in importance_data:
        model_name = list(importance_data.keys())[0]
    
    importance = importance_data[model_name]
    
    # Sort and get top 20
    sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:20]
    features, scores = zip(*sorted_features) if sorted_features else ([], [])
    
    return jsonify({
        'features': list(features),
        'importance': list(scores),
        'model': model_name
    }), 200

@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': inference_engine._initialized
    }), 200
