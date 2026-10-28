"""
SpaceScope: Vercel Serverless Entrypoint
Exposes the WSGI application for @vercel/python runtime
"""
import os
import sys

# Ensure repository root is on sys.path so modules can be imported seamlessly
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from flask_api import app, api

# Alias for serverless runtime handlers
handler = app

if __name__ == "__main__":
    app.run(debug=True, port=5000)
