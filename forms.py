from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField

class UserDataForm(FlaskForm):
    """Form for collecting user data input."""
    
    user_input = TextAreaField(
        'Enter your data',
        render_kw={
            'placeholder': 'Type your message here...',
            'rows': 4,
            'class': 'form-control'
        }
    )
    
    submit = SubmitField(
        'Submit Data',
        render_kw={'class': 'btn btn-primary'}
    )
