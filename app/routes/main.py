from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the home page."""
    return render_template('index.html', title="Business Lead Generator")

@main_bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html', title="About") 