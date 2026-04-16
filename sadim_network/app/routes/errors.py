from flask import Blueprint, render_template

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)

def not_pound_error(error):
    return render_template('404.html'), 404

@errors_bp.app_errorhandler(429)
def ratelimit_error(e):
    return render_template("429.html"), 429