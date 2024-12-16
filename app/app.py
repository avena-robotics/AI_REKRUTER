from flask import Flask, render_template, session
from config import Config
from routes.main_routes import main_bp
from routes.campaign_routes import campaign_bp
from routes.candidate_routes import candidate_bp
from routes.test_routes import test_bp
from routes.test_public_routes import test_public_bp
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from filters import format_datetime
from services.group_service import get_user_groups
from logger import Logger

APP_VERSION = "1.0.3"  # Define version as a constant

def create_app():
    config = Config.instance()
    
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize logger
    logger = Logger.instance(config)
    
    # Set debug mode from environment variable
    app.debug = config.DEBUG_MODE

    # Register custom filters
    app.jinja_env.filters['format_datetime'] = format_datetime

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(campaign_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(test_public_bp)
    app.register_blueprint(user_bp)

    # Add context processor at app level
    @app.context_processor
    def inject_user_groups():
        if 'user_id' in session:
            logger.debug(f"Context processor called for user_id: {session.get('user_id')}")
            user_groups = get_user_groups(session.get('user_id'))
            return {'user_groups': user_groups}
        return {'user_groups': []}

    @app.context_processor
    def inject_version():
        """Make version available to all templates"""
        return dict(app_version=APP_VERSION)

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(error):
        logger.debug(f"404 error: {str(error)}")
        return render_template('error.html', 
                             error_code=404,
                             error_message="Strona, której szukasz nie istnieje."), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {str(error)}")
        return render_template('error.html',
                             error_code=500,
                             error_message="Wystąpił wewnętrzny błąd serwera."), 500

    return app

app = create_app()

if __name__ == '__main__':
    # Use debug mode from config when running directly
    config = Config.instance()
    app.run(
        port=5000, 
        debug=config.DEBUG_MODE
    )   
