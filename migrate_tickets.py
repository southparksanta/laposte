import sqlite3

def migrate():
    conn = sqlite3.connect('instance/mncposte_v4.db')
    c = conn.cursor()
    
    # Add column user_id to contact_message
    print("Attempting to add user_id column...")
    c.execute("ALTER TABLE contact_message ADD COLUMN user_id INTEGER")
    print("Added user_id column.")

    try:
        # Add column status to contact_message
        c.execute("ALTER TABLE contact_message ADD COLUMN status VARCHAR(20) DEFAULT 'Open'")
    except sqlite3.OperationalError:
        print("Column status already exists")
        
    # Create ticket_reply table if not exists (SQLAlchemy would do this on startup but let's be sure or handle manual creation if needed, 
    # actually app.py create_all will handle new tables, but migration handles existing ones).
    # Since TicketReply is a NEW table, app.py startup will create it. We only need to migrate existing tables.
    
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
