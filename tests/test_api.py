"""
Unit tests for API endpoints
"""

import unittest
import json
from app import create_app

class APITestCase(unittest.TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_search_drugs(self):
        """Test drug search endpoint"""
        response = self.client.get('/api/drugs/search?q=aspirin')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('results', data)
    
    def test_predict_missing_drug(self):
        """Test prediction with missing drug name"""
        response = self.client.post('/api/predict',
                                   data=json.dumps({}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)
    
    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('database', data)
        self.assertIn('model', data)

if __name__ == '__main__':
    unittest.main()
