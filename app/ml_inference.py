"""
ML Model Inference Module
Handles model loading and prediction
"""

import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
import sqlite3

# Paths
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / 'models'
DB_PATH = BASE_DIR / 'pharma.db'

class ModelInference:
    """Singleton class for loading and using ML models"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.load_models()
            self._initialized = True
    
    def load_models(self):
        """Load all models and artifacts"""
        print("Loading ML models...")
        
        # Load best model
        with open(MODELS_DIR / 'best_model.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        # Load label binarizer
        with open(MODELS_DIR / 'label_binarizer.pkl', 'rb') as f:
            self.mlb = pickle.load(f)
        
        # Load feature names
        with open(MODELS_DIR / 'feature_names.pkl', 'rb') as f:
            self.feature_names = pickle.load(f)
        
        # Load metrics
        with open(MODELS_DIR / 'model_metrics.json', 'r') as f:
            self.metrics_data = json.load(f)
        
        # Load side effect labels
        with open(MODELS_DIR / 'side_effect_labels.json', 'r') as f:
            self.side_effect_labels = json.load(f)
        
        print(f"✓ Loaded model: {self.metrics_data['best_model']}")
        print(f"✓ Loaded {len(self.side_effect_labels)} side effect labels")
    
    def get_drug_features(self, drug_name):
        """Extract features for a drug from database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get drug CID
        cursor.execute('''
            SELECT cid FROM drugs 
            WHERE LOWER(drug_name) = LOWER(?)
        ''', (drug_name,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None, None
        
        cid = result[0]
        
        # Get ATC codes
        cursor.execute('''
            SELECT atc_level1, atc_level2, atc_level3, atc_level4, atc_level5
            FROM atc_codes
            WHERE cid = ?
        ''', (cid,))
        atc_codes = cursor.fetchall()
        
        conn.close()
        
        if not atc_codes:
            return None, None
        
        # Build feature vector
        features = self._build_feature_vector(drug_name, atc_codes)
        
        return features, cid
    
    def _build_feature_vector(self, drug_name, atc_codes):
        """Build feature vector matching training format"""
        # Initialize feature dict
        feature_dict = {name: 0 for name in self.feature_names}
        
        # Set ATC features
        for atc_row in atc_codes:
            for level_idx, level_name in enumerate(['atc_l1', 'atc_l2', 'atc_l3', 'atc_l4', 'atc_l5']):
                code = atc_row[level_idx]
                if code:
                    feature_key = f'{level_name}_{code}'
                    if feature_key in feature_dict:
                        feature_dict[feature_key] = 1
        
        # Convert to DataFrame
        features_df = pd.DataFrame([feature_dict])
        
        return features_df
    
    def predict(self, drug_name):
        """Predict side effects for a drug"""
        # Get features
        features, cid = self.get_drug_features(drug_name)
        
        if features is None:
            return None
        
        # Predict
        predictions = self.model.predict(features)
        predict_proba = self.model.predict_proba(features)
        
        # Get predicted side effects
        predicted_labels = self.mlb.inverse_transform(predictions)[0]
        
        # Get probabilities for all labels
        # For OneVsRestClassifier, predict_proba returns shape (n_samples, n_classes)
        # Each column is the probability of the positive class for that label
        results = []
        
        # predict_proba is a 2D array of shape (n_samples, n_classes)
        # predict_proba[0] gives all class probabilities for the first sample
        for label in predicted_labels:
            label_idx = list(self.mlb.classes_).index(label)
            # Get probability for this label (column index)
            prob = predict_proba[0, label_idx]
            
            results.append({
                'side_effect': label,
                'probability': float(prob),
                'severity': self._estimate_severity(prob)
            })
        
        # Sort by probability
        results.sort(key=lambda x: x['probability'], reverse=True)
        
        return {
            'drug': drug_name,
            'cid': cid,
            'predictions': results[:10],  # Top 10
            'model': self.metrics_data['best_model'],
            'total_predicted': len(predicted_labels)
        }
    
    def _estimate_severity(self, probability):
        """Estimate severity based on probability"""
        if probability >= 0.7:
            return 'high'
        elif probability >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def get_atc_description(self, atc_code):
        """Get human-readable description of ATC code"""
        # ATC Level 1 descriptions
        atc_level1_desc = {
            'A': 'Alimentary tract and metabolism',
            'B': 'Blood and blood forming organs',
            'C': 'Cardiovascular system',
            'D': 'Dermatological',
            'G': 'Genito-urinary system and sex hormones',
            'H': 'Systemic hormonal preparations',
            'J': 'Anti-infectives for systemic use',
            'L': 'Antineoplastic and immunomodulating agents',
            'M': 'Musculo-skeletal system',
            'N': 'Nervous system',
            'P': 'Antiparasitic products',
            'R': 'Respiratory system',
            'S': 'Sensory organs',
            'V': 'Various'
        }
        
        if atc_code and len(atc_code) > 0:
            return atc_level1_desc.get(atc_code[0], 'Unknown category')
        return 'Unknown category'

# Global instance
inference_engine = ModelInference()

def predict_risk(drug_name):
    """
    Main prediction function for user-friendly interface
    
    Args:
        drug_name: Name of the drug
        
    Returns:
        Dictionary with predictions and layman-friendly summary
    """
    result = inference_engine.predict(drug_name)
    
    if not result:
        return {
            'error': f'Drug "{drug_name}" not found in database',
            'suggestion': 'Please check the spelling or try a different name'
        }
    
    # Get ATC category for explanation
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT atc_level1, atc_level2
        FROM atc_codes
        WHERE cid = ?
        LIMIT 1
    ''', (result['cid'],))
    atc_result = cursor.fetchone()
    conn.close()
    
    atc_category = ''
    if atc_result and atc_result[0]:
        atc_category = inference_engine.get_atc_description(atc_result[0])
    
    # Generate layman's summary
    if result['predictions']:
        top_effect = result['predictions'][0]
        summary = (
            f"Based on the properties of {drug_name}, there is a predicted risk of "
            f"{top_effect['side_effect']} (probability: {top_effect['probability']:.1%})"
        )
        if atc_category:
            summary += f", likely due to its classification as a {atc_category.lower()} medication."
    else:
        summary = f"No significant side effects predicted for {drug_name} based on available data."
    
    result['summary'] = summary
    result['atc_category'] = atc_category
    
    return result
