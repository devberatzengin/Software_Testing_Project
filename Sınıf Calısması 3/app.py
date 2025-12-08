import time
import sys
import os
import socket
import threading
import json
from random import choice

# -ansi color codes
RESET = '\033[0m'
BLUE = '\033[94m'      # Jerry (J) - Parlak Mavi
MAGENTA = '\033[35m'   # Tuffy (T) - Magenta
GRAY_WALL = '\033[37m' # Duvarlar (#) - Gri/Beyaz Ön Plan Rengi
GREEN = '\033[92m'     # Peynir (C) - Parlak Yeşil
YELLOW = '\033[93m'    # Geçilen Yol (*) - Parlak Sarı
WHITE = '\033[97m'     # Boş Yol ( . ) - Parlak Beyaz/Gri
RED = '\033[99m'     # Boş Yol ( . ) - Parlak Beyaz/Gri

# imports 
try:
    import tty, termios
except ImportError:
    pass

# networks settings
HOST = '0.0.0.0'
PORT = 65432
BUFFER_SIZE = 4096

#maze
maze_matrix = [
    ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'], 
    ['#', '.', '.', '.', '.', '#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'], 
    ['#', '#', '#', '#', '.', '#', '.', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '.', '#', '#'], 
    ['#', '.', '.', '.', '.', '#', '.', '#', '.', '.', '.', '.', '.', '.', '.', '.', '#', '.', '.', '#'], 
    ['#', '.', '#', '#', '#', '#', '.', '#', '.', '#', '#', '#', '#', '#', '#', '.', '#', '#', '.', '#'], 
    ['#', '.', '#', '.', '.', '.', '.', '.', '.', '#', '.', '.', '.', '.', '#', '.', '.', '#', '.', '#'], 
    ['#', '.', '#', '.', '#', '#', '#', '#', '.', '#', '.', '#', '#', '#', '#', '#', '.', '#', '.', '#'], 
    ['#', '.', '.', '.', '#', '.', '.', '.', '.', '#', '.', '#', '.', '.', '.', '.', '.', '#', '.', '#'], 
    ['#', '#', '#', '.', '#', '.', '#', '#', '#', '#', '.', '#', '.', '#', '#', '#', '#', '#', '.', '#'], 
    ['#', '.', '.', '.', '.', '.', '#', '.', '.', '.', '.', '.', '.', '#', '.', '.', '.', '.', '.', '#'], 
    ['#', '.', '#', '#', '#', '#', '#', '.', '#', '#', '#', '#', '#', '#', '.', '#', '#', '#', '#', '#'], 
    ['#', '.', '#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#', '.', '.', '.', '#'], 
    ['#', '.', '#', '.', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '.', '#', '.', '#', '#', '#'], 
    ['#', '.', '.', '.', '#', '.', '.', '.', '.', '.', '.', '.', '.', '#', '.', '#', '.', '.', '.', '#'], 
    ['#', '#', '#', '#', '#', '.', '#', '#', '#', '#', '#', '#', '.', '#', '.', '#', '#', '#', '.', '#'], 
    ['#', '.', '.', '.', '.', '.', '#', '.', '.', '.', '.', '.', '.', '#', '.', '.', '.', '#', '.', '#'], 
    ['#', '.', '#', '#', '#', '#', '#', '.', '#', '#', '#', '#', '#', '#', '#', '#', '.', '#', '.', '#'], 
    ['#', '.', '.', '.', '.', '.', '.', '.', '#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'], 
    ['#', '#', '.', '#', '#', '#', '#', '#', '#', '.', '#', '#', '#', '#', '#', '#', '#', '#', 'C', '#'], 
    ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#']
]

GRID_HEIGHT = len(maze_matrix)
GRID_WIDTH = len(maze_matrix[0])

PLAYER_LOCATIONS = {
    "Jerry": [1, 1],
    "Tuffy": [18, 9] 
}
PLAYER_COLORS = {
    "Jerry": BLUE,
    "Tuffy": MAGENTA
}
CHEESE_LOCATION = [18, 18]

# for one user play
jerrys_location = PLAYER_LOCATIONS["Jerry"] 
indicator = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)] 
JERRY_TRAIL = {} 
is_game_over = False


# 0 Ai debuger, 1 One Player, 2 server, 3 client
GAME_MODE = 2
show_indicator = 0 # shows indicator for cell's counts. 1 means open

client_connections = [] 


# theese cordinates in maze ? 
def check_coordinates(x_cor, y_cor):
    if not (0 <= x_cor < GRID_HEIGHT and 0 <= y_cor < GRID_WIDTH):
        return False
    return maze_matrix[x_cor][y_cor] != '#'

# returns next cell's value and cooridnates
def get_next_location(player_name, current_loc, command):
    r, c = current_loc
    new_r, new_c = r, c

    if command == 'W': new_r -= 1
    elif command == 'S': new_r += 1
    elif command == 'A': new_c -= 1
    elif command == 'D': new_c += 1
    else: return None

    if check_coordinates(new_r, new_c):
        return (0, new_r, new_c) 
    else:
        return None

def complete_indicator(indicator, matrix):
    global JERRY_TRAIL
    JERRY_TRAIL = {} 
    
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            indicator[i][j] = 0 
            
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            if matrix[i][j] == '#':
                indicator[i][j] = '#'
            if i == PLAYER_LOCATIONS["Jerry"][0] and j == PLAYER_LOCATIONS["Jerry"][1]:
                indicator[i][j] = 'J'
            elif i == PLAYER_LOCATIONS["Tuffy"][0] and j == PLAYER_LOCATIONS["Tuffy"][1] and GAME_MODE == 2:
                 indicator[i][j] = 'T'
            elif matrix[i][j] == 'C':
                 indicator[i][j] = 'C'

# moves jerry to new cell and updates indicator values
def move_jerry_to(next_road, player_name="Jerry"):
    global is_game_over, JERRY_TRAIL
    
    if next_road:
        old_r, old_c = PLAYER_LOCATIONS[player_name]

        new_r, new_c = next_road[1], next_road[2]
        
        old_key = (old_r, old_c)
        if maze_matrix[old_r][old_c] != 'C':
            current_count = JERRY_TRAIL.get(old_key, 0)
            new_count = current_count + 1
            JERRY_TRAIL[old_key] = new_count
            indicator[old_r][old_c] = new_count # Indicator'a sayıyı yaz

        # checks for cheese        
        if maze_matrix[new_r][new_c] == 'C':
            is_game_over = True
            return True, f"🎉 {player_name} reached the Cheese! Game Over."
        
        indicator[new_r][new_c] = 'J' if player_name == "Jerry" else 'T'
        PLAYER_LOCATIONS[player_name] = [new_r, new_c]
        
        return False, f"Move success: {player_name} -> ({new_r}, {new_c})"
    else:
        return False, "Error: Cannot move in that direction!"

# for ai mode, choose min value in circle cells
def check_next_way(indicator, current_loc):
    possible_moves = []
    r, c = current_loc
    directions = [(-1, 0), (0, -1), (1, 0), (0, 1)] 

    for dr, dc in directions:
        next_r, next_c = r + dr, c + dc
        next_key = (next_r, next_c)
        
        if check_coordinates(next_r, next_c):
            if maze_matrix[next_r][next_c] == 'C':
                return (0, next_r, next_c)
                
            if indicator[next_r][next_c] != 'J':
                visit_count = JERRY_TRAIL.get(next_key, 0)
                possible_moves.append((visit_count, next_r, next_c))

    if not possible_moves:
        return None
    
    return min(possible_moves)

# reads move (wasd)
def get_user_next_location(player_name):

    r, c = PLAYER_LOCATIONS[player_name]
    
    while True:
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            try:
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            cmd = ch.strip().upper()
            sys.stdout.write(cmd + "\n")
            sys.stdout.flush()
        else:
            cmd = input(f"{player_name} (W/A/S/D) or Q: ").strip().upper()

        if cmd == 'Q':
            return 'Q'
        
        next_road = get_next_location(player_name, (r, c), cmd)
        
        if next_road:
            return next_road
        else:
            print("Error: Cannot move in that direction!")
            if GAME_MODE in [2, 3]: # for 2 players mode. Servers needs to know invalid move
                continue
            return None # for one player or ai mode 


def print_display_matrix(current_locations, winner=None):

    global GRAY_WALL, RED, BLUE, MAGENTA, GREEN, YELLOW, WHITE, RESET

    # clears terminal    
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush() 
    
    print("\n--- MAZE PATH ---")
    
    jerry_loc = tuple(current_locations["Jerry"])
    tuffy_loc = tuple(current_locations["Tuffy"])
    
    if winner:
        print(f"!!! WINNER: {winner} !!!")
    elif GAME_MODE in [2, 3]:
        print(f"Jerry (BLUE): {jerry_loc} | Tuffy (MAGENTA): {tuffy_loc}")
    
    for i in range(GRID_HEIGHT):
        line = ""
        for j in range(GRID_WIDTH):
            current_pos = (i, j)
            
            if maze_matrix[i][j] == '#':
                line += f"{GRAY_WALL}# {RESET}" 

            elif maze_matrix[i][j] == 'C':
                line += f"{GREEN}C {RESET}"

            elif current_pos == jerry_loc:
                line += f"{PLAYER_COLORS['Jerry']}J {RESET}"

            elif current_pos == tuffy_loc and (GAME_MODE in [2, 3]):
                line += f"{PLAYER_COLORS['Tuffy']}T {RESET}"

            elif current_pos in JERRY_TRAIL:
                line += f"{YELLOW}* {RESET}" 

            else:
                line += f"{WHITE}. {RESET}" 
                                
        print(line) 
        
    print("-----------------------------\n")
    sys.stdout.flush() # clears tampon area 
    
def print_indicator_debug(indicator): 

    print("\n--- Indicator (DEBUG) ---")
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            value = indicator[i][j]
            display_value = f"{value:<2}"
            
            if value == '#': char_to_print = f"{RED}{display_value}{RESET}"
            elif value == 'J': char_to_print = f"{BLUE}{display_value}{RESET}"
            elif maze_matrix[i][j] == 'C': char_to_print = f"{GREEN}{display_value}{RESET}"
            elif isinstance(value, int) and value > 0: char_to_print = f"{YELLOW}{display_value}{RESET}"
            else: char_to_print = display_value
            
            print(char_to_print, end="")
        print(RESET)
    print("-----------------------------\n")


def update_game_state_network(player_name, next_road):
    
    if not next_road:
        print(f"LOG: {player_name} tried an invalid move.")
        return None, None 

    won, status_msg = move_jerry_to(next_road, player_name)
    winner = player_name if won else None
    
    return winner, status_msg

# server sents status to clients  
def broadcast_game_state(status_msg, winner=None):
    global client_connections
    
    game_state = {
        "status": "update",
        "jerry_loc": PLAYER_LOCATIONS["Jerry"],
        "tuffy_loc": PLAYER_LOCATIONS["Tuffy"],
        "message": status_msg,
        "winner": winner
    }
    message = json.dumps(game_state).encode()
    
    print(f"BROADCAST: {status_msg}")
    
    for conn in client_connections:
        try:
            conn.sendall(message)
        except:
            pass 



def handle_client(conn, addr):

    global client_connections
    
    player_names = ["Jerry", "Tuffy"]
    
    assigned_player = player_names[len(client_connections)]
    client_connections.append(conn)
    
    print(f"Connected: {addr} assigned to {assigned_player}")
    
    # send start positions to client
    conn.sendall(json.dumps({
        "status": "ready",
        "player_id": assigned_player,
        "location": PLAYER_LOCATIONS[assigned_player]
    }).encode())
    
    if len(client_connections) == 2:
        broadcast_game_state("Game Started!")
    
    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data: break
            
            message = json.loads(data.decode())
            command = message.get('command')
            
            if command == 'Q':
                break

            next_road = get_next_location(assigned_player, PLAYER_LOCATIONS[assigned_player], command)
            
            winner, status_msg = update_game_state_network(assigned_player, next_road)
            
            broadcast_game_state(status_msg, winner)

            if winner: break

        except Exception as e:
            print(f"Error handling {assigned_player}: {e}")
            break

    client_connections.remove(conn)
    conn.close()

# starts server
def start_server():
    complete_indicator(indicator, maze_matrix)
    print(f"Maze Server starting on {socket.gethostbyname(socket.gethostname())}:{PORT}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(2)
        
        print("Waiting for 2 players to connect...")
        
        while len(client_connections) < 2:
            try:
                conn, addr = s.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
            except KeyboardInterrupt:
                break
        
        # keep server online
        while True:
            time.sleep(1)

if sys.platform.startswith('linux') or sys.platform == 'darwin':
    FD = sys.stdin.fileno()
    try:
        OLD_TERMIOS_SETTINGS = termios.tcgetattr(FD)
    except:
        OLD_TERMIOS_SETTINGS = None
else:
    OLD_TERMIOS_SETTINGS = None

def client_input_handler(sock, player_id):

    is_macos_linux = sys.platform.startswith('linux') or sys.platform == 'darwin'
    
    while True:
        try:
            cmd = None
            if is_macos_linux and OLD_TERMIOS_SETTINGS is not None:
                try:
                    tty.setraw(FD) 
                    ch = sys.stdin.read(1)
                    cmd = ch.strip().upper()
                finally:
                    termios.tcsetattr(FD, termios.TCSADRAIN, OLD_TERMIOS_SETTINGS)
                
                sys.stdout.write(cmd + "\n")
                sys.stdout.flush()

            else: 
                cmd = input(f"{player_id} Move (W/A/S/D) or Q: ").strip().upper()
        
        except EOFError:
            cmd = 'Q'
        except Exception:
            cmd = 'Q'
            
        if cmd in ['W', 'A', 'S', 'D']:
            message = json.dumps({"command": cmd, "player": player_id}).encode()
            sock.sendall(message)
            
        elif cmd == 'Q':
            if is_macos_linux and OLD_TERMIOS_SETTINGS is not None:
                os.system('stty sane') 
            
            message = json.dumps({"command": cmd, "player": player_id}).encode()
            try: sock.sendall(message)
            except: pass
            break


def start_client():
    global JERRY_TRAIL, PLAYER_LOCATIONS


    # enter server ip for max security
    server_ip = get_ip_input()
    
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, PORT))
            print("Connected to server. Waiting for game start...")
            
            my_player_id = None
            
            while True:
                data = s.recv(BUFFER_SIZE)
                if not data: break

                game_state = json.loads(data.decode())
                
                if game_state.get('status') == 'ready':
                    my_player_id = game_state['player_id']
                    print(f"Connected. You are player: {my_player_id}. Control with WASD.")
                    
                    input_thread = threading.Thread(target=client_input_handler, args=(s, my_player_id))
                    input_thread.daemon = True
                    input_thread.start()

                elif game_state.get('status') == 'update':
                    PLAYER_LOCATIONS["Jerry"] = game_state['jerry_loc']
                    PLAYER_LOCATIONS["Tuffy"] = game_state['tuffy_loc']
                    
                    print(f"Server Message: {game_state['message']}")
                    print_display_matrix(PLAYER_LOCATIONS, game_state.get('winner'))
                    
                    if game_state.get('winner'):
                        break

    except Exception as e:
        print(f"Connection error: {e}")
            
    print("Game Over. Client disconnected.")



def get_ip_input():
    print("Enter Server IP (e.g., 192.168.1.X): ", end="", flush=True)
    return sys.stdin.readline().strip()


if __name__ == "__main__":
    
    if GAME_MODE == 2:
        start_server()

    elif GAME_MODE == 3:
        start_client()

    # one player moode
    elif GAME_MODE == 1:
        complete_indicator(indicator, maze_matrix)
        total_move = 0
        
        while not is_game_over:
            print_display_matrix(PLAYER_LOCATIONS)
            
            next_location_tuple = get_user_next_location("Jerry")
            
            if next_location_tuple == 'Q':
                break
            
            total_move+=1
            print(f"\n Total move {total_move} \n")

            won, msg = move_jerry_to(next_location_tuple, "Jerry")
            print(msg)

            if show_indicator == 1:
                print_indicator_debug(indicator)

    # Ai mode
    elif GAME_MODE == 0:
        complete_indicator(indicator, maze_matrix)
        total_move = 0
        
        while not is_game_over:
            print_display_matrix(PLAYER_LOCATIONS)
            
            next_road = check_next_way(indicator, PLAYER_LOCATIONS["Jerry"])
            
            if next_road is None:
                print("\n*** Computer is stuck! ***")
                break
                
            total_move+=1
            print(f"\n Total move {total_move} \n")

            won, msg = move_jerry_to(next_road, "Jerry")
            print(msg)
            
            if show_indicator == 1:
                print_indicator_debug(indicator)
            
            time.sleep(0.05)
            
    print("Game Over.")