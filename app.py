import os
import logging
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from forms import UserDataForm, SearchResultsForm
from search_engine import GoogleSearchEngine

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Initialize the search engine
search_engine = GoogleSearchEngine()

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
    
    # Store search query in database if configured
    if database_url:
        try:
            from models import SearchQuery
            search_record = SearchQuery(
                query=query,
                user_agent=request.headers.get('User-Agent', ''),
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            )
            db.session.add(search_record)
            db.session.commit()
        except Exception as e:
            app.logger.warning(f"Failed to store search query: {e}")
    
    # Perform Google search
    search_results = search_engine.search(query, num_results=15)
    
    # Create the search results form for the header search bar
    search_form = SearchResultsForm()
    search_form.q.data = query  # Pre-populate with current query
    
    # Handle search errors
    if 'error' in search_results:
        flash(f"Search error: {search_results['error']}", 'warning')
        return render_template('search_results.html', 
                             query=query, 
                             search_form=search_form, 
                             results=[], 
                             error=search_results['error'])
    
    # Display search results
    return render_template('search_results.html', 
                         query=query, 
                         search_form=search_form, 
                         results=search_results.get('results', []),
                         total_results=search_results.get('total_results', 0))

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

@app.route('/debug-search')
def debug_search():
    """Debug endpoint to test Google search response."""
    # Enable debug for this endpoint in development
    # if not app.debug:
    #     return "Debug mode only", 403
    
    query = request.args.get('q', 'test')
    search_results = search_engine.search(query, num_results=5)
    
    return f"""
    <h1>Debug Search Results</h1>
    <p>Query: {query}</p>
    <pre>{search_results}</pre>
    <hr>
    <a href="/debug-search?q=python">Test with 'python'</a> |
    <a href="/debug-search?q=hello">Test with 'hello'</a> |
    <a href="/">Back to search</a>
    """

# Initialize database tables if database is configured
if database_url:
    with app.app_context():
        # Make sure to import the models here or their tables won't be created
        import models  # noqa: F401
        db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
