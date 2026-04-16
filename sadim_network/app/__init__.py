from flask import Flask, render_template
from app import config
from app.limiter import limiter

app = Flask(__name__)
app.config.from_object('app.config.settings')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 ميجا
limiter.init_app(app)

from app.routes.index import main_bp
from app.routes.errors import errors_bp

from app.routes.admin.admin import admin_bp
from app.routes.loding import loading_bp
from app.routes.register import register_bp
from app.routes.apis.chatbot_api import bot_bp
from app.routes.LIBRARY_SADIM.Agatha_Christie import Library_Agatha_bp
from app.routes.admin.profile import profile_bp
#blueprint
app.register_blueprint(loading_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(profile_bp)

app.register_blueprint(errors_bp)
app.register_blueprint(main_bp)
app.register_blueprint(register_bp)
app.register_blueprint(bot_bp)
app.register_blueprint(Library_Agatha_bp)
