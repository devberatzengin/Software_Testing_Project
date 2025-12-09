import socket
import threading
import json
import sys
import time
from game_core import (
    HOST, PORT, BUFFER_SIZE, PLAYER_LOCATIONS, maze_matrix,
    indicator, complete_indicator, get_next_location, move_jerry_to, 
    print_display_matrix, print_indicator_debug, show_indicator,
    START_TIME, print_game_over_screen
)

# Server için özel mod
GAME_MODE = 2

# Ağ bağlantıları ve kilit mekanizması
client_connections = [] 
lock = threading.Lock() 
TOTAL_MOVES = 0 # Toplam hamle sayısını takip eder


def update_game_state_network(player_name, next_road):
    """
    Sunucu tarafında oyuncu hareketini günceller ve toplam hamle sayısını artırır.
    """
    global TOTAL_MOVES
    
    won, status_msg = move_jerry_to(next_road, player_name)
    winner = player_name if won else None
    
    # Sadece geçerli hamleler sayılır
    if next_road:
        TOTAL_MOVES += 1
    
    return winner, status_msg

def update_server_display(status_msg, winner=None):
    """
    Sunucu terminalini günceller ve haritayı yeniden çizer.
    """
    complete_indicator(indicator, maze_matrix, current_locations=PLAYER_LOCATIONS, game_mode=GAME_MODE)

    print(f"SERVER LOG: {status_msg}")
    print_display_matrix(PLAYER_LOCATIONS, game_mode=GAME_MODE, winner=winner)
    if show_indicator == 1:
        print_indicator_debug(indicator)


def broadcast_game_state(status_msg, winner=None):
    """
    Oyun durumunu tüm bağlı istemcilere yayınlar ve oyun bittiğinde ekranı basar.
    """
    global client_connections
    
    game_state = {
        "status": "update",
        "jerry_loc": PLAYER_LOCATIONS["Jerry"],
        "tuffy_loc": PLAYER_LOCATIONS["Tuffy"],
        "message": status_msg,
        "winner": winner
    }
    message = json.dumps(game_state).encode()
    
    update_server_display(status_msg, winner)
    
    # Oyun bitti ekranı (Sadece sunucuda gösterilir)
    if winner:
        END_TIME = time.time()
        duration = END_TIME - START_TIME
        print_game_over_screen(winner, TOTAL_MOVES, duration)
        
    connections_to_remove = []
    
    for conn in client_connections:
        try:
            conn.sendall(message)
        except:
            connections_to_remove.append(conn)
    
    with lock:
        for conn in connections_to_remove:
            if conn in client_connections:
                client_connections.remove(conn)


def handle_client(conn, addr):
    """
    Her bir istemci bağlantısını yöneten iş parçacığı.
    """
    global client_connections, START_TIME
    
    player_names = ["Jerry", "Tuffy"]
    assigned_player = None
    
    with lock:
        if len(client_connections) >= 2:
            conn.close()
            return
            
        assigned_player = player_names[len(client_connections)]
        client_connections.append(conn)
    
    print(f"Connected: {addr} assigned to {assigned_player}")
    
    try:
        conn.sendall(json.dumps({
            "status": "ready",
            "player_id": assigned_player,
            "location": PLAYER_LOCATIONS[assigned_player]
        }).encode())
    except:
        with lock:
            if conn in client_connections:
                client_connections.remove(conn)
        conn.close()
        return

    if len(client_connections) == 2:
        # İki oyuncu bağlandığında START_TIME'ı başlat
        START_TIME = time.time()
        broadcast_game_state("Game Started! Jerry starts.")
    
    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data: break
            
            message = json.loads(data.decode())
            command = message.get('command')
            
            if command == 'Q':
                break

            next_road = get_next_location(assigned_player, PLAYER_LOCATIONS[assigned_player], command)
            
            # Global durumu güncelleme ve kilit dışı yayınlama
            if next_road:
                with lock:
                    winner, status_msg = update_game_state_network(assigned_player, next_road)
                
                broadcast_game_state(status_msg, winner)
    
                if winner: break
            else:
                print(f"LOG: {assigned_player} attempted an invalid move: {command}")

        except Exception as e:
            print(f"Error handling {assigned_player}: {e}")
            break

    print(f"Client {assigned_player} disconnected.")
    with lock:
        if conn in client_connections:
            client_connections.remove(conn)
    conn.close()


def start_server():
    """
    Labirent sunucusunu başlatır.
    """
    print("--- MAZE SERVER ---")
    
    try:
        complete_indicator(indicator, maze_matrix, current_locations=PLAYER_LOCATIONS, game_mode=GAME_MODE)
    except TypeError as e:
        print("\n!!! KRİTİK HATA !!!")
        print(f"game_core.py dosyasındaki complete_indicator fonksiyonunun imzası hatalı: {e}")
        print("Lütfen complete_indicator(indicator, matrix, current_locations=None, game_mode=0) imzasını kullandığınızdan emin olun.")
        sys.exit(1)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = '127.0.0.1'

    print(f"Maze Server starting on {local_ip}:{PORT}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, PORT))
        except OSError as e:
            print(f"Hata: Adres zaten kullanılıyor veya başka bir sorun: {e}")
            sys.exit(1)
            
        s.listen(2)
        
        print("Waiting for 2 players to connect...")
        
        update_server_display("Server initialized.")
        
        try:
            while True:
                conn, addr = s.accept()
                
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
                
        except KeyboardInterrupt:
            print("\nServer shutting down.")
        except Exception as e:
            print(f"Server error: {e}")


if __name__ == "__main__":
    start_server()