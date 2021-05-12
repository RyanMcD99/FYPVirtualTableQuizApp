from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
import logging
import pandas as pd
from quiz import app
from quiz import database
from quiz.forms import createTeamForm, joinTeamForm, hostForm, createQuizForm
import time


database.clearCollections()
questionNum = 0
qStartTime = 0
socketio = SocketIO(app)
logging.basicConfig(level=logging.DEBUG)

@app.route('/', methods=['GET','POST'])
def logIn():
    if request.method == "POST":
        session['username'] = request.form['username']
        app.logger.info("Username entered: "+ session['username'])
        app.logger.info("Redirecting " + session['username'] + " to team selection")
        return redirect(url_for('teamHome'))
        
        
    return render_template('home.html')

@app.route('/createquiz', methods=['GET'])
def createQuiz():
    create_quiz_form = createQuizForm()
    return render_template('createQuiz.html', create_quiz_form=create_quiz_form)

@app.route('/teamHome', methods=['GET','POST'])
def teamHome():
    create_form = createTeamForm()
    join_form = joinTeamForm()
    host_form = hostForm()
    if request.method == "POST":
        if create_form.create.data and create_form.validate_on_submit():

            if database.teamExists(create_form.teamName.data):
                app.logger.error(session['username'] + ": team already made with name " + create_form.teamName.data)
                return "Team already made", 400
            else:
                session['teamName'] = create_form.teamName.data
                database.createTeam(create_form.teamName.data, session['username'])
                app.logger.info(create_form.teamName.data + " team created, " + session['username'] + " redirected to chatroom")
                return redirect(url_for('chat', teamName=session.get('teamName')))

        if join_form.join.data and join_form.validate_on_submit():

            if not database.teamExists(join_form.teamName.data):
                app.logger.error(session['username'] + ": tried join team " + create_form.teamName.data)
                return "Team not found", 404
            else:
                session['teamName'] = join_form.teamName.data
                database.joinTeam(join_form.teamName.data, session['username'])
                app.logger.info(create_form.teamName.data + " team joined, " + session['username'] + " redirected to chatroom")
                return redirect(url_for('chat', teamName=session.get('teamName')))
        
        if host_form.validate_on_submit():
            return redirect(url_for('host', hostName=session['username']))
    

         
    return render_template('teamHome.html', create_form = create_form, join_form = join_form, host_form=host_form)



@app.route('/chat/<teamName>')
def chat(teamName):
    username = session.get('username','')
    room = database.getRoom(teamName)

    if room and database.isTeamMember(teamName, username):
        return render_template('chatRoom.html', username=username, room=room)
    else:
        return "Room doesn't exist, or no permission", 404



@app.route('/quiz/<teamName>', methods = ['GET', 'POST'])
def quiz(teamName):
    global questionNum
    global qStartTime
    questionList = database.getQuestionsDB()
    if database.getRoom(teamName) and database.isTeamMember(teamName, session['username']):
        if not questionList or questionNum == 6 or questionNum ==0:
            return redirect(url_for('leaderboard', teamName= teamName))    
        questionDic = questionList[0]
        question = questionDic.get('question')
        app.logger.info("Current Question: " + question)
        correct = questionDic.get('correct')
        question = questionDic.get('question')
        answers = questionDic.get('answers')
        genre = questionDic.get('genre')
        if request.method == "POST":
            curr_answer = request.form['answer']
            app.logger.info('Team: ' + teamName + ' chose ' + curr_answer)
            if curr_answer == correct:
                score = round((10 - (time.time()-qStartTime))*100)
                app.logger.info(teamName+ " scored: " + str(score))
                database.updateTeamScore(teamName, score)
                database.addAnswer(teamName, question, curr_answer, score, questionNum)
            else:
                database.addAnswer(teamName, question, curr_answer, 0, questionNum)

            return redirect(url_for('waitForQuestion', teamName=teamName))
        else:
            a1, a2, a3, a4 = answers
            return render_template('question.html', username=session['username'], room=database.getRoom(teamName), 
                                    questionNum = questionNum, question=question, answer1=a1, answer2=a2, answer3=a3, answer4=a4, genre=genre)
    else:
        return "No Permission", 403

@app.route("/waitForQuestion/<teamName>")
def waitForQuestion(teamName):
    if database.getRoom(teamName) and database.isTeamMember(teamName, session['username']):
        return render_template('waitForQuestion.html', room = database.getRoom(teamName), username=session['username'])
    else:
        return "No Permission", 403


@app.route("/hostlobby/<hostName>", methods = ['GET','POST'])
def host(hostName):
    if database.checkForHost():
        if database.isHost(hostName):
            return render_template('host.html', hostName=hostName)
        else:
            return "No permission", 403
    else:
        database.addHost(hostName)
        return redirect(url_for("host", hostName = hostName))



@app.route("/hostquiz/<hostName>", methods = ['GET', 'POST'])
def hostQuiz(hostName):
    global questionNum
        if database.isHost(hostName):
        questionList = database.getQuestionsDB()
        
        if questionNum == 6:
            return render_template('leaderboardHost.html', leaderboard=database.getLeaderboard(),hostName=hostName, buttonText="Next Round")
        if not questionList:
            return render_template('leaderboardHost.html', leaderboard=database.getLeaderboard(),hostName=hostName, buttonText="No More Rounds")
        questionDic = questionList[0]
        

        return render_template('hostQuiz.html', hostName = hostName, question = questionDic.get('question'))
    else:
        return "no permission", 403


@app.route("/leaderboard/<teamName>", methods=['GET'])
def leaderboard(teamName):
    global questionNum
    questionNum = 0
    leaderboard = database.getLeaderboard()
    return render_template("leaderboard.html", leaderboard=leaderboard, teamName=teamName)  



# Quiz timer runs out and alert sent to start next Q
@socketio.on('next question')
def next_question(data):
    global qStartTime
    global questionNum
    qStartTime = time.time()
    questionNum += 1
    # Stop deleting extra Q
    if questionNum != 6:
        database.removeQuestionDB()
    
    socketio.emit('refresh question', {'url' : '/quiz/'})
    app.logger.info('next Q')


# Host sends alert to start quiz, this is emitted to all quiz players and they are 
# redirected to start quiz
@socketio.on('start quiz')
def start_quiz():
    global questionNum
    global qStartTime
    qStartTime = time.time()
    questionNum += 1
    database.addQuestionsDB()
    app.logger.info("Quiz Started")
    socketio.emit('quiz started', {'url' : '/quiz/'})

@socketio.on('end quiz')
def end_quiz():
    database.clearCollections()
    socketio.emit('quiz over', {'url': '/teamHome'})


@socketio.on('join room')
def handle_join_room_event(data):
    app.logger.info(data['username'] + " has joined the room "+ data['room'])
    join_room(data['room'])
    socketio.emit('join room message', data, room=data['room'])

@socketio.on('send message')
def handle_send_message_event(data):
    app.logger.info(data['username'] + " Sent message to room " + data['room'] + ": " + data['message'])
    socketio.emit('receive message', data, room = data['room'])


@socketio.on('team answered')
def handle_send_message_event(data):
    app.logger.info(data['room'] + " answered Q")
    socketio.emit('redirect wait', {'url':'/waitForQuestion/'}, room = data['room'])

@socketio.on('clear leaderboard')
def clear_leaderboard():
    database.clearAnswers()

if __name__ == '__main__':
    socketio.run(app, debug=True, threaded=True)