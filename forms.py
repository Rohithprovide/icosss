from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField

class UserDataForm(FlaskForm):
    """Form for search input."""
    
    q = StringField(
        'Search',
        render_kw={
            'placeholder': '',
            'class': 'home-search'
        }
    )
    
    submit = SubmitField(
        'Submit Data',
        render_kw={'class': 'btn btn-primary'}
    )
