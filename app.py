import os
import logging
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from forms import UserDataForm

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-change-in-production")

@app.route('/', methods=['GET', 'POST'])
def index():
    """Homepage with input form for user data collection."""
    form = UserDataForm()
    
    if form.validate_on_submit():
        # Get the submitted data
        user_data = form.user_input.data
        
        # Log the received data for debugging
        app.logger.info(f"Received user data: {user_data}")
        
        # Flash success message
        flash('Data submitted successfully!', 'success')
        
        # Redirect back to index page
        return redirect(url_for('index'))
    
    # Handle form validation errors
    if form.errors:
        for field_name, errors in form.errors.items():
            for error in errors:
                field_display = field_name.replace("_", " ").title() if field_name else "Field"
                flash(f'{field_display}: {error}', 'danger')
    
    return render_template('index.html', form=form)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
