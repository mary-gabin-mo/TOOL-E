
import sys
import os

# Add the Server directory to sys.path explicitly
server_dir = os.path.dirname(os.path.abspath(__file__))
if server_dir not in sys.path:
    sys.path.append(server_dir)

from sqlalchemy import text
from app.database import engine_tools

def reset_database():
    print("WARNING: This will delete ALL transactions and reset tool quantities.")
    user_input = input("Are you sure you want to proceed? (y/n): ")
    if user_input.lower() != 'y':
        print("Aborted.")
        return

    try:
        # Use a connection (engine.connect()) rather than begin() for TRUNCATE if needed,
        # but SQLAlchemy usually handles execution fine.
        with engine_tools.connect() as conn:
            # 1. Reset Transactions Table
            print("Resetting transactions table...")
            # We disable foreign key checks temporarily just in case, though usually fine for child table
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            conn.execute(text("TRUNCATE TABLE transactions;"))
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            
            # 2. Reset Tools Table
            print("Resetting tools quantities to 5...")
            conn.execute(text("""
                UPDATE tools 
                SET total_quantity = 5, 
                    available_quantity = 5,
                    consumed_quantity = 0,
                    current_status = 'Available'
            """))
            conn.commit()
            
        print("Database reset successfully.")

    except Exception as e:
        print(f"Error resetting database: {e}")

if __name__ == "__main__":
    reset_database()
