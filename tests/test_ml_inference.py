"""
Unit tests for ML inference module
"""

import unittest
from app.ml_inference import ModelInference, predict_risk

class MLInferenceTestCase(unittest.TestCase):
    """Test ML inference functionality"""
    
    def setUp(self):
        """Set up test case"""
        self.inference = ModelInference()
    
    def test_model_loading(self):
        """Test that models are loaded correctly"""
        self.assertIsNotNone(self.inference.model)
        self.assertIsNotNone(self.inference.mlb)
        self.assertIsNotNone(self.inference.feature_names)
    
    def test_feature_extraction(self):
        """Test feature extraction from database"""
        # This requires database to be populated
        # features, cid = self.inference.get_drug_features('aspirin')
        # self.assertIsNotNone(features)
        pass
    
    def test_atc_description(self):
        """Test ATC code description"""
        desc = self.inference.get_atc_description('A01BC23')
        self.assertIsInstance(desc, str)
        self.assertNotEqual(desc, '')

if __name__ == '__main__':
    unittest.main()
