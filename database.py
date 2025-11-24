import sqlite3

def init_db():
    conn = sqlite3.connect("santa.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            name TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT,
            wishes TEXT,
            game_id INTEGER,
            FOREIGN KEY (game_id) REFERENCES games(id)
        )
    """)

    conn.commit()
    conn.close()

def add_game(chat_id, name):
    conn = sqlite3.connect("santa.db")
    c = conn.cursor()
    c.execute("INSERT INTO games (chat_id, name) VALUES (?, ?)", (chat_id, name))
    conn.commit()
    conn.close()

def get_games():
    conn = sqlite3.connect("santa.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM games")
    games = c.fetchall()
    conn.close()
    return games

def get_game_by_chat(chat_id):
    conn = sqlite3.connect("santa.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM games WHERE chat_id=?", (chat_id,))
    game = c.fetchone()
    conn.close()
    return game

def add_participant(user_id, username, full_name, wishes, game_id):
    conn = sqlite3.connect("santa.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO participants (user_id, username, full_name, wishes, game_id)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, full_name, wishes, game_id))
    conn.commit()
    conn.close()

def get_participants(game_id):
    conn = sqlite3.connect("santa.db")
    c = conn.cursor()
    c.execute("SELECT id, user_id, username, full_name, wishes FROM participants WHERE game_id=?", (game_id,))
    players = c.fetchall()
    conn.close()
    return players

def delete_participants(game_id):
    conn = sqlite3.connect("santa.db")
    c = conn.cursor()
    c.execute("DELETE FROM participants WHERE game_id=?", (game_id,))
    conn.commit()
    conn.close()

def delete_game(game_id):
    conn = sqlite3.connect("santa.db")
    c = conn.cursor()
    c.execute("DELETE FROM games WHERE id=?", (game_id,))
    c.execute("DELETE FROM participants WHERE game_id=?", (game_id,))
    conn.commit()
    conn.close()
