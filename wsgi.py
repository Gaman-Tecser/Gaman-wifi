import logging
from app import create_app

app = create_app()

# Ensure Flask app logs go to gunicorn output
gunicorn_logger = logging.getLogger("gunicorn.error")
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)
logging.getLogger("app.blueprints.portal.routes").handlers = gunicorn_logger.handlers
logging.getLogger("app.blueprints.portal.routes").setLevel(logging.INFO)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
