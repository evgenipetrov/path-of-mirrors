import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

try:
    from src.main import app
    from fastapi.routing import APIRoute

    endpoints = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in route.methods:
                endpoints.append(f"{method} {route.path}")

    # Sort alphabetically
    for endpoint in sorted(endpoints):
        print(endpoint)

except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error listing endpoints: {e}")
    sys.exit(1)
