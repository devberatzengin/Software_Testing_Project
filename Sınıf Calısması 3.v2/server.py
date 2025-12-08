import time
import socket
import threading
import json
from common import HOST, PORT, BUFFER_SIZE, PLAYER_LOCATIONS, JERRY_TRAIL, \
                   print_display_matrix, get_next_location, move_player_to, \
                   get_ip_input, restore_terminal_settings

# Bağlı istemci soketlerinin listesi
client_connections = [] 

# Ağ hareketini işleyen ve global durumu güncelleyen fonksiyon (Sadece Server'da)
def update_game_state_network(player_name, next_road):
    
    if not next_road:
        print(f"LOG: {player_name} tried an invalid move.")
        return None, None 

    # Ortak dosyadan move_player_to kullanılıyor
    won, status_msg = move_player_to(next_road, player_name)
    winner = player_name if won else None
    
    return winner, status_msg

# Oyun durumunu tüm bağlı istemcilere yayınlar
def broadcast_game_state(status_msg, winner=None):
    global client_connections
    
    # JERRY_TRAIL'ı da client'lara gönderiyoruz
    game_state = {
        "status": "update",
        "jerry_loc": PLAYER_LOCATIONS["Jerry"],
        "tuffy_loc": PLAYER_LOCATIONS["Tuffy"],
        "message": status_msg,
        "winner": winner,
        "jerry_trail": JERRY_TRAIL
    }
    message = json.dumps(game_state).encode()
    
    # Sunucuda da labirenti çizdirelim
    print_display_matrix(PLAYER_LOCATIONS, winner)
    print(f"BROADCAST: {status_msg}")
    
    # Tüm client'lara gönder
    for conn in client_connections:
        try:
            conn.sendall(message)
        except:
            # Bağlantı koparsa listeden çıkar
            print(f"Client connection lost.")
            client_connections.remove(conn) 


def handle_client(conn, addr):

    global client_connections
    
    player_names = ["Jerry", "Tuffy"]
    
    # Oyuncu atanması. (Daha robust bir atama mekanizması düşünülebilir)
    # Şu anki yapı, ilk bağlanan Jerry, ikinci bağlanan Tuffy olur
    if len(client_connections) < 2:
        assigned_player = player_names[len(client_connections)]
        client_connections.append(conn)
    else:
        # 2 oyuncu doluysa, bağlantıyı reddet
        conn.close()
        print(f"Connection from {addr} refused. Game is full.")
        return


    print(f"Connected: {addr} assigned to {assigned_player}")
    
    # İstemciye başlangıç pozisyonunu ve kimliğini gönder
    conn.sendall(json.dumps({
        "status": "ready",
        "player_id": assigned_player,
        "location": PLAYER_LOCATIONS[assigned_player]
    }).encode())
    
    if len(client_connections) == 2:
        # 2. oyuncu bağlandığında oyunu başlat
        broadcast_game_state("Game Started!")
    
    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data: break
            
            message = json.loads(data.decode())
            command = message.get('command')
            
            if command == 'Q':
                break

            # Komut geçerliyse hareket et
            next_road = get_next_location(assigned_player, PLAYER_LOCATIONS[assigned_player], command)
            
            winner, status_msg = update_game_state_network(assigned_player, next_road)
            
            broadcast_game_state(status_msg, winner)

            if winner: break

        except Exception as e:
            print(f"Error handling {assigned_player}: {e}")
            break

    # İstemci bağlantısı kesilince
    try:
        if conn in client_connections:
            client_connections.remove(conn)
        conn.close()
    except:
        pass

    print(f"Client {assigned_player} disconnected.")
    # Oyun bitmediyse, kalan oyuncuyu bilgilendir
    if not winner and len(client_connections) == 1:
        broadcast_game_state(f"Player {assigned_player} left. Game paused.")


def start_server():
    # Başlangıç labirentini göstermek için bir kerelik çizim
    print_display_matrix(PLAYER_LOCATIONS)
    print(f"Maze Server starting on {socket.gethostbyname(socket.gethostname())}:{PORT}")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(2) # 2 oyuncu kabul eder
            
            print("Waiting for 2 players to connect...")
            
            # Sunucu döngüsü
            while True:
                conn, addr = s.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        restore_terminal_settings() # Çıkışta terminal ayarlarını düzelt


if __name__ == "__main__":
    start_server()