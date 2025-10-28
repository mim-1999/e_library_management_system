# database.py
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


class DatabaseConnection:
    def __init__(self):
        self.connection = None

    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            print("✅ Database connection established successfully!")
            return self.connection
        except Error as e:
            print(f"❌ Error connecting to database: {e}")
            return None

    def disconnect(self):
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Database connection closed.")


class DatabaseManager:
    def __init__(self):
        self.db = DatabaseConnection()
        self.connection = self.db.connect()

    def execute_query(self, query, params=None, fetch=False):
        """
        Execute a SQL query
        - query: SQL string
        - params: Tuple of parameters for the query
        - fetch: If True, returns results. If False, returns last inserted ID
        """
        try:
            # Get results as dictionaries
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                self.connection.commit()
                last_id = cursor.lastrowid
                cursor.close()
                return last_id

        except Error as e:
            print(f"❌ Database error: {e}")
            self.connection.rollback()  # Undo changes if error
            return None

    def test_connection(self):
        """Test if database connection works"""
        if self.connection and self.connection.is_connected():
            print("✅ Database connection is active!")
            return True
        else:
            print("❌ Database connection failed!")
            return False

# Test function


def test_database():
    """Test the database connection and basic operations"""
    print("🧪 Testing Database Connection...")

    db = DatabaseManager()

    if db.test_connection():
        # Test a simple query
        result = db.execute_query("SELECT 1 as test", fetch=True)
        if result:
            print("✅ Database query test successful!")
        else:
            print("❌ Database query test failed!")
    else:
        print("❌ Database connection test failed!")


if __name__ == "__main__":
    test_database()
