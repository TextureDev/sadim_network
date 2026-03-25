# visits
from flask import session, render_template, request, redirect, url_for, flash
from datetime import datetime
from app.routes.admin.admin import admin_bp
from utlis.login_required import login_required
from utlis.permissions import admin_required
from werkzeug.utils import secure_filename
import os
from app.routes.shared import UPLOAD_FOLDER, allowed_file, BASE_DIR
from app.models.visitor_logs import visitor_logs


# ------------------ صفحة لوحة التحكم الرئيسية ------------------


@admin_bp.before_request
def log_visitors():
    # تجاهل كل الملفات الثابتة
    if request.path.startswith('/static/'):
        return
    
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    path = request.path

    visitor_logs.log_visit(ip, user_agent, path)
#------------------ صفحة عرض الزيارات ------------------
@admin_bp.route('/')
@login_required
@admin_required
def dashboard_home():
    total_visits = visitor_logs.get_visit_count()
    visits = visitor_logs.get_all_visits()

    return render_template(
        'dashboard/dashboard_home.html',
        total_visits=total_visits,
        visits=visits
    )
# ------------------ حذف جميع الزيارات ------------------
@admin_bp.route('/delete_visits', methods=['POST'])
@login_required
@admin_required

def delete_visits():
     
    visitor_logs.delete_all_visits()
    flash('✅ تم حذف جميع الزيارات بنجاح!', 'success')
    return redirect(url_for('admin.dashboard_home'))