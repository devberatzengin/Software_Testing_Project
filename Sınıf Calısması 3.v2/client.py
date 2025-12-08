import sys
import os
import socket
import threading
import json
import time
from common import PORT, BUFFER_SIZE, PLAYER_LOCATIONS, JERRY_TRAIL, \
                   print_display_matrix, get_ip_input, restore_terminal_settings, \
                   FD, OLD_TERMIOS_SETTINGS
# common.py'den termios ve tty'yi tekrar import et
try:
    import tty, termios
except ImportError:
    pass

# Kullanıcı girdilerini (WASD) okuyan thread
def client_input_handler(sock, player_id):

    is_macos_linux = sys.platform.startswith('linux') or sys.platform == 'darwin'
    
    while True:
        cmd = None
        try:
            if is_macos_linux and OLD_TERMIOS_SETTINGS is not None:
                try:
                    # Raw moda geç
                    tty.setraw(FD) 
                    ch = sys.stdin.read(1)
                    cmd = ch.strip().upper()
                finally:
                    # Eski ayarlara dön
                    termios.tcsetattr(FD, termios.TCSADRAIN, OLD_TERMIOS_SETTINGS)
                
                # Komutu ekrana yazdır
                sys.stdout.write(cmd + "\n")
                sys.stdout.flush()

            else: 
                # Windows veya tty kullanılamayan diğer sistemler
                cmd = input(f"{player_id} Move (W/A/S/D) or Q: ").strip().upper()
        
        except EOFError:
            cmd = 'Q'
        except Exception:
            cmd = 'Q'
            
        if cmd in ['W', 'A', 'S', 'D']:
            # Komutu sunucuya gönder
            message = json.dumps({"command": cmd, "player": player_id}).encode()
            try: sock.sendall(message)
            except: pass
            
        elif cmd == 'Q':
            # Çıkışta terminal ayarlarını düzelt
            restore_terminal_settings() 
            
            message = json.dumps({"command": cmd, "player": player_id}).encode()
            try: sock.sendall(message)
            except: pass
            break


def start_client():
    global JERRY_TRAIL, PLAYER_LOCATIONS

    # Server IP'sini al
    server_ip = get_ip_input()
    
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, PORT))
            print("Connected to server. Waiting for game start...")
            
            my_player_id = None
            
            while True:
                # Sunucudan veri al
                data = s.recv(BUFFER_SIZE)
                if not data: break

                game_state = json.loads(data.decode())
                
                if game_state.get('status') == 'ready':
                    # Oyuncu kimliğini al
                    my_player_id = game_state['player_id']
                    print(f"Connected. You are player: {my_player_id}. Control with WASD.")
                    
                    # Kullanıcı girdisi için ayrı bir thread başlat
                    input_thread = threading.Thread(target=client_input_handler, args=(s, my_player_id))
                    input_thread.daemon = True
                    input_thread.start()

                elif game_state.get('status') == 'update':
                    # Global konumları ve JERRY_TRAIL'ı güncelle
                    PLAYER_LOCATIONS["Jerry"] = game_state['jerry_loc']
                    PLAYER_LOCATIONS["Tuffy"] = game_state['tuffy_loc']
                    # Server'dan gelen trail bilgisini kullan
                    JERRY_TRAIL = game_state.get('jerry_trail', {}) 
                    
                    print(f"Server Message: {game_state['message']}")
                    # Labirenti çiz
                    print_display_matrix(PLAYER_LOCATIONS, game_state.get('winner'))
                    
                    if game_state.get('winner'):
                        break
                        
                elif game_state.get('status') == 'paused':
                    print(f"Game Paused: {game_state['message']}")


    except ConnectionRefusedError:
        print(f"Connection error: Server at {server_ip}:{PORT} refused the connection. Is the server running?")
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        restore_terminal_settings() # Çıkışta terminal ayarlarını düzelt
            
    print("Game Over. Client disconnected.")


if __name__ == "__main__":
    start_client()