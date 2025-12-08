import random 
import time 

# 0: Two Players, 1 Vs Computer, 2: Network
game_mode= int(input("Game Mode: "))

table = [['_'] * 3 for _ in range(3)]
is_game_over = False
winner = ""
time_mode = False 




def print_table():

    print("\n--- Board Status ---")
    for row in table:
        print(' '.join(row))
    print("--------------------")

def check_game(symbol):
    lines=[]
    
    # horizontal lines
    lines.append([table[0][0],table[0][1],table[0][2]])
    lines.append([table[1][0],table[1][1],table[1][2]])
    lines.append([table[2][0],table[2][1],table[2][2]])
        
    # vertical lines
    lines.append([table[0][0],table[1][0],table[2][0]])
    lines.append([table[0][1],table[1][1],table[2][1]])
    lines.append([table[0][2],table[1][2],table[2][2]])

    # cross lines
    lines.append([table[0][0],table[1][1],table[2][2]])
    lines.append([table[0][2],table[1][1],table[2][0]])

    for line in lines:
        if line.count(symbol) == 3:
            if game_mode==1:
                print("\nComputer Won!")
            else:
                print(f"\n*** Player {symbol} Won! ***")
            return True
            
 
    if all('_' not in row for row in table):
        print("\n*** Draw! ***")
        global winner
        winner = "Draw"
        return True
        
    return False

def check_coordinates(x_cor, y_cor):

    if not (0 <= x_cor < 3 and 0 <= y_cor < 3):
        return False
    return table[x_cor][y_cor] == '_'

def computer_move():

    empty_cells = []
    for r in range(3):
        for c in range(3):
            if table[r][c] == '_':
                empty_cells.append((r, c))
    
    if empty_cells:
        return random.choice(empty_cells)
    else:
        return None

def get_user_move(symbol):

    start_time = time.time()
    while True:
        try:
            if time_mode and time.time() - start_time > 2: 
                print(f"\nTime's up for {symbol}!")
                return None, None 
            
            x_cor = int(input(f"Player {symbol}: Enter X Coordinate (0, 1, 2): "))
            y_cor = int(input(f"Player {symbol}: Enter Y Coordinate (0, 1, 2): "))


            if check_coordinates(x_cor, y_cor):
                return x_cor, y_cor
            else:
                print("Error: Invalid coordinate or cell already filled! Try Again.")
        except ValueError:
            print("Error: Please enter number only.")


if game_mode == 0:
    current_symbol = 'X'
    while not is_game_over:
        print_table()
        
        # get move
        x, y = get_user_move(current_symbol)
        
        # Check for time out 
        if x is None:
            current_symbol = 'O' if current_symbol == 'X' else 'X' # Switch turn after timeout
            continue 

        table[x][y] = current_symbol
        
        if check_game(current_symbol):
            is_game_over = True
            print_table()
            break
        
        # switch turn
        current_symbol = 'O' if current_symbol == 'X' else 'X'

elif game_mode == 1:

    print("You are 'X' Computer is 'O'")
    while not is_game_over:
        print_table()


        print("\nYour turn :")
        x_cor, y_cor = get_user_move('X')
        
        if x_cor is not None:
            table[x_cor][y_cor] = 'X'
        
        if check_game('X'):
            is_game_over = True
            print_table()
            break
        
        if all('_' not in row for row in table):
            is_game_over = True
            print_table()
            break
        
        print_table()
        
        print("\nComputer's turn (O)...")
        ai_move = computer_move()
        
        if ai_move:
            r, c = ai_move
            table[r][c] = 'O'
            
            if check_game('O'):
                is_game_over = True
                print_table()
                break
        
elif game_mode == 2:
    print("Please run server.py on one machine and client.py on the other machines.")

