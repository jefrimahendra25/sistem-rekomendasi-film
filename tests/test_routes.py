import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json

# Tambahkan direktori utama ke path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        """Setup test client dan konfigurasi."""
        self.app = create_app().test_client()
        self.app.testing = True
    
    def test_home_page(self):
        """Test halaman utama mengembalikan status 200."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'FilmKu', response.data)
    
    def test_search_endpoint(self):
        """Test endpoint pencarian."""
        response = self.app.get('/api/search?q=komang')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('results', data)
        self.assertEqual(data['status'], 'success')
        self.assertIsInstance(data['results'], list)
        # Pastikan ada hasil pencarian
        self.assertGreater(len(data['results']), 0, "Pencarian harus mengembalikan setidaknya 1 hasil")
    
    def test_genres_endpoint(self):
        """Test endpoint daftar genre."""
        response = self.app.get('/api/genres')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('genres', data)
        self.assertIsInstance(data['genres'], list)
    
    def test_countries_endpoint(self):
        """Test endpoint daftar negara."""
        response = self.app.get('/api/countries')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('countries', data)
        self.assertIsInstance(data['countries'], list)

    def test_welcome_endpoint(self):
        """Test endpoint welcome dengan logging."""
        response = self.app.get('/api/welcome')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('message', data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Selamat datang di API Rekomendasi Film!')

if __name__ == '__main__':
    unittest.main()
