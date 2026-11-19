"""
PRANVYRA Application Entry Point
Every Breath. A Better Tomorrow.
"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    is_debug = os.environ.get("FLASK_ENV") == "development" or os.environ.get("FLASK_DEBUG") == "1"
    print(f"\n=======================================================")
    print(f"  PRANVYRA - AI Urban Air Intelligence & Action Platform")
    print(f"  Every Breath. A Better Tomorrow.")
    print(f"  Access web application: http://127.0.0.1:{port} (Debug: {is_debug})")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=is_debug)

