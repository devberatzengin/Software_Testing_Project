import time
import sys
import os
from random import choice # AI sıkışmasını önlemek için eklendi
# common.py'den gerekli tüm fonksiyonları ve değişkenleri içe aktar
from common import PLAYER_LOCATIONS, JERRY_TRAIL, maze_matrix, \
                   print_display_matrix, get_next_location, move_player_to, \
                   restore_terminal_settings, check_coordinates, \
                   indicator, show_indicator, complete_indicator, print_indicator_debug, \
                   FD, OLD_TERMIOS_SETTINGS
                   
# Linux/MacOS için tty/termios'u import et
try:
    import tty, termios
except ImportError:
    pass


# --- Sadece Yerel Modlar için Yardımcı Fonksiyonlar ---

# Kullanıcı girdisini (WASD) okuyan fonksiyon
def get_user_next_location(player_name):
    
    global OLD_TERMIOS_SETTINGS, FD

    r, c = PLAYER_LOCATIONS[player_name]
    is_macos_linux = sys.platform.startswith('linux') or sys.platform == 'darwin'
    
    while True:
        cmd = None
        try:
            if is_macos_linux and OLD_TERMIOS_SETTINGS is not None:
                # Linux/MacOS için tek tuşla girdi (Enter zorunluluğu yok)
                try:
                    # Terminali raw moda geçir
                    tty.setraw(FD) 
                    ch = sys.stdin.read(1)
                    cmd = ch.strip().upper()
                finally:
                    # Eski ayarlara dön
                    termios.tcsetattr(FD, termios.TCSADRAIN, OLD_TERMIOS_SETTINGS)
                
                # Komutu ekrana yazdır (görünmesi için)
                sys.stdout.write(cmd + "\n")
                sys.stdout.flush()

            else: 
                # Windows veya tty kullanılamayan sistemler için standart input
                cmd = input(f"{player_name} Move (W/A/S/D) or Q: ").strip().upper()
        
        except EOFError:
            cmd = 'Q'
        except Exception:
            cmd = 'Q' # Hata durumunda çıkış varsay
            
        
        if cmd == 'Q':
            return 'Q'
        
        next_road = get_next_location(player_name, (r, c), cmd)
        
        if next_road:
            return next_road
        else:
            print("Error: Cannot move in that direction!")
            # Geçersiz hareketse döngüye devam et (tekrar girdi bekle)
            continue 
        


# AI modu için bir sonraki en iyi yolu (artık rastgelelik içerir) bulan fonksiyon
def check_next_way(current_loc):
    
    best_moves = []
    min_visits = float('inf')
    
    r, c = current_loc
    directions = [(-1, 0), (0, -1), (1, 0), (0, 1)] # Kuzey, Batı, Güney, Doğu

    for dr, dc in directions:
        next_r, next_c = r + dr, c + dc
        next_key = (next_r, next_c)
        
        # Duvar ve labirent sınırları kontrolü common.py'den
        if check_coordinates(next_r, next_c): 
            # Peynir kontrolü (öncelikli)
            if maze_matrix[next_r][next_c] == 'C':
                return (0, next_r, next_c)
                
            # Ziyaret sayısını al
            visit_count = JERRY_TRAIL.get(next_key, 0)
            
            # Eğer bu ziyaret sayısı şu ana kadarki minimumdan azsa
            if visit_count < min_visits:
                min_visits = visit_count
                best_moves = [(visit_count, next_r, next_c)] # Yeni en iyi yollar listesini başlat
            elif visit_count == min_visits:
                best_moves.append((visit_count, next_r, next_c)) # Aynı değere sahip yolları ekle

    if not best_moves:
        return None
    
    # En az ziyaret edilen yollar arasından RASTGELE birini seç
    return min(best_moves)


# --- 🎮 Mod Başlatıcılar ---

# Tek Oyunculu Mod (Manuel Kontrol)
def start_one_player_mode():
    global show_indicator
    is_game_over = False
    total_move = 0
    player_name = "Jerry"

    # Oyunu başlatmadan önce indicator'ı hazırla
    complete_indicator(maze_matrix) 

    print("--- 👤 Single Player Mode Started ---")
    
    try:
        while not is_game_over:
            # Labirenti çiz (game_mode=1 olarak belirterek Tuffy'yi göstermeyiz)
            print_display_matrix(PLAYER_LOCATIONS, game_mode=1)
            
            # Kullanıcıdan girdi al
            next_location_tuple = get_user_next_location(player_name)
            
            if next_location_tuple == 'Q':
                break
            
            total_move += 1
            print(f"\n Total move {total_move} \n")

            # common.py'deki move_player_to'yu kullan (JERRY_TRAIL ve indicator güncellenir)
            won, msg = move_player_to(next_location_tuple, player_name)
            is_game_over = won
            print(msg)

            # Indicator'ı gösterme kontrolü
            if show_indicator == 1: 
                print_indicator_debug(indicator) 
    
    except KeyboardInterrupt:
        print("\nGame interrupted.")
        restore_terminal_settings()

    print("Game Over.")
    restore_terminal_settings()


# AI Çözücü Modu
def start_ai_mode():
    global show_indicator
    is_game_over = False
    total_move = 0
    player_name = "Jerry"

    # Oyunu başlatmadan önce indicator'ı hazırla
    complete_indicator(maze_matrix) 

    print("--- 🤖 AI Solver Mode Started ---")
    
    try:
        while not is_game_over:
            # Labirenti çiz (game_mode=0 olarak belirterek Tuffy'yi göstermeyiz)
            print_display_matrix(PLAYER_LOCATIONS, game_mode=0)
            
            # AI kararı al (en az ziyaret edilen yollar arasından rastgele seçer)
            next_road = check_next_way(PLAYER_LOCATIONS[player_name])
            
            if next_road is None:
                print("\n*** Computer is stuck! ***")
                break
                
            total_move+=1
            print(f"\n Total move {total_move} \n")

            # common.py'deki move_player_to'yu kullan
            won, msg = move_player_to(next_road, player_name)
            is_game_over = won
            print(msg)
            
            # Indicator'ı gösterme kontrolü
            if show_indicator == 1:
                print_indicator_debug(indicator)
            
            time.sleep(0.05) # Hızı ayarlayın
    
    except KeyboardInterrupt:
        print("\nGame interrupted.")
        restore_terminal_settings()

    print("Game Over.")
    restore_terminal_settings()


if __name__ == "__main__":
    
    # Komut satırı argümanı ile modu seçme
    try:
        GAME_MODE = int(sys.argv[1])
    except:
        print("Kullanım: python local_modes.py <0/1>")
        print("0: AI Solver Mode | 1: Single Player Mode (Manuel)")
        sys.exit(1)
        
    if GAME_MODE == 1:
        start_one_player_mode()
    elif GAME_MODE == 0:
        start_ai_mode()
    else:
        print("Geçersiz mod seçimi. Lütfen 0 (AI) veya 1 (Tek Oyunculu) girin.")