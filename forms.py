from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class UserDataForm(FlaskForm):
    """Form for collecting user data input."""
    
    user_input = TextAreaField(
        'Enter your data',
        validators=[
            DataRequired(message='Please enter some data.'),
            Length(min=1, max=500, message='Data must be between 1 and 500 characters.')
        ],
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
