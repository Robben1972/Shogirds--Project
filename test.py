import sqlite3

def drop_tables_except_users(db_path, tables_to_drop):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for table in tables_to_drop:
            if table.lower() != 'users':
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"Table '{table}' dropped successfully.")
            else:
                print(f"Skipping table '{table}' as it is protected.")

        conn.commit()
        conn.close()
        print("Operation completed successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

db_path = "bot.db"  
tables_to_drop = ["contents", "images", "scheduled_posts", "users"]
drop_tables_except_users(db_path, tables_to_drop)

