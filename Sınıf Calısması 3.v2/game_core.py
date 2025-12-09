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
RED = '\033[91m'       # Hata/Uyarı/Kırmızı

# imports 
try:
    import tty, termios
except ImportError:
    pass

# networks settings
HOST = '0.0.0.0'
PORT = 65432
BUFFER_SIZE = 4096

# maze
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

indicator = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)] 
JERRY_TRAIL = {} 
is_game_over = False
show_indicator = 0 
GAME_MODE = 0 # Varsayılan olarak 1 (Tek Kullanıcı) ayarla.
START_TIME = None # Oyun başlama zamanı

# Terminal ayarları için global değişkenler
FD = None
OLD_TERMIOS_SETTINGS = None

if sys.platform.startswith('linux') or sys.platform == 'darwin':
    try:
        FD = sys.stdin.fileno()
        OLD_TERMIOS_SETTINGS = termios.tcgetattr(FD)
    except:
        OLD_TERMIOS_SETTINGS = None


def restore_terminal_settings():
    """Terminal ayarlarını varsayılana döndürür (Mac/Linux için)."""
    global FD, OLD_TERMIOS_SETTINGS
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        if FD is not None and OLD_TERMIOS_SETTINGS is not None:
            try:
                termios.tcsetattr(FD, termios.TCSADRAIN, OLD_TERMIOS_SETTINGS)
            except termios.error:
                pass
            except Exception as e:
                print(f"Uyarı: Terminal ayarlarını geri yüklerken hata oluştu: {e}")
            finally:
                os.system('stty sane') 


def read_single_char():
    """
    Mac/Linux'ta terminal ayarlarını bozmadan tek bir karakter okur (Atomik okuma).
    """
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        try:
            fd = sys.stdin.fileno()
            # Yerel ayarları kaydet
            old_settings = termios.tcgetattr(fd)
            # RAW moda geç
            tty.setraw(fd)
            
            # Karakteri oku
            ch = sys.stdin.read(1)
            return ch.strip().upper()
        except:
            return None
        finally:
            # KRİTİK: Ayarları ANINDA geri yükle.
            if 'old_settings' in locals():
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                except termios.error:
                    restore_terminal_settings() 
    return None 


def check_coordinates(x_cor, y_cor):
    """
    Verilen koordinatların labirent sınırları içinde ve duvar ('#') olup olmadığını kontrol eder.
    """
    if not (0 <= x_cor < GRID_HEIGHT and 0 <= y_cor < GRID_WIDTH):
        return False
    return maze_matrix[x_cor][y_cor] != '#'

def get_next_location(player_name, current_loc, command):
    """
    Verilen komuta göre bir sonraki konumu hesaplar ve geçerliliğini kontrol eder.
    """
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

def complete_indicator(indicator, matrix, current_locations=None, game_mode=0):
    """
    Labirentin güncel durumunu gösterge matrisine işler (Duvarlar, İzler ve Oyuncular).
    """
    global JERRY_TRAIL
    
    # Sıfırlama
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            indicator[i][j] = 0 
            
    locs = current_locations if current_locations else PLAYER_LOCATIONS
    
    # Duvarlar ve Ziyaret Edilen Yollar (JERRY_TRAIL)
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            if matrix[i][j] == '#':
                indicator[i][j] = '#'
            # Ziyaret edilen yerleri (izleri) geri yükle
            elif (i, j) in JERRY_TRAIL:
                indicator[i][j] = JERRY_TRAIL[(i, j)]

    # Peynir ve Oyuncu Konumları
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            if matrix[i][j] == 'C':
                 indicator[i][j] = 'C'
            
            if i == locs["Jerry"][0] and j == locs["Jerry"][1]:
                indicator[i][j] = 'J'
            elif i == locs["Tuffy"][0] and j == locs["Tuffy"][1] and game_mode >= 2: 
                 indicator[i][j] = 'T'


def move_jerry_to(next_road, player_name="Jerry"):
    """
    Oyuncuyu yeni bir hücreye taşır, izi (JERRY_TRAIL) günceller.
    """
    global is_game_over, JERRY_TRAIL
    
    if next_road:
        old_r, old_c = PLAYER_LOCATIONS[player_name]

        new_r, new_c = next_road[1], next_road[2]
        
        # Eski hücrenin ziyaret sayısını artır
        old_key = (old_r, old_c)
        if maze_matrix[old_r][old_c] != 'C':
            current_count = JERRY_TRAIL.get(old_key, 0)
            new_count = current_count + 1
            JERRY_TRAIL[old_key] = new_count

        # Peynir kontrolü        
        if maze_matrix[new_r][new_c] == 'C':
            is_game_over = True
            PLAYER_LOCATIONS[player_name] = [new_r, new_c]
            return True, f"🎉 {player_name} reached the Cheese! Game Over."
        
        # Yeni konumu güncelle
        PLAYER_LOCATIONS[player_name] = [new_r, new_c]
        
        return False, f"Move success: {player_name} -> ({new_r}, {new_c})"
    else:
        return False, "Error: Cannot move in that direction!"

def check_next_way(indicator, current_loc):
    """
    AI modu için etraftaki en az ziyaret edilmiş (veya peynir olan) hücreyi seçer.
    """
    possible_moves = []
    r, c = current_loc
    directions = [(-1, 0), (0, -1), (1, 0), (0, 1)] 

    for dr, dc in directions:
        next_r, next_c = r + dr, c + dc
        next_key = (next_r, next_c)
        
        if check_coordinates(next_r, next_c):
            if maze_matrix[next_r][next_c] == 'C':
                return (0, next_r, next_c)
                
            if indicator[next_r][next_c] not in ['J', 'T']: 
                visit_count = JERRY_TRAIL.get(next_key, 0)
                possible_moves.append((visit_count, next_r, next_c))

    if not possible_moves:
        return None
    
    return min(possible_moves)

def get_user_next_location(player_name):
    """
    Kullanıcıdan WASD girdisi alır. (Tek oyunculu modlar için)
    """
    r, c = PLAYER_LOCATIONS[player_name]
    
    while True:
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            # Atomik okumayı kullan.
            cmd = read_single_char()
            if cmd:
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
            continue

def print_display_matrix(current_locations, game_mode=1, winner=None):
    """
    Labirenti renkli ASCII karakterlerle terminale basar.
    GAME_MODE=3 (Client) ise labirenti basmayı atlar.
    """
    if game_mode == 3: 
        return 

    global GRAY_WALL, RED, BLUE, MAGENTA, GREEN, YELLOW, WHITE, RESET

    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush() 
    
    print("\n--- MAZE PATH ---")
    
    jerry_loc = tuple(current_locations["Jerry"])
    tuffy_loc = tuple(current_locations["Tuffy"])
    
    if winner:
        print(f"!!! WINNER: {winner} !!!")
    elif game_mode >= 2:
        print(f"Jerry (BLUE): {jerry_loc} | Tuffy (MAGENTA): {tuffy_loc}")
    else:
         print(f"Jerry (BLUE): {jerry_loc}")
    
    for i in range(GRID_HEIGHT):
        line = ""
        for j in range(GRID_WIDTH):
            current_pos = (i, j)
            
            if maze_matrix[i][j] == '#':
                line += f"{GRAY_WALL}# {RESET}" 

            elif maze_matrix[i][j] == 'C':
                if current_pos == jerry_loc or current_pos == tuffy_loc:
                    player = "J" if current_pos == jerry_loc else "T"
                    color = PLAYER_COLORS[player]
                    line += f"{color}{player} {RESET}" 
                else:
                    line += f"{GREEN}C {RESET}"

            elif current_pos == jerry_loc:
                line += f"{PLAYER_COLORS['Jerry']}J {RESET}"

            elif current_pos == tuffy_loc and game_mode >= 2: 
                line += f"{PLAYER_COLORS['Tuffy']}T {RESET}"

            elif current_pos in JERRY_TRAIL:
                line += f"{YELLOW}* {RESET}" 

            else:
                line += f"{WHITE}. {RESET}" 
                                
        print(line) 
        
    print("-----------------------------\n")
    sys.stdout.flush() 

def print_indicator_debug(indicator): 
    """
    AI/Debug modu için gösterge matrisini basar.
    """
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


def print_game_over_screen(winner, total_moves, duration):
    """
    Oyun bittiğinde terminale kazanan ekranını basar.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush() 
    
    print("\n" + "="*50)
    print(f"{BLUE if winner == 'Jerry' else MAGENTA}🎉 MAZE RUNNER - GAME OVER 🎉{RESET}".center(60))
    print("="*50 + "\n")
    
    # Kazanan Mesajı
    if winner:
        winner_color = PLAYER_COLORS[winner]
        print(f"🏆 {winner_color}WINNER: {winner}!{RESET}".center(60))
    else:
        print("🛑 GAME ENDED (NO WINNER)".center(60))

    # İstatistikler
    print("\n" + "-"*50)
    print("📊 GAME STATISTICS".center(50))
    print("-"*50)
    print(f"| Total Moves: {total_moves:<33}|")
    
    # Süre formatı
    if duration is not None:
        duration_str = f"{duration:.2f} seconds"
        print(f"| Duration: {duration_str:<32}|")
    
    print("-"*50)
    print("\n")
    sys.stdout.flush()


def start_one_player_mode(game_mode):
    """
    GAME_MODE 1 (Kullanıcı) veya 0 (AI) için oyunu başlatır.
    """
    global is_game_over, PLAYER_LOCATIONS, show_indicator, indicator, START_TIME
    
    PLAYER_LOCATIONS["Jerry"] = [1, 1]
    is_game_over = False
    
    complete_indicator(indicator, maze_matrix)
    total_move = 0
    START_TIME = time.time()
    
    while not is_game_over:
        complete_indicator(indicator, maze_matrix)
        print_display_matrix(PLAYER_LOCATIONS, game_mode=game_mode)
        
        if game_mode == 1:
            next_location_tuple = get_user_next_location("Jerry")
            
            if next_location_tuple == 'Q':
                break
            next_road = next_location_tuple
        
        elif game_mode == 0:
            next_road = check_next_way(indicator, PLAYER_LOCATIONS["Jerry"])
            
            if next_road is None:
                print("\n*** Computer is stuck! ***")
                break
            
            time.sleep(0.05) 
        
        total_move+=1
        print(f"\n Total move: {total_move} \n")

        won, msg = move_jerry_to(next_road, "Jerry")
        print(msg)

        if won:
            END_TIME = time.time()
            duration = END_TIME - START_TIME
            print_game_over_screen("Jerry", total_move, duration)
            break
            
        if show_indicator == 1:
            complete_indicator(indicator, maze_matrix)
            print_indicator_debug(indicator)
        
    print("Game Over.")


if __name__ == "__main__":
    

    if len(sys.argv) > 1:
        try:
            mode_arg = int(sys.argv[1])
            if mode_arg in [0, 1]:
                GAME_MODE = mode_arg
            else:
                 print("Hata: Geçersiz GAME_MODE argümanı. 0 (AI) veya 1 (Kullanıcı) girin.")
                 sys.exit(1)
        except ValueError:
            print("Hata: Geçersiz GAME_MODE argümanı. 0 (AI) veya 1 (Kullanıcı) girin.")
            sys.exit(1)
            
    if GAME_MODE in [0, 1]:
        start_one_player_mode(GAME_MODE)
    else:
        print("Hata: game_core.py sadece GAME_MODE 0 (AI) veya 1 (Kullanıcı) ile çalışır.")