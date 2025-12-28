
import sqlite3

def migrate():
    conn = sqlite3.connect('instance/mncposte_v4.db')
    cursor = conn.cursor()
    
    # Columns to add (Retry failed one)
    new_columns = [
        ('step3_label', 'TEXT', "Arrivé à Ville d''expédition"),
    ]
    
    for col_name, col_type, default_val in new_columns:
        try:
            cursor.execute(f"ALTER TABLE tracking ADD COLUMN {col_name} {col_type} DEFAULT '{default_val}'")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
