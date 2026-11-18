import uuid
from datetime import datetime, timezone
from database.db import get_db_connection

def generate_impact_receipt(visitor_id, decision_title, before_desc, after_desc, savings_kg, why_it_matters, methodology, user_id=None):
    """
    Feature 6: PERSONAL IMPACT RECEIPT
    Generates an official, verifiable environmental impact receipt for the user's decision.
    Clearly labeled as estimated avoided emissions, not a direct measurement of citywide air quality.
    Strictly isolated per authenticated user_id.
    """
    receipt_id = f"PRAN-RCPT-{uuid.uuid4().hex[:8].upper()}"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    savings_float = round(float(savings_kg), 2)

    if user_id is None and visitor_id and str(visitor_id).startswith("user_"):
        try:
            user_id = int(str(visitor_id).replace("user_", ""))
        except Exception:
            pass
    
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO impact_receipts 
           (receipt_id, user_id, visitor_id, decision_title, before_desc, after_desc, savings_kg, why_it_matters, methodology)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (receipt_id, user_id, visitor_id, decision_title, before_desc, after_desc, savings_float, why_it_matters, methodology)
    )
    conn.commit()
    conn.close()
    
    return {
        "receipt_id": receipt_id,
        "issued_at": now_str,
        "user_id": user_id,
        "visitor_id": visitor_id,
        "decision": decision_title,
        "decision_title": decision_title,
        "before_desc": before_desc,
        "after_desc": after_desc,
        "comparison": {
            "before": before_desc,
            "after": after_desc
        },
        "savings_kg": savings_float,
        "potential_savings": f"{savings_float} kg CO₂e Avoided",
        "potential_savings_raw_kg": savings_float,
        "why_it_matters": why_it_matters,
        "methodology": methodology,
        "disclaimer": "CRITICAL ENVIRONMENTAL NOTICE: This receipt records estimated personal emissions avoided through decision optimization. It is an educational accounting calculation based on documented conversion factors, NOT a direct physical sensor measurement of citywide air quality improvement."
    }

def get_visitor_receipts(visitor_id=None, user_id=None):
    """Retrieves all receipts issued to an authenticated user."""
    conn = get_db_connection()
    if user_id:
        v_id = f"user_{user_id}"
        rows = conn.execute(
            "SELECT * FROM impact_receipts WHERE (user_id = ? OR visitor_id = ?) ORDER BY id DESC LIMIT 50",
            (user_id, v_id)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM impact_receipts WHERE visitor_id = ? ORDER BY id DESC LIMIT 50",
            (visitor_id,)
        ).fetchall()
    conn.close()
    
    return [
        {
            "receipt_id": r["receipt_id"],
            "issued_at": r["created_at"],
            "decision": r["decision_title"],
            "decision_title": r["decision_title"],
            "before_desc": r["before_desc"],
            "after_desc": r["after_desc"],
            "comparison": {
                "before": r["before_desc"],
                "after": r["after_desc"]
            },
            "savings_kg": r["savings_kg"],
            "potential_savings": f"{r['savings_kg']} kg CO₂e Avoided",
            "potential_savings_raw_kg": r["savings_kg"],
            "why_it_matters": r["why_it_matters"],
            "methodology": r["methodology"],
            "disclaimer": "Estimated Avoided Emissions (Not a direct measurement of citywide air quality)"
        }
        for r in rows
    ]
