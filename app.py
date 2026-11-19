import os
from flask import Flask, render_template, jsonify, request, redirect, session
from flask_cors import CORS
from config import Config
from database.db import init_db

# Import Route Blueprints
from routes.api_auth import auth_bp
from routes.api_dashboard import dashboard_bp
from routes.api_assistant import assistant_bp
from routes.api_planner import planner_bp
from routes.api_indoor import indoor_bp
from routes.api_commute import commute_bp
from routes.api_impact import impact_bp
from routes.api_community import community_bp
from routes.api_user import user_bp
from routes.api_breath_route import breath_route_bp
from routes.api_life_switch import life_switch_bp

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    
    # Restrict CORS to configured origins (or wildcard in dev)
    allowed_origins = Config.ALLOWED_ORIGINS if Config.ALLOWED_ORIGINS != ["*"] else "*"
    CORS(app, origins=allowed_origins, supports_credentials=True)
    
    # Initialize DB schema & migrations
    with app.app_context():
        init_db()
        
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(assistant_bp, url_prefix="/api/assistant")
    app.register_blueprint(planner_bp, url_prefix="/api/planner")
    app.register_blueprint(indoor_bp, url_prefix="/api/indoor")
    app.register_blueprint(commute_bp, url_prefix="/api/commute")
    app.register_blueprint(impact_bp, url_prefix="/api/impact")
    app.register_blueprint(community_bp, url_prefix="/api/community")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(breath_route_bp, url_prefix="/api/breath-route")
    app.register_blueprint(life_switch_bp, url_prefix="/api/life-switch")

    # Mandatory Authentication Enforcement Filter
    @app.before_request
    def enforce_mandatory_authentication():
        # Whitelist public resources
        public_prefixes = ("/static/", "/login", "/register", "/logout", "/api/auth/")
        if request.path.startswith(public_prefixes) or request.path in ["/login", "/register", "/logout"]:
            return None

        # Check authenticated session strictly (no client-controlled bypass header)
        user_id = session.get("user_id")

        if not user_id:
            if request.path.startswith("/api/") or request.is_json or "application/json" in request.headers.get("Accept", ""):
                return jsonify({
                    "success": False,
                    "authenticated": False,
                    "error": "Authentication required. Please sign in to access PRANVYRA."
                }), 401
            return redirect(f"/login?next={request.path}")
        
    @app.route("/")
    def index():
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")
        return render_template("index.html")

    @app.route("/welcome")
    def welcome_view():
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")
        return render_template("welcome.html")

    @app.route("/login")
    def login_view():
        if session.get("user_id"):
            return redirect("/")
        return render_template("login.html")

    @app.route("/register")
    def register_view():
        if session.get("user_id"):
            return redirect("/")
        return render_template("login.html")

    @app.route("/logout")
    def logout_view():
        session.clear()
        return redirect("/login")
        
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Resource not found"}), 404
        
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500
        
    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    is_debug = os.environ.get("FLASK_ENV") == "development" or os.environ.get("FLASK_DEBUG") == "1"
    print(f"\n=======================================================")
    print(f"  PRANVYRA - AI Urban Air Intelligence & Action Platform")
    print(f"  Every Breath. A Better Tomorrow.")
    print(f"  Running on: http://127.0.0.1:{port} (Debug: {is_debug})")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=is_debug)
