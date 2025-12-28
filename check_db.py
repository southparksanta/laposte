import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('mncposte_v4.db')
        c = conn.cursor()
        print("Connected to mncposte_v4.db")
        
        # Get info for contact_message
        try:
            c.execute("PRAGMA table_info(contact_message)")
            columns = c.fetchall()
            print("Columns in contact_message:")
            found_user_id = False
            for col in columns:
                print(col)
                if col[1] == 'user_id':
                    found_user_id = True
            
            if found_user_id:
                print(">> user_id column FOUND.")
            else:
                print(">> user_id column NOT FOUND.")
                
        except Exception as e:
            print(f"Error checking table: {e}")
            
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == '__main__':
    check_db()
