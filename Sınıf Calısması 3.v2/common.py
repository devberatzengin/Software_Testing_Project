import os
import sys
import socket
import json
import time

# tty, termios sadece linux/macos için gerekli, ortak dosyada kalsın.
try:
    import tty, termios
except ImportError:
    pass


# --- 🌈 ANSI Color Codes ---
RESET = '\033[0m'
BLUE = '\033[94m'      # Jerry (J) - Parlak Mavi
MAGENTA = '\033[35m'   # Tuffy (T) - Magenta
GRAY_WALL = '\033[37m' # Duvarlar (#) - Gri/Beyaz Ön Plan Rengi
GREEN = '\033[92m'     # Peynir (C) - Parlak Yeşil
YELLOW = '\033[93m'    # Geçilen Yol (*) - Parlak Sarı
WHITE = '\033[97m'     # Boş Yol ( . ) - Parlak Beyaz/Gri
RED = '\033[99m'       


# --- 🌐 Network Settings ---
HOST = '0.0.0.0'
PORT = 65432
BUFFER_SIZE = 4096


# --- 🗺️ Maze Data ---
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

# --- 🎯 Global Game State and Indicator ---
PLAYER_LOCATIONS = {
    "Jerry": [1, 1],
    "Tuffy": [18, 9] 
}
PLAYER_COLORS = {
    "Jerry": BLUE,
    "Tuffy": MAGENTA
}
CHEESE_LOCATION = [18, 18]

# Jerry'nin ziyaret izini tutar.
JERRY_TRAIL = {} 

# Debug amaçlı indicator dizisi ve görünürlük ayarı (Sadece local_modes.py kullanır)
indicator = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)] 
show_indicator = 0 # 1 olursa gösterilir

# --- 🖥️ Terminal Settings (Linux/MacOS) ---
if sys.platform.startswith('linux') or sys.platform == 'darwin':
    FD = sys.stdin.fileno()
    try:
        OLD_TERMIOS_SETTINGS = termios.tcgetattr(FD)
    except:
        OLD_TERMIOS_SETTINGS = None
else:
    OLD_TERMIOS_SETTINGS = None

# --- 🛠️ Utility Functions ---

# Koordinatların labirent sınırları içinde ve duvar olup olmadığını kontrol eder.
def check_coordinates(x_cor, y_cor):
    if not (0 <= x_cor < GRID_HEIGHT and 0 <= y_cor < GRID_WIDTH):
        return False
    return maze_matrix[x_cor][y_cor] != '#'

# Komuta göre bir sonraki konumu hesaplar.
def get_next_location(player_name, current_loc, command):
    r, c = current_loc
    new_r, new_c = r, c

    if command == 'W': new_r -= 1
    elif command == 'S': new_r += 1
    elif command == 'A': new_c -= 1
    elif command == 'D': new_c += 1
    else: return None

    # Duvar kontrolü
    if check_coordinates(new_r, new_c):
        # next_road formatı: (is_valid, new_r, new_c)
        return (0, new_r, new_c) 
    else:
        return None

# Jerry'yi yeni hücreye taşır ve JERRY_TRAIL/indicator'ı günceller.
# Ağ modunda SADECE sunucuda çağrılmalıdır.
def move_player_to(next_road, player_name):
    global JERRY_TRAIL, PLAYER_LOCATIONS, indicator
    
    if next_road:
        old_r, old_c = PLAYER_LOCATIONS[player_name]
        new_r, new_c = next_road[1], next_road[2]
        
        won = False

        # Sadece Jerry'nin izini bırakıyoruz
        if player_name == "Jerry":
            old_key = (old_r, old_c)
            # Eğer eski konum Peynir (C) değilse, izi kaydet
            if maze_matrix[old_r][old_c] != 'C':
                current_count = JERRY_TRAIL.get(old_key, 0)
                new_count = current_count + 1
                JERRY_TRAIL[old_key] = new_count
                indicator[old_r][old_c] = new_count 

        # Peynir kontrolü
        if maze_matrix[new_r][new_c] == 'C':
            PLAYER_LOCATIONS[player_name] = [new_r, new_c]
            won = True
            return won, f"🎉 {player_name} reached the Cheese! Game Over."

        # Indicator'da yeni konumu J/T olarak işaretle
        indicator[new_r][new_c] = 'J' if player_name == "Jerry" else 'T' 
        
        PLAYER_LOCATIONS[player_name] = [new_r, new_c]
        
        return won, f"Move success: {player_name} -> ({new_r}, {new_c})"
    else:
        return False, "Error: Cannot move in that direction!"

# Labirenti sıfırlayan ve indicator'ı dolduran fonksiyon (Local modlar için)
def complete_indicator(matrix):
    global JERRY_TRAIL, indicator
    JERRY_TRAIL = {} 
    
    # Indicator'ı sıfırla
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            indicator[i][j] = 0 
            
    # Duvarlar, Oyuncular ve Peynir yerlerini indicator'a işle
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            if matrix[i][j] == '#':
                indicator[i][j] = '#'
            if i == PLAYER_LOCATIONS["Jerry"][0] and j == PLAYER_LOCATIONS["Jerry"][1]:
                indicator[i][j] = 'J'
            elif matrix[i][j] == 'C':
                 indicator[i][j] = 'C'

# Labirenti terminale çizer. (Client/Server görselinde kullanılır)
def print_display_matrix(current_locations, winner=None, game_mode=2):

    global GRAY_WALL, BLUE, MAGENTA, GREEN, YELLOW, WHITE, RESET
    
    # clears terminal    
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush() 
    
    print("\n--- MAZE PATH ---")
    
    jerry_loc = tuple(current_locations["Jerry"])
    tuffy_loc = tuple(current_locations["Tuffy"])
    
    if winner:
        print(f"!!! WINNER: {winner} !!!")
    elif game_mode in [2, 3]: # Network modları
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

            elif current_pos == tuffy_loc and (game_mode in [2, 3]): # Tuffy sadece network modunda gösterilir
                line += f"{PLAYER_COLORS['Tuffy']}T {RESET}"

            elif current_pos in JERRY_TRAIL:
                line += f"{YELLOW}* {RESET}" 

            else:
                line += f"{WHITE}. {RESET}" 
                                
        print(line) 
        
    print("-----------------------------\n")
    sys.stdout.flush() 

# Indicator dizisini renkli ve formatlı olarak debug amaçlı yazdırır (Local modlar için)
def print_indicator_debug(indicator): 

    global GRAY_WALL, RED, BLUE, MAGENTA, GREEN, YELLOW, WHITE, RESET

    print("\n--- Indicator (DEBUG) ---")
    for i in range(GRID_HEIGHT):
        line = ""
        for j in range(GRID_WIDTH):
            value = indicator[i][j]
            # 2 karakter genişliğinde formatla (örn: " 1", "10", " J")
            display_value = f"{value:<2}"
            
            if value == '#': char_to_print = f"{GRAY_WALL}{display_value}{RESET}"
            elif value == 'J': char_to_print = f"{BLUE}{display_value}{RESET}"
            elif value == 'C': char_to_print = f"{GREEN}{display_value}{RESET}"
            elif isinstance(value, int) and value > 0: char_to_print = f"{YELLOW}{display_value}{RESET}"
            else: char_to_print = f"{WHITE}{display_value}{RESET}"
            
            line += char_to_print
        print(line)
    print("-----------------------------\n")

# IP girdisi alma
def get_ip_input():
    print("Enter Server IP (e.g., 192.168.1.X): ", end="", flush=True)
    return sys.stdin.readline().strip()

# Terminal ayarlarını düzeltme
def restore_terminal_settings():
    if (sys.platform.startswith('linux') or sys.platform == 'darwin') and OLD_TERMIOS_SETTINGS is not None:
        try:
            os.system('stty sane') 
        except:
            try:
                termios.tcsetattr(FD, termios.TCSADRAIN, OLD_TERMIOS_SETTINGS)
            except:
                pass