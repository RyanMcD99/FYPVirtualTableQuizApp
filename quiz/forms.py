from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from quiz import database

# Flask forms for teamHome
class createTeamForm(FlaskForm):
    teamName = StringField('Enter team name to create', validators=[DataRequired()])
    create = SubmitField('Create Team')

class joinTeamForm(FlaskForm):
    teamName = StringField('Enter team name to join', validators=[DataRequired()])
    join = SubmitField('Join Team')

class hostForm(FlaskForm):
    host = SubmitField('Host')



# Flask form would be used for creating a quiz
class createQuizForm(FlaskForm):
    quizQuestion = StringField('Enter quiz question', validators=[DataRequired()])
    quizCorrectAnswer = StringField('Enter correct answer', validators=[DataRequired()])
    quizAnswer1 = StringField('Enter first answer option', validators=[DataRequired()])
    quizAnswer2 = StringField('Enter second answer option', validators=[DataRequired()])
    quizAnswer3 = StringField('Enter third answer option', validators=[DataRequired()])
    quizAnswer4 = StringField('Enter fourth answer option', validators=[DataRequired()])
    quizGenre = StringField('Enter question genre', validators=[DataRequired()])
    submitQuestion = SubmitField('Add question to database')