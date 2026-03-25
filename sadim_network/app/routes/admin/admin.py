# ملف لادارة الموقع هذه نسخة متواضعة
#_____  
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
#_________
from app.db.sadim_db import get_db_connection
from utlis.login_required import login_required
from utlis.permissions import admin_required
from datetime import datetime
admin_bp = Blueprint('admin', __name__, url_prefix='/dashboard', template_folder='../../templates')


# ------------------ صفحة عرض المستخدمين ------------------
@admin_bp.route('/users')
@login_required
@admin_required

def dashboard_users():
    conn = get_db_connection()
    cur = conn.cursor()

    # المتصلين الآن – آخر 5 دقائق
    cur.execute("""
        SELECT email, username, ip, user_agent, created_at 
        FROM user_logs 
        WHERE created_at >= NOW() - INTERVAL '5 minutes'
        ORDER BY created_at DESC
    """)
    online_users = cur.fetchall()

    # غير المتصلين
    cur.execute("""
        SELECT email, username, ip, user_agent, created_at 
        FROM user_logs 
        WHERE created_at < NOW() - INTERVAL '5 minutes'
        ORDER BY created_at DESC
    """)
    offline_users = cur.fetchall()

    # إحصائيات آخر ظهور
    stats = {}

    cur.execute("SELECT COUNT(*) FROM user_logs WHERE created_at >= NOW() - INTERVAL '1 day'")
    stats["day"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM user_logs WHERE created_at >= NOW() - INTERVAL '7 days'")
    stats["week"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM user_logs WHERE created_at >= NOW() - INTERVAL '30 days'")
    stats["month"] = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        'dashboard/users_dashboard.html',
        online_users=online_users,
        offline_users=offline_users,
        stats=stats
    )
from app.routes.admin import users, visits, services, library
