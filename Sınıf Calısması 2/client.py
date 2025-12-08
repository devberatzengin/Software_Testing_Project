import socket
import pickle
import sys

# change SERVER_HOST for your local host address
SERVER_HOST = '127.0.0.1' 
SERVER_PORT = 65432

# Prints boards
def print_board(board):
    print("\n--- Board Status ---")
    for row in board:
        print(' '.join(row))
    print("--------------------")

# client function
def start_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((SERVER_HOST, SERVER_PORT))
    except ConnectionRefusedError:
        print(f"Error: Could not connect to the server at {SERVER_HOST}:{SERVER_PORT}. Ensure the server is running.")
        sys.exit()

    my_symbol = None
    game_over = False

    while not game_over:
        try:
            data = s.recv(4096)
            if not data: break

            # gets datas
            game_data = pickle.loads(data)
            current_board = game_data.get('board')
            message = game_data.get('message', 'Board Updated.')
            current_turn = game_data.get('turn')
            game_over = game_data.get('game_over', False)

            # determine player's symbol 
            if my_symbol is None and 'my_symbol' in game_data:
                 my_symbol = game_data['my_symbol']
            
            print_board(current_board)
            if my_symbol:
                print(f"Your Symbol: {my_symbol}")
            print(f"Status: {message}")
            
            if game_over:
                break
            
            is_my_turn = (my_symbol == current_turn)

            # gets indexs from user
            if is_my_turn:
                while True:
                    try:
                        r = int(input("YOUR TURN. Enter X coordinate (0, 1, 2): "))
                        c = int(input("YOUR TURN. Enter Y coordinate (0, 1, 2): "))
                        
                        if 0 <= r < 3 and 0 <= c < 3:
                            move = {'r': r, 'c': c}
                            s.sendall(pickle.dumps(move))
                            break
                        else:
                            print("Invalid coordinate. Try again.")
                    except ValueError:
                        print("Error: Please enter number.")
        
        # raise connection error
        except Exception as e:
            print(f"Connection error: {e}")
            break

    print("Game Finished. Connection closed.")
    s.close()

if __name__ == "__main__":
    start_client()