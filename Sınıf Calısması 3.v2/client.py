import socket
import threading
import json
import sys
import os
import time
from game_core import (
    PORT, BUFFER_SIZE, PLAYER_LOCATIONS, 
    print_display_matrix, 
    restore_terminal_settings,
    read_single_char, 
    JERRY_TRAIL 
)

# Client için özel mod
GAME_MODE = 3


def client_input_handler(sock, player_id):
    """
    Kullanıcıdan WASD girdisi alır ve anında sunucuya gönderir.
    Girdi okuması için atomik fonksiyon kullanılır.
    """
    while True:
        cmd = None
        
        # Atomik okumayı kullan
        cmd = read_single_char()
        
        if cmd:
            # Ekrana bas
            sys.stdout.write(cmd + "\n")
            sys.stdout.flush()

        if cmd is None:
            time.sleep(0.01) # Hızlı dönmesini engelle
            continue
            
        if cmd in ['W', 'A', 'S', 'D', 'Q']:
            message = json.dumps({"command": cmd, "player": player_id}).encode()
            
            if cmd == 'Q':
                restore_terminal_settings() 
                
            try: 
                sock.sendall(message)
                if cmd == 'Q': break
            except: 
                print("\nServer connection lost. Quitting input handler.")
                break
        
        # Hafif gecikme
        time.sleep(0.005) 
        

def get_ip_input():
    """
    Sunucu IP adresini kullanıcıdan alır (Standart input kullanılır).
    """
    print("Enter Server IP (e.g., 192.168.1.X or 127.0.0.1): ", end="", flush=True)
    return sys.stdin.readline().strip()


def start_client():
    """
    Labirent istemcisini başlatır.
    """
    global PLAYER_LOCATIONS, JERRY_TRAIL
    
    print("--- MAZE CLIENT ---")
    
    try:
        server_ip = get_ip_input()
    except:
        restore_terminal_settings()
        print("\nIP adresi girişi sırasında hata oluştu. Çıkılıyor.")
        return

    if not server_ip:
        print("Sunucu IP adresi girmediniz. Çıkılıyor.")
        return
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, PORT))
            print(f"Connected to server {server_ip}:{PORT}. Waiting for game start...")
            
            my_player_id = None
            
            while True:
                try:
                    data = s.recv(BUFFER_SIZE)
                except ConnectionResetError:
                    print("\nConnection lost: Server closed the connection.")
                    break
                    
                if not data: break

                game_state = json.loads(data.decode())
                
                if game_state.get('status') == 'ready':
                    my_player_id = game_state['player_id']
                    PLAYER_LOCATIONS[my_player_id] = game_state['location']
                    print(f"\nConnected. You are player: {my_player_id}. Control with WASD.")
                    
                    input_thread = threading.Thread(target=client_input_handler, args=(s, my_player_id))
                    input_thread.daemon = True
                    input_thread.start()

                elif game_state.get('status') == 'update':
                    PLAYER_LOCATIONS["Jerry"] = game_state['jerry_loc']
                    PLAYER_LOCATIONS["Tuffy"] = game_state['tuffy_loc']
                    
                    # Client tarafında haritayı gösterme işlevi print_display_matrix'te atlanacaktır.
                    print(f"Server Message: {game_state['message']}")
                    print_display_matrix(PLAYER_LOCATIONS, game_mode=GAME_MODE, winner=game_state.get('winner'))
                    
                    if game_state.get('winner'):
                        break
                
                elif game_state.get('status') == 'full':
                    print(f"Error: {game_state.get('message')}")
                    break

    except ConnectionRefusedError:
        print(f"Connection error: Server at {server_ip}:{PORT} is not available.")
    except Exception as e:
        print(f"Connection error: {e}")
            
    print("Game Over. Client disconnected.")
    restore_terminal_settings()


if __name__ == "__main__":
    start_client()