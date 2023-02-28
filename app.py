from flask import Flask, json, request
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit
from flask_ngrok import run_with_ngrok
from tic_tac_toe import GameState, GameType, UserType ,TicTacToeGame, User
from connect4 import Connect4, Turn as Connect4Turn, GameState as Connect4GameState

app = Flask(__name__)
socket = SocketIO(app, cors_allowed_origins='*')
CORS(app)
run_with_ngrok(app)

@app.route('/')
def test():
    return 'Hello World!'

@socket.on('createTicTacToeGame')
def create_new_game(user_info):
    new_game = TicTacToeGame()
    new_game.add_user({'id':request.sid, 'name':user_info['name']})
    emit('newGameCreated', {'gameId': new_game.id, 'type':'Tic Tac Toe'}, broadcast=True)
    emit('newGameDetails', { 'id':new_game.id, 'squares':new_game.squares } , to=request.sid)

@socket.on('getExistingTicTacToeGame')
def get_ongoing_game(game_info):
    print(f'\ntrying to fetch game {game_info["id"]}')
    print([game for game in TicTacToeGame._games])
    existing_game = list(filter(lambda game: game.id == int(game_info['id']), TicTacToeGame._games))[0]
    emit('ongoingGameDetails', { 'id':existing_game.id, 'squares':existing_game.squares } , to=request.sid)

@socket.on('createConnect4Game')
def create_new_connect4_game(user_info):
    new_game = Connect4()
    new_game.add_user({'id':request.sid, 'name':user_info['name']})
    emit('newGameCreated', {'gameId': new_game.id, 'type':'Connect4'}, broadcast=True)
    emit('newConnect4GameDetails', { 'id':new_game.id, 'allowed':new_game.allowed, 'filled':new_game.filled, 'winningCircles':new_game.winningCircles } , to=request.sid)

@socket.on('getExistingConnect4Game')
def get_ongoing_connect4_game(game_info):
    print(f'\ntrying to fetch game {game_info["id"]}')
    print([game for game in Connect4._games])
    existing_game = list(filter(lambda game: game.id == int(game_info['id']), Connect4._games))[0]
    emit('ongoingConnect4GameDetails', 
        { 'id':existing_game.id,
         'filled':existing_game.filled, 
         'allowed':existing_game.allowed, 
         'turn':existing_game.turn.value } , to=request.sid)

@socket.on('chat')
def chat(data):
    print(f'recieved chat message:{data["msg"]}')
    socket.emit('chat', {'msg':data['msg']}, broadcast=True)

@socket.on('join')
def join_game():
    user_id = request.sid
    print(user_id)
    emit('joined',{'user_id':user_id})

@socket.on('connect')
def test_connect():
    #global squares
    print(f'connection request recieved from {request.sid}');
    send('connected!')

@socket.on('getAllOngoingGames')
def get_all_ongoing_games():
    print(f'getting all onging games: {Connect4._games}')
    return list(map(lambda x: {'gameId':x.id, 'type':'Tic Tac Toe'}, TicTacToeGame._games)) + list(map(lambda x: {'gameId':x.id, 'type':'Connect4'}, Connect4._games))

@socket.on('move')
def move(move):
    game = TicTacToeGame._games[move['gameId']]
    if game.is_game_over():
        print('game over!')
        emit('gameOver', {'winningSquares':game.winner}, to=request.sid)
        return {'squares':game.squares, 'turn':game.turn.value}
    pos = move['pos']
    game.move(pos)
    if game.winner is not None:
        emit('gameOver', {'winningSquares':game.winner}, broadcast=True)
    emit('opponentMadeMove', {'squares':game.squares, 'turn':game.turn.value}, skip_sid=request.sid, broadcast=True)
    return {'squares':game.squares, 'turn':game.turn.value}

@socket.on('connect4Move')
def make_connect4_move(move):
    
    game = Connect4._games[move['gameId']]
    print(f'turn is ${game.turn}')
    # game changes based on move
    pos = move['cellNumber']
    if(int(pos) in game.allowed and game.filled[int(pos)] == -1):
        game.move(pos)
        if game.is_game_over():
            game.state = Connect4GameState.OVER
            game.calculate_winner()
            emit('connect4gameover', 
                {'winningCircles': game.winningCircles
                    }, broadcast=True)
        else:
            emit('connect4MoveSuccess', {
                'filled':game.filled,
                'allowed':game.allowed,
                'turn':game.turn.value
                }, broadcast = True)
    else:
        print('emitting move not allowed message')
        emit('moveNotAllowed', to=request.sid)


if __name__ == "__main__":
    socket.run(app)
