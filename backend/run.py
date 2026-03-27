#!/usr/bin/env python
"""
TestFlow Backend - Development Server

Run this script to start the development server.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    port = 8000
    host = "0.0.0.0"

    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║           TestFlow Backend - Development Server          ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  API Docs:    http://localhost:{port}/docs           ║
    ║  ReDoc:       http://localhost:{port}/redoc          ║
    ║  Health:      http://localhost:{port}/health         ║
    ║  WebSocket:   ws://localhost:{port}/ws/executor     ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Press Ctrl+C to stop the server                             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.debug
    )
