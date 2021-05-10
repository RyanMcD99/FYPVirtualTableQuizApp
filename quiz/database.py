from pymongo import MongoClient
import pandas as pd
from pprint import pprint

client = MongoClient("<Had sensitive info>")
db = client.fyp
team_collection = db.get_collection("quizTeamsScores")
chatrooms_collection = db.get_collection("chatRoomData")
question_collection = db.get_collection("questions")
answers_collection = db.get_collection("teamAnswers")
host_collection = db.get_collection("hostInformation")
chosen_questions = db.get_collection("chosenQuestions")

# Adds teams to necessary databases
def createTeam(teamName, username):
    team = { 'name': teamName, 'Score': 0 , 'members': [username]}
    room = { 'name': teamName, 'members': [username] }
    teamAnswers = {'name': teamName, 'questions':[], 'answers':[], 'scores':[]}
    team_collection.insert_one(team)
    chatrooms_collection.insert_one(room)
    answers_collection.insert_one(teamAnswers)

# Adds host name to database
def addHost(name):
    host = { 'name': name }
    host_collection.insert_one(host)

# Adds player to teams and rooms
def joinTeam(teamName, username):
    teamData = team_collection.find_one({'name': teamName})
    team_collection.update_one({'_id':teamData.get('_id')}, { '$push': { 'members': username }})
    roomData = chatrooms_collection.find_one({'name': teamName})
    chatrooms_collection.update_one({'_id': roomData.get('_id')}, { '$push': { 'members': username }})

# Returns team members - check if they should be allowed on certain pages
def getTeamMembers(name):
    teamData = team_collection.find_one({'name': name})
    teamMembers = teamData.get('members')
    return teamMembers

# Return team score - leaderboard
def getTeamScore(name):
    teamData = team_collection.find_one({'name': name})
    teamScore = teamData.get('Score')
    return teamScore

# Increase team score
def updateTeamScore(name, score):
    teamData = team_collection.find_one({'name': name})
    currentScore = teamData.get('Score')
    team_collection.update_one({'_id':teamData.get('_id')}, {'$inc': {'Score': score}})

# Check if team is already made or not
def teamExists(teamName):
    if team_collection.count_documents({'name': teamName}, limit = 1):
        return True
    else:
        return False

# Makes sure someone is part of a team - permissions        
def isTeamMember(roomName, username):
    if username in getTeamMembers(roomName):
        return True
    else:
        return False

# Return room
def getRoom(roomName):
    return chatrooms_collection.find_one({'name': roomName})

# Clear all databases - start of new quiz
def clearCollections():
    chatrooms_collection.remove({})
    answers_collection.remove({})
    team_collection.remove({})
    host_collection.remove({})
    chosen_questions.remove({})


# Add questions for quiz to a new collection
def addQuestionsDB():
    randQs = question_collection.aggregate([{ '$match': { 'genre':'General Knowledge' } },
                                            { '$sample': { 'size': 5 } }])
    for doc in randQs:
        chosen_questions.insert_one(doc)
    randQs = question_collection.aggregate([{ '$match': { 'genre':'Sport' } },
                                            { '$sample': { 'size': 5 } }])
    for doc in randQs:
        chosen_questions.insert_one(doc)
    randQs = question_collection.aggregate([{ '$match': { 'genre':'Geography' } },
                                            { '$sample': { 'size': 5 } }])
    for doc in randQs:
        chosen_questions.insert_one(doc)

# Return questions used in quiz
def getQuestionsDB():
    cursorQ = chosen_questions.find()
    questions = []
    for doc in cursorQ:
        questions.append(doc)
    return questions

# Check to see if question DB empty
def checkQuestionDB():
    if chosen_questions.count() == 0:
        return False
    else:
        return True

# Remove a question from database - to cycle through Qs
def removeQuestionDB():
    chosen_questions.delete_one({})

# Add team answer to collection
def addAnswer(teamName, question, answer, score, questionNum):
    teamAnswers = answers_collection.find_one({'name': teamName})
    if len(teamAnswers['scores']) != questionNum:
        answers_collection.update_one({'_id':teamAnswers.get('_id')}, { '$push': 
                                    {'questions': question, 'answers': answer, 'scores':score}})

# Clear answers - new leaderboard
def clearAnswers():
    answers_collection.remove({})
    teamDB = team_collection.find()
    for t in teamDB:
        teamAnswers = {'name': t['name'], 'questions':[], 'answers':[], 'scores':[]}
        answers_collection.insert_one(teamAnswers)


# Create and return leaderboard
def getLeaderboard():
    teamDB = team_collection.find()
    teams = []
    qScores = {'1':[], '2':[], '3':[], '4':[], '5':[]}
    totals = []
    for t in teamDB:
        teams.append(t['name'])
        teamAnswers = answers_collection.find_one({'name':t['name']})
        while len(teamAnswers['scores']) < 5:
            teamAnswers['scores'].append(0)
        qScores['1'].append(teamAnswers['scores'][0])
        qScores['2'].append(teamAnswers['scores'][1])
        qScores['3'].append(teamAnswers['scores'][2])
        qScores['4'].append(teamAnswers['scores'][3])
        qScores['5'].append(teamAnswers['scores'][4])
        totals.append(t['Score'])

    
    lb = pd.DataFrame({'Teams': teams, '1':qScores['1'], '2':qScores['2'], '3':qScores['3'],
                        '4':qScores['4'], '5':qScores['5'], 'Total': totals})

    lb = lb.sort_values(['Total', 'Teams'], ascending=False)
    lb.index = range(1,len(lb)+1)
    return lb


# Check if host has been chosen
def checkForHost():
    if host_collection.count() == 0:
        return False
    else:
        return True

# Check is user is host - permissions
def isHost(name):
    if host_collection.count_documents({'name': name}, limit = 1):
        return True
    else:
        return False

# Used to quickly add genres to database entries
def addGenre():
    question_collection.update_many({"genre":{"$exists":False}}, {"$set":{ "genre": "generalKnowledge"}})

# Used in database testing
# if __name__ == "__main__":
#     addGenre()
    