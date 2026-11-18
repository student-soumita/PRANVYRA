from flask import Blueprint, request, jsonify, session
from datetime import datetime
from database.db import get_db_connection, get_user_by_id
from services.air_quality import get_live_air_quality
from services.weather import get_live_weather
from services.recommendation_engine import generate_smart_daily_planner
from services.auth import get_current_user_id

planner_bp = Blueprint("planner", __name__)

@planner_bp.route("/today", methods=["GET"])
def get_today_planner():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "User record not found."}), 404

    v_id = f"user_{user_id}"
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM daily_routines WHERE (user_id = ? OR visitor_id = ?) AND routine_date = ? ORDER BY id ASC",
        (user_id, v_id, today_str)
    ).fetchall()
    
    # If no tasks exist for today, automatically generate them based on user's profile & air quality
    if not rows:
        lat = user.get("latitude")
        lon = user.get("longitude")
        aqi_val = 100
        weather_data = {"temperature": 24.0}
        
        if lat is not None and lon is not None:
            aqi_res = get_live_air_quality(lat, lon)
            if aqi_res.get("is_available"):
                aqi_val = aqi_res.get("aqi", 100)
            weather_res = get_live_weather(lat, lon)
            if weather_res.get("success"):
                weather_data = weather_res
                
        new_tasks = generate_smart_daily_planner(aqi_val, weather_data, user)
        for t in new_tasks:
            conn.execute(
                """INSERT INTO daily_routines 
                   (user_id, visitor_id, routine_date, time_slot, title, description, priority, action_type, is_completed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (user_id, v_id, today_str, t["time_slot"], t["title"], t["description"], t["priority"], t["action_type"])
            )
        conn.commit()
        rows = conn.execute(
            "SELECT * FROM daily_routines WHERE (user_id = ? OR visitor_id = ?) AND routine_date = ? ORDER BY id ASC",
            (user_id, v_id, today_str)
        ).fetchall()
        
    tasks = [dict(r) for r in rows]
    total = len(tasks)
    completed = sum(1 for t in tasks if t["is_completed"])
    pct = round((completed / total * 100)) if total > 0 else 0
    
    conn.close()
    
    return jsonify({
        "success": True,
        "date": today_str,
        "tasks": tasks,
        "total_tasks": total,
        "completed_tasks": completed,
        "completion_percentage": pct
    })

@planner_bp.route("/toggle", methods=["POST"])
def toggle_task():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    data = request.get_json() or {}
    task_id = data.get("task_id")
    
    if not task_id:
        return jsonify({"success": False, "error": "Task ID required."}), 400
        
    conn = get_db_connection()
    task = conn.execute(
        "SELECT * FROM daily_routines WHERE id = ? AND (user_id = ? OR visitor_id = ?)",
        (task_id, user_id, v_id)
    ).fetchone()
    if not task:
        conn.close()
        return jsonify({"success": False, "error": "Task not found or access denied."}), 404
        
    new_state = 0 if task["is_completed"] else 1
    completed_time = datetime.now().isoformat() if new_state else None
    
    conn.execute(
        "UPDATE daily_routines SET is_completed = ?, completed_at = ? WHERE id = ?",
        (new_state, completed_time, task_id)
    )
    
    # Update green points and impact log on completion
    if new_state:
        conn.execute("UPDATE users SET green_points = green_points + 15 WHERE id = ?", (user_id,))
        conn.execute(
            """INSERT INTO impact_logs 
               (user_id, visitor_id, action_type, title, description, co2_saved_kg, points_earned)
               VALUES (?, ?, 'daily_routine', ?, ?, 0.45, 15)""",
            (user_id, v_id, task["title"], "Completed scheduled environmental routine action")
        )
    else:
        conn.execute("UPDATE users SET green_points = MAX(0, green_points - 15) WHERE id = ?", (user_id,))
        
    conn.commit()
    
    today_str = task["routine_date"]
    all_tasks = conn.execute(
        "SELECT is_completed FROM daily_routines WHERE (user_id = ? OR visitor_id = ?) AND routine_date = ?",
        (user_id, v_id, today_str)
    ).fetchall()
    
    total = len(all_tasks)
    completed = sum(1 for r in all_tasks if r["is_completed"])
    pct = round((completed / total * 100)) if total > 0 else 0
    
    conn.close()
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "is_completed": bool(new_state),
        "completion_percentage": pct,
        "points_delta": 15 if new_state else -15
    })

@planner_bp.route("/generate", methods=["POST"])
def force_regenerate_planner():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "User record not found."}), 404

    v_id = f"user_{user_id}"
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    lat = user.get("latitude")
    lon = user.get("longitude")
    aqi_val = 100
    weather_data = {"temperature": 24.0}
    
    if lat is not None and lon is not None:
        aqi_res = get_live_air_quality(lat, lon)
        if aqi_res.get("is_available"):
            aqi_val = aqi_res.get("aqi", 100)
        weather_res = get_live_weather(lat, lon)
        if weather_res.get("success"):
            weather_data = weather_res
            
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM daily_routines WHERE (user_id = ? OR visitor_id = ?) AND routine_date = ? AND is_completed = 0",
        (user_id, v_id, today_str)
    )
    
    new_tasks = generate_smart_daily_planner(aqi_val, weather_data, user)
    for t in new_tasks:
        conn.execute(
            """INSERT INTO daily_routines 
               (user_id, visitor_id, routine_date, time_slot, title, description, priority, action_type, is_completed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (user_id, v_id, today_str, t["time_slot"], t["title"], t["description"], t["priority"], t["action_type"])
        )
    conn.commit()
    
    rows = conn.execute(
        "SELECT * FROM daily_routines WHERE (user_id = ? OR visitor_id = ?) AND routine_date = ? ORDER BY id ASC",
        (user_id, v_id, today_str)
    ).fetchall()
    conn.close()
    
    tasks = [dict(r) for r in rows]
    total = len(tasks)
    completed = sum(1 for t in tasks if t["is_completed"])
    pct = round((completed / total * 100)) if total > 0 else 0
    
    return jsonify({
        "success": True,
        "tasks": tasks,
        "total_tasks": total,
        "completed_tasks": completed,
        "completion_percentage": pct
    })

