import unittest
import os
import sqlite3
import database
import app
from io import BytesIO

class TestSecurity(unittest.TestCase):

    def setUp(self):
        # Use an in-memory DB for tests, or a specific test file
        self.test_db = "test_body_orchestrator.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        os.environ["BODY_ORCH_DB"] = self.test_db
        database.init_db()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_sql_injection_prevention(self):
        # Attempt to inject SQL into the name field
        malicious_name = "Hacked', address='Pwned' WHERE id=1;--"
        database.update_organization(1, malicious_name, "Normal Address", "Contact")
        
        # Verify that it was treated as a literal string, not executed as SQL
        org = database.get_organization(1)
        self.assertEqual(org['name'], malicious_name)
        self.assertEqual(org['address'], "Normal Address")

    def test_xss_prevention(self):
        malicious_name = "<script>alert('XSS')</script>"
        database.update_organization(1, malicious_name, "Address", "Contact")
        org = database.get_organization(1)
        
        # Render the template to ensure the output is escaped
        rendered_html = app.render_dashboard_template(org).decode('utf-8')
        
        self.assertNotIn("<script>", rendered_html)
        self.assertIn("&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;", rendered_html)

    def test_dns_rebinding_protection(self):
        def dummy_start_response(status, headers):
            self.assertEqual(status, '403 Forbidden')

        environ = {
            'HTTP_HOST': 'malicious-domain.com:5050',
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'GET'
        }
        
        response = app.application(environ, dummy_start_response)
        self.assertEqual(response, [b"403 Forbidden: Invalid Host header"])

    def test_csrf_protection_missing_token(self):
        def dummy_start_response(status, headers):
            self.assertEqual(status, '403 Forbidden')

        environ = {
            'HTTP_HOST': '127.0.0.1:5050',
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': '12',
            'wsgi.input': BytesIO(b"name=Testing")
        }
        
        response = app.application(environ, dummy_start_response)
        # Verify that the response is the rendered network template (which is returned on CSRF failure for root)
        self.assertIn(b"Orchestration Hub", response[0])

    def test_payload_too_large(self):
        def dummy_start_response(status, headers):
            self.assertEqual(status, '413 Payload Too Large')

        # Simulate a 2MB payload, which exceeds the 1MB limit
        environ = {
            'HTTP_HOST': '127.0.0.1:5050',
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': str(2 * 1024 * 1024)
        }
        
        response = app.application(environ, dummy_start_response)
        self.assertEqual(response, [b"Payload Too Large"])

if __name__ == '__main__':
    unittest.main()
