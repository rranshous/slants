import json
from random import randint

def get_board_data(board):
    with open('boards.json','r') as fh:
        data = json.loads(fh.read())
    board_data = data.get(board)
    return board_data

def create_random_platforms(count=10):
    to_return = []
    for i in xrange(10):
        to_return.append({
            'position':[randint(0,100),randint(0,100)],
            'length':randint(2,30),
            'angle':randint(0,359)
        })
    return to_return
