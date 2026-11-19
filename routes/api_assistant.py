import json
from flask import Blueprint, request, jsonify, session
from database.db import get_db_connection, get_user_by_id
from services.ai_orchestrator import process_chat_query
from services.expert_router import list_all_experts, get_expert_details
from services.auth import get_current_user_id

assistant_bp = Blueprint("assistant", __name__)

@assistant_bp.route("/experts", methods=["GET"])
def get_experts_list():
    """Returns the list of 5 specialized environmental expert roles."""
    experts = list_all_experts()
    return jsonify({
        "success": True,
        "experts": experts
    })

@assistant_bp.route("/chat", methods=["POST"])
def chat_with_assistant():
    """
    Main conversational interface for PRANVYRA Intelligence Core.
    Supports auto/manual expert routing, multi-turn memory, and trilingual responses.
    Strictly isolates conversation history per authenticated user.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "User record not found."}), 404

    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    req_lang = (data.get("language") or "").strip().lower()
    if req_lang in ["en", "hi", "bn"]:
        language = req_lang
    elif session.get("language_pref") in ["en", "hi", "bn"]:
        language = session.get("language_pref")
    elif user and user.get("language_pref") in ["en", "hi", "bn"]:
        language = user.get("language_pref")
    else:
        language = "en"
    session["language_pref"] = language
    requested_role = data.get("expert_role", "auto")
    lat = data.get("lat") or user.get("latitude")
    lon = data.get("lon") or user.get("longitude")
    
    if not user_message:
        return jsonify({"success": False, "error": "Message cannot be empty."}), 400

    user["visitor_id"] = f"user_{user_id}"

    # Process inquiry through Intelligence Core Orchestrator
    result = process_chat_query(
        user_message=user_message,
        visitor_id=user["visitor_id"],
        requested_role=requested_role,
        language=language,
        lat=lat,
        lon=lon
    )
    
    return jsonify(result)

@assistant_bp.route("/history", methods=["GET"])
def get_chat_history():
    """Retrieves private conversation history for the active authenticated user."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT role, message, language, structured_card_json, created_at FROM chat_history WHERE (user_id = ? OR visitor_id = ?) ORDER BY id ASC LIMIT 50",
        (user_id, v_id)
    ).fetchall()
    conn.close()
    
    history = []
    for r in rows:
        card = None
        if r["structured_card_json"]:
            try:
                card = json.loads(r["structured_card_json"])
            except Exception:
                pass
        history.append({
            "role": r["role"],
            "message": r["message"],
            "language": r["language"] or "en",
            "structured_card": card,
            "created_at": r["created_at"]
        })
        
    return jsonify({"success": True, "history": history})

@assistant_bp.route("/clear", methods=["POST"])
def clear_chat():
    """Resets the conversation history for the active authenticated user only."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    conn = get_db_connection()
    conn.execute("DELETE FROM chat_history WHERE (user_id = ? OR visitor_id = ?)", (user_id, v_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Conversation history cleared."})

