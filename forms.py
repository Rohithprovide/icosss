from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField

class UserDataForm(FlaskForm):
    """Form for search input on homepage."""
    
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

class SearchResultsForm(FlaskForm):
    """Form for search input on search results page."""
    
    q = StringField(
        'Search',
        render_kw={
            'placeholder': '',
            'class': 'results-search'
        }
    )
    
    submit = SubmitField(
        'Search',
        render_kw={'class': 'btn btn-primary'}
    )
