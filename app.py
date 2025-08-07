import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
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
        
        # Redirect to success page with the data
        return redirect(url_for('success', data=user_data))
    
    # Handle form validation errors
    if form.errors:
        for field_name, errors in form.errors.items():
            for error in errors:
                field_display = field_name.replace("_", " ").title() if field_name else "Field"
                flash(f'{field_display}: {error}', 'danger')
    
    return render_template('index.html', form=form)

@app.route('/success')
def success():
    """Success page showing submitted data."""
    user_data = request.args.get('data', '')
    return render_template('success.html', user_data=user_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
