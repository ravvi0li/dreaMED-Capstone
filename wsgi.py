"""
WSGI Entry Point
"""

from app import create_app
import os

# Create Flask app
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Use environment variable PORT or default to 5001
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
