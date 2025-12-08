# server.py
import socket
import threading
import pickle # Used to serialize/deserialize data (board state, moves)

# --- NETWORK & GAME SETTINGS ---
HOST = '0.0.0.0' 
PORT = 65432     

board = [['_'] * 3 for _ in range(3)]
current_turn = 'X' 
clients = [] # Stores client sockets
symbols = {} # Maps client socket to their symbol (X or O)

def check_win(board, symbol):

    lines = []
    lines.extend([board[i] for i in range(3)]) # Rows
    lines.extend([[board[r][c] for r in range(3)] for c in range(3)]) # Columns
    lines.append([board[i][i] for i in range(3)]) # Diagonal 1
    lines.append([board[i][2-i] for i in range(3)]) # Diagonal 2

    for line in lines:
        if line.count(symbol) == 3:
            return True
    return False

def check_draw(board):
    return all('_' not in row for row in board)

def broadcast(data_dict):

    data_to_send = pickle.dumps(data_dict)
    for client in clients:
        try:
            client.sendall(data_to_send)
        except:
            clients.remove(client)

def handle_client(conn, addr, symbol):

    global current_turn
    print(f"[{symbol}] {addr} connected.")
    
    conn.sendall(pickle.dumps({
            'board': board,
            'message': f"Game Started! {current_turn}'s turn.",
            'turn': current_turn,
            'my_symbol': symbol
        }))

    while True:
        try:
            data = conn.recv(1024)
            if not data: break
            
            move_data = pickle.loads(data)
            r, c = move_data['r'], move_data['c']

            if symbol != current_turn:
                conn.sendall(pickle.dumps({'board': board, 'message': "Error: Not your turn.", 'turn': current_turn}))
                continue
            
            if 0 <= r < 3 and 0 <= c < 3 and board[r][c] == '_':
                board[r][c] = symbol
                
                if check_win(board, symbol):
                    broadcast({'board': board, 'message': f"*** Player {symbol} WON! ***", 'game_over': True})
                    break
                elif check_draw(board):
                    broadcast({'board': board, 'message': "*** DRAW! ***", 'game_over': True})
                    break
                else:
                    current_turn = 'O' if current_turn == 'X' else 'X'
                    broadcast({
                        'board': board,
                        'message': f"Turn: {current_turn}",
                        'turn': current_turn
                    })
            else:
                conn.sendall(pickle.dumps({'board': board, 'message': "Error: Invalid or filled cell.", 'turn': current_turn}))

        except Exception as e:
            print(f"Connection error or closed for {symbol}: {e}")
            break

    print(f"[{symbol}] {addr} disconnected.")
    if conn in clients:
        clients.remove(conn)
    conn.close()

def start_server():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows reusing the port quickly
    s.bind((HOST, PORT))
    s.listen(2) 
    print(f"Server listening on {socket.gethostbyname(socket.gethostname())}:{PORT}. Waiting for 2 players...")

    while len(clients) < 2:
        conn, addr = s.accept()
        clients.append(conn)
        
        symbol = 'X' if len(clients) == 1 else 'O'
        
        thread = threading.Thread(target=handle_client, args=(conn, addr, symbol))
        thread.start()
        
    print("Two players connected. Game ON!")

if __name__ == "__main__":
    start_server()