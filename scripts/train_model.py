"""
Multi-Label Classification Model Training for Side Effect Prediction
Implements Logistic Regression, Random Forest, and MLP models
"""

import sqlite3
import pandas as pd
import numpy as np
import json
import pickle
from pathlib import Path
from collections import Counter

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, 
    hamming_loss, classification_report
)

import warnings
warnings.filterwarnings('ignore')

# Paths
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'pharma.db'
MODELS_DIR = BASE_DIR / 'models'

# Hyperparameters
TOP_N_SIDE_EFFECTS = 50  # Keep top 50 most frequent side effects
TEST_SIZE = 0.2
RANDOM_STATE = 42

class SideEffectPredictor:
    """Complete ML pipeline for side effect prediction"""
    
    def __init__(self, top_n_effects=50):
        self.top_n_effects = top_n_effects
        self.mlb = None
        self.feature_names = None
        self.models = {}
        self.metrics = {}
        
    def load_data_from_db(self):
        """Load and prepare data from SQLite database"""
        print("📥 Loading data from database...")
        
        conn = sqlite3.connect(DB_PATH)
        
        # Get drugs with ATC codes
        query_drugs = '''
            SELECT DISTINCT d.cid, d.drug_name
            FROM drugs d
            INNER JOIN atc_codes a ON d.cid = a.cid
        '''
        df_drugs = pd.read_sql_query(query_drugs, conn)
        
        # Get ATC codes for each drug (pivot to multi-hot encoding)
        query_atc = '''
            SELECT cid, 
                   GROUP_CONCAT(DISTINCT atc_level1) as atc_l1,
                   GROUP_CONCAT(DISTINCT atc_level2) as atc_l2,
                   GROUP_CONCAT(DISTINCT atc_level3) as atc_l3,
                   GROUP_CONCAT(DISTINCT atc_level4) as atc_l4,
                   GROUP_CONCAT(DISTINCT atc_level5) as atc_l5
            FROM atc_codes
            GROUP BY cid
        '''
        df_atc = pd.read_sql_query(query_atc, conn)
        
        # Get side effects for each drug
        query_se = '''
            SELECT dse.cid, se.side_effect_name
            FROM drug_side_effects dse
            INNER JOIN side_effects se ON dse.side_effect_id = se.id
        '''
        df_se = pd.read_sql_query(query_se, conn)
        conn.close()
        
        # Merge data
        df = df_drugs.merge(df_atc, on='cid', how='left')
        
        # Group side effects by drug
        side_effects_grouped = df_se.groupby('cid')['side_effect_name'].apply(list).reset_index()
        df = df.merge(side_effects_grouped, on='cid', how='left')
        
        # Remove drugs without side effects
        df = df.dropna(subset=['side_effect_name'])
        
        print(f"✓ Loaded {len(df)} drugs with side effects")
        return df
    
    def filter_top_side_effects(self, df):
        """Keep only top N most frequent side effects"""
        print(f"\n🔍 Filtering to top {self.top_n_effects} side effects...")
        
        # Count all side effects
        all_effects = []
        for effects in df['side_effect_name']:
            all_effects.extend(effects)
        
        effect_counts = Counter(all_effects)
        top_effects = set([effect for effect, count in effect_counts.most_common(self.top_n_effects)])
        
        # Filter side effects for each drug
        df['side_effect_name'] = df['side_effect_name'].apply(
            lambda effects: [e for e in effects if e in top_effects]
        )
        
        # Remove drugs with no side effects after filtering
        df = df[df['side_effect_name'].apply(len) > 0]
        
        print(f"✓ Kept {len(df)} drugs with at least one of top {self.top_n_effects} side effects")
        print(f"\nTop 10 side effects:")
        for i, (effect, count) in enumerate(effect_counts.most_common(10), 1):
            print(f"   {i}. {effect}: {count} drugs")
        
        return df
    
    def create_features(self, df):
        """Create feature matrix from ATC codes and drug names"""
        print("\n🔧 Engineering features...")
        
        features = []
        
        # Create multi-hot encoding for ATC codes at different levels
        for level in ['atc_l1', 'atc_l2', 'atc_l3', 'atc_l4', 'atc_l5']:
            # Split concatenated codes and create binary features
            all_codes = set()
            for codes_str in df[level].dropna():
                all_codes.update(codes_str.split(','))
            
            for code in sorted(all_codes):
                df[f'{level}_{code}'] = df[level].apply(
                    lambda x: 1 if pd.notna(x) and code in x.split(',') else 0
                )
                features.append(f'{level}_{code}')
        
        # Optional: Add TF-IDF features from drug names
        tfidf = TfidfVectorizer(max_features=50, ngram_range=(1, 2))
        tfidf_features = tfidf.fit_transform(df['drug_name'].fillna(''))
        tfidf_df = pd.DataFrame(
            tfidf_features.toarray(),
            columns=[f'name_tfidf_{i}' for i in range(tfidf_features.shape[1])]
        )
        
        # Combine all features
        X = pd.concat([
            df[features].reset_index(drop=True),
            tfidf_df
        ], axis=1)
        
        self.feature_names = X.columns.tolist()
        
        print(f"✓ Created {X.shape[1]} features")
        print(f"   - ATC hierarchical features: {len(features)}")
        print(f"   - Drug name TF-IDF features: {tfidf_features.shape[1]}")
        
        return X
    
    def create_labels(self, df):
        """Create multi-label binary matrix"""
        print("\n🏷️  Creating multi-label target matrix...")
        
        self.mlb = MultiLabelBinarizer()
        y = self.mlb.fit_transform(df['side_effect_name'])
        
        print(f"✓ Created label matrix: {y.shape}")
        print(f"   - {y.shape[0]} samples")
        print(f"   - {y.shape[1]} side effect labels")
        print(f"   - Average labels per drug: {y.sum(axis=1).mean():.2f}")
        
        return y
    
    def train_models(self, X_train, y_train, X_test, y_test):
        """Train and evaluate multiple models"""
        print("\n🤖 Training models...")
        print("="*60)
        
        # Model 1: Logistic Regression (Interpretable)
        print("\n1️⃣  Training Logistic Regression...")
        lr = OneVsRestClassifier(
            LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, C=1.0),
            n_jobs=-1
        )
        lr.fit(X_train, y_train)
        self.models['Logistic Regression'] = lr
        self.evaluate_model('Logistic Regression', lr, X_test, y_test)
        
        # Model 2: Random Forest (Interpretable, better performance)
        print("\n2️⃣  Training Random Forest...")
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        self.models['Random Forest'] = rf
        self.evaluate_model('Random Forest', rf, X_test, y_test)
        
        # Model 3: MLP (Black-box, deep learning)
        print("\n3️⃣  Training MLP Neural Network...")
        mlp = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            max_iter=500,
            random_state=RANDOM_STATE,
            early_stopping=True,
            validation_fraction=0.1
        )
        mlp.fit(X_train, y_train)
        self.models['MLP'] = mlp
        self.evaluate_model('MLP', mlp, X_test, y_test)
        
        print("\n" + "="*60)
    
    def evaluate_model(self, name, model, X_test, y_test):
        """Evaluate a single model"""
        y_pred = model.predict(X_test)
        
        metrics = {
            'precision_macro': precision_score(y_test, y_pred, average='macro', zero_division=0),
            'precision_micro': precision_score(y_test, y_pred, average='micro', zero_division=0),
            'recall_macro': recall_score(y_test, y_pred, average='macro', zero_division=0),
            'recall_micro': recall_score(y_test, y_pred, average='micro', zero_division=0),
            'f1_macro': f1_score(y_test, y_pred, average='macro', zero_division=0),
            'f1_micro': f1_score(y_test, y_pred, average='micro', zero_division=0),
            'hamming_loss': hamming_loss(y_test, y_pred)
        }
        
        self.metrics[name] = metrics
        
        print(f"\n📊 {name} Performance:")
        print(f"   Precision (Macro): {metrics['precision_macro']:.4f}")
        print(f"   Precision (Micro): {metrics['precision_micro']:.4f}")
        print(f"   Recall (Macro):    {metrics['recall_macro']:.4f}")
        print(f"   Recall (Micro):    {metrics['recall_micro']:.4f}")
        print(f"   F1-Score (Macro):  {metrics['f1_macro']:.4f}")
        print(f"   F1-Score (Micro):  {metrics['f1_micro']:.4f}")
        print(f"   Hamming Loss:      {metrics['hamming_loss']:.4f}")
    
    def extract_feature_importance(self):
        """Extract feature importance from interpretable models"""
        print("\n🔍 Extracting feature importance...")
        
        importance_data = {}
        
        # Logistic Regression coefficients
        if 'Logistic Regression' in self.models:
            lr = self.models['Logistic Regression']
            # Average absolute coefficients across all binary classifiers
            coefs = np.abs(np.array([clf.coef_[0] for clf in lr.estimators_])).mean(axis=0)
            importance_data['Logistic Regression'] = dict(zip(self.feature_names, coefs))
        
        # Random Forest feature importance
        if 'Random Forest' in self.models:
            rf = self.models['Random Forest']
            importance_data['Random Forest'] = dict(zip(self.feature_names, rf.feature_importances_))
        
        return importance_data
    
    def save_models(self):
        """Save trained models and artifacts"""
        print("\n💾 Saving models and artifacts...")
        
        MODELS_DIR.mkdir(exist_ok=True)
        
        # Save best model (highest F1 macro)
        best_model_name = max(self.metrics.items(), key=lambda x: x[1]['f1_macro'])[0]
        best_model = self.models[best_model_name]
        
        with open(MODELS_DIR / 'best_model.pkl', 'wb') as f:
            pickle.dump(best_model, f)
        print(f"✓ Saved best model ({best_model_name})")
        
        # Save all models
        for name, model in self.models.items():
            filename = name.lower().replace(' ', '_') + '.pkl'
            with open(MODELS_DIR / filename, 'wb') as f:
                pickle.dump(model, f)
        print(f"✓ Saved all {len(self.models)} models")
        
        # Save label binarizer
        with open(MODELS_DIR / 'label_binarizer.pkl', 'wb') as f:
            pickle.dump(self.mlb, f)
        print("✓ Saved label binarizer")
        
        # Save feature names
        with open(MODELS_DIR / 'feature_names.pkl', 'wb') as f:
            pickle.dump(self.feature_names, f)
        print("✓ Saved feature names")
        
        # Save metrics as JSON
        with open(MODELS_DIR / 'model_metrics.json', 'w') as f:
            json.dump({
                'metrics': self.metrics,
                'best_model': best_model_name,
                'n_features': len(self.feature_names),
                'n_labels': len(self.mlb.classes_),
                'top_n_effects': self.top_n_effects
            }, f, indent=2)
        print("✓ Saved model metrics")
        
        # Save feature importance
        importance = self.extract_feature_importance()
        with open(MODELS_DIR / 'feature_importance.json', 'w') as f:
            json.dump(importance, f, indent=2)
        print("✓ Saved feature importance")
        
        # Save side effect labels
        with open(MODELS_DIR / 'side_effect_labels.json', 'w') as f:
            json.dump(self.mlb.classes_.tolist(), f, indent=2)
        print("✓ Saved side effect labels")

def main():
    """Main training pipeline"""
    print("🚀 Starting ML Model Training Pipeline")
    print("="*60)
    
    # Initialize predictor
    predictor = SideEffectPredictor(top_n_effects=TOP_N_SIDE_EFFECTS)
    
    # Load data
    df = predictor.load_data_from_db()
    
    # Filter to top side effects
    df = predictor.filter_top_side_effects(df)
    
    # Create features and labels
    X = predictor.create_features(df)
    y = predictor.create_labels(df)
    
    # Train-test split
    print(f"\n📊 Splitting data (train: {int((1-TEST_SIZE)*100)}%, test: {int(TEST_SIZE*100)}%)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"✓ Train set: {X_train.shape[0]} samples")
    print(f"✓ Test set: {X_test.shape[0]} samples")
    
    # Train models
    predictor.train_models(X_train, y_train, X_test, y_test)
    
    # Save everything
    predictor.save_models()
    
    print("\n" + "="*60)
    print("✅ Training pipeline completed successfully!")
    print(f"📁 Models saved to: {MODELS_DIR}")
    
    # Print comparison table
    print("\n" + "="*60)
    print("MODEL COMPARISON TABLE")
    print("="*60)
    print(f"{'Model':<20} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Hamming':<10}")
    print(f"{'     ':<20} {'(Macro)':<12} {'(Macro)':<12} {'(Macro)':<12} {'Loss':<10}")
    print("-"*60)
    
    for name, metrics in predictor.metrics.items():
        print(f"{name:<20} {metrics['precision_macro']:<12.4f} {metrics['recall_macro']:<12.4f} "
              f"{metrics['f1_macro']:<12.4f} {metrics['hamming_loss']:<10.4f}")
    
    print("="*60)

if __name__ == '__main__':
    main()
