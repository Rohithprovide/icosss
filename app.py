import os
import logging
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from forms import UserDataForm, SearchResultsForm

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database, relative to the app instance folder
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    # initialize the app with the extension, flask-sqlalchemy >= 3.0.x
    db.init_app(app)

@app.route('/', methods=['GET'])
def index():
    """Homepage with search form."""
    form = UserDataForm()
    return render_template('index.html', form=form)

@app.route('/search', methods=['GET'])
def search():
    """Search results page."""
    query = request.args.get('q', '').strip()
    
    if not query:
        flash('Please enter a search term.', 'warning')
        return redirect(url_for('index'))
    
    # Log the search query
    app.logger.info(f"Search query: {query}")
    
    # Create the search results form for the header search bar
    search_form = SearchResultsForm()
    search_form.q.data = query  # Pre-populate with current query
    
    # For now, we'll just display the search results page
    # You can add actual search logic here later
    return render_template('search_results.html', query=query, search_form=search_form)

@app.route('/autocomplete', methods=['POST'])
def autocomplete():
    """Autocomplete endpoint that fetches suggestions from DuckDuckGo API."""
    q = request.form.get('q') or (request.get_json() or {}).get('q')
    if not q:
        return jsonify(['', []])
    
    try:
        # Make request to DuckDuckGo API
        response = requests.get('https://duckduckgo.com/ac/', 
                              params={'q': q, 'type': 'list'}, 
                              timeout=5)
        
        if response.status_code == 200:
            suggestions = response.json()
            return jsonify([q, suggestions[1] if len(suggestions) > 1 else []])
        else:
            return jsonify([q, []])
    except Exception as e:
        app.logger.error(f"Autocomplete error: {e}")
        return jsonify([q, []])

# Initialize database tables if database is configured
if database_url:
    with app.app_context():
        # Make sure to import the models here or their tables won't be created
        import models  # noqa: F401
        db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
