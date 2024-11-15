from flask import render_template
from app import app, db

@app.errorhandler(404)
def not_found_error(error):
    """Error handler for 404 errors."""
    app.logger.error(f"404 error: page not found")
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    """Error handler for 500 errors."""
    db.session.rollback()
    app.logger.error(f"500 error: internal server error")
    return render_template("500.html"), 500