from flask import Flask
from config import Config
from routes.main_routes import main_bp
from routes.campaign_routes import campaign_bp
from routes.candidate_routes import candidate_bp
from routes.test_routes import test_bp
from routes.test_public_routes import test_public_bp
from filters import format_datetime

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register custom filters
    app.jinja_env.filters['datetime'] = format_datetime

    # Register blueprints with consistent naming and url_prefix
    app.register_blueprint(main_bp)
    app.register_blueprint(campaign_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(test_public_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 