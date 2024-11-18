from flask import app
from app.routes.campaign_routes import campaign_bp

# ... app initialization ...
app.register_blueprint(campaign_bp) 