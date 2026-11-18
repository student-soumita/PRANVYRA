"""
PRANVYRA Application Entry Point
Every Breath. A Better Tomorrow.
"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f"  PRANVYRA - AI Urban Air Intelligence & Action Platform")
    print(f"  Every Breath. A Better Tomorrow.")
    print(f"  Access web application: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=True)

