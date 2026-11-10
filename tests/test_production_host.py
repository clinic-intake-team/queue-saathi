import tempfile
import unittest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.production import create_app


class ProductionHostTests(unittest.TestCase):
    def test_same_origin_api_and_spa_with_safe_asset_handling(self):
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            (dist / 'index.html').write_text('<html>QueueSaathi</html>')
            (dist / 'assets').mkdir()
            (dist / 'assets/app.js').write_text('console.log("app")')
            api = FastAPI()
            @api.get('/health')
            def health():
                return {'status': 'ok'}
            client = TestClient(create_app(api, dist))
            self.assertEqual(client.get('/api/health').json(), {'status': 'ok'})
            for route in ['/', '/doctor', '/intake?new=1', '/results']:
                self.assertIn('QueueSaathi', client.get(route).text)
            self.assertEqual(client.get('/assets/app.js').status_code, 200)
            self.assertEqual(client.get('/assets/missing.js').status_code, 404)
            self.assertEqual(client.get('/api/not-found').status_code, 404)
            self.assertEqual(client.post('/doctor').status_code, 405)
            self.assertEqual(client.get('/%2e%2e/secret').status_code, 404)

    def test_missing_build_is_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'Frontend build missing'):
                create_app(FastAPI(), directory)
