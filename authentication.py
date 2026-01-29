# authentication.py
import bcrypt
from models import User, Admin
from database import DatabaseManager


class Authentication:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.current_user = None

    def hash_password(self, password):
        # return hashlib.sha256(password.encode()).hexdigest()
        """Hash password using bcrypt (same as in CRUDManager)"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    def verify_password(self, plain_password, hashed_password):
        """Verify password against hash"""
        try:
            # Convert string back to bytes for bcrypt
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            print(f"Password verification error: {e}")
            return False

    def login(self, username, password):
        query = "SELECT * FROM users WHERE username = %s"
        user_data = self.db_manager.execute_query(
            query, (username,), fetch=True)

        if not user_data:
            return None, "User not found"

        user_data = user_data[0]

        # hashed_password = self.hash_password(password)

        # if user_data['password'] != hashed_password:
        #     return None, "Invalid password"
        # Verify password using bcrypt
        if not self.verify_password(password, user_data['password']):
            return None, "Invalid password"

        if not user_data['is_active']:
            return None, "Account is deactivated"

        # Update last login
        update_query = "UPDATE users SET last_login = NOW() WHERE user_id = %s"
        self.db_manager.execute_query(update_query, (user_data['user_id'],))

        # Create appropriate user object
        if user_data['role'] == 'admin':
            self.current_user = Admin(
                user_data['user_id'],
                user_data['username'],
                user_data['name'],
                user_data['email'],
                user_data['phone'],
                user_data.get('department', 'General'),
                user_data['is_active']
            )
        else:
            self.current_user = User(
                user_data['user_id'],
                user_data['username'],
                user_data['name'],
                user_data['email'],
                user_data['phone'],
                user_data['role'],
                user_data['membership_type'],
                user_data['is_active']
            )

        return self.current_user, "Login successful"

    def logout(self):
        self.current_user = None
        return "Logout successful"

    def validate_role(self, required_role):
        if not self.current_user:
            return False
        return self.current_user.role == required_role

    def register_user(self, username, password, name, email, phone, role="user"):
        # Check if username exists
        check_query = "SELECT user_id FROM users WHERE username = %s OR email = %s"
        existing = self.db_manager.execute_query(
            check_query, (username, email), fetch=True)

        if existing:
            return None, "Username or email already exists"

        # Insert new user
        insert_query = """INSERT INTO users (username, password, name, email, phone, role, membership_type, is_active) 
                         VALUES (%s, %s, %s, %s, %s, %s, 'Standard', TRUE)"""
        hashed_pw = self.hash_password(password)
        user_id = self.db_manager.execute_query(insert_query,
                                                (username, hashed_pw, name, email, phone, role))

        if user_id:
            # Get the newly created user
            user_query = "SELECT * FROM users WHERE user_id = %s"
            new_user_data = self.db_manager.execute_query(
                user_query, (user_id,), fetch=True)[0]

            if new_user_data['role'] == 'admin':
                user = Admin(
                    user_id,
                    new_user_data['username'],
                    new_user_data['name'],
                    new_user_data['email'],
                    new_user_data['phone'],
                    new_user_data['role'],
                    new_user_data['membership_type'],
                    new_user_data['is_active']
                )
            else:
                user = User(
                    user_id,
                    new_user_data['username'],
                    new_user_data['name'],
                    new_user_data['email'],
                    new_user_data['phone'],
                    new_user_data['role'],
                    new_user_data['membership_type'],
                    new_user_data['is_active']
                )
            return user, "Registration successful"
        return None, "Registration failed"
        #     return User(user_id, username, name, email, phone, role), "Registration successful"
        # return None, "Registration failed"

# Test function


def test_auth():
    """Test authentication system"""
    print("🧪 Testing Authentication System...")

    from database import DatabaseManager
    db = DatabaseManager()
    auth = Authentication(db)

    # Test 1: Password hashing and verification
    print("\n1. Testing password hashing...")
    password = "mysecret123"
    hashed = auth.hash_password(password)
    print(f"   Password: {password}")
    print(f"   Hashed: {hashed[:30]}...")

    verified = auth.verify_password("mysecret123", hashed)
    print(f"   Correct password verification: {verified}")

    verified = auth.verify_password("wrongpass", hashed)
    print(f"   Wrong password verification: {not verified}")

    # Test 2: User creation flow (simulate registration)
    print("\n2. Testing user registration flow...")
    print("   (This would create a user in the database)")

    print("\n✅ Authentication module is ready!")


if __name__ == "__main__":
    test_auth()
