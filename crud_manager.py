# crud_manager.py
from database import DatabaseManager
from models import Book, User, Admin
from datetime import datetime
# Using bcrypt library
import bcrypt


class CRUDManager:
    def __init__(self):
        self.db = DatabaseManager()  # Connect to database

    # ============= BOOK OPERATIONS =============

    def add_book(self, book, added_by=None):
        """Add a new book to database"""
        query = """INSERT INTO books 
                   (isbn, title, author, publication_year, total_copies, 
                    available_copies, genre, price, description, added_by) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        params = (book.isbn, book.title, book.author, book.publication_year,
                  book.total_copies, book.available_copies, book.genre,
                  book.price, book.description, added_by)
        return self.db.execute_query(query, params)

    def get_book(self, isbn):
        """Get a book by ISBN"""
        query = "SELECT * FROM books WHERE isbn = %s"
        result = self.db.execute_query(query, (isbn,), fetch=True)

        if result and len(result) > 0:
            data = result[0]
            book = Book(data['isbn'], data['title'], data['author'],
                        data['publication_year'], data['total_copies'],
                        data.get('genre'), data.get('price', 0.00),
                        data.get('description', ''))
            book.available_copies = data['available_copies']
            return book
        return None

    def get_all_books(self):
        """Get all books from database"""
        query = "SELECT * FROM books ORDER BY title"
        results = self.db.execute_query(query, fetch=True)

        books = []
        for data in results:
            book = Book(data['isbn'], data['title'], data['author'],
                        data['publication_year'], data['total_copies'],
                        data.get('genre'), data.get('price', 0.00),
                        data.get('description', ''))
            book.available_copies = data['available_copies']
            books.append(book)
        return books

    def update_book(self, isbn, **updates):
        """Update book information"""
        if not updates:
            return False

        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        query = f"UPDATE books SET {set_clause} WHERE isbn = %s"

        values = list(updates.values())
        values.append(isbn)

        return self.db.execute_query(query, values)

    def delete_book(self, isbn):
        """Delete a book from database"""
        # Check if book is currently borrowed
        check_query = """SELECT COUNT(*) as active_borrows FROM transactions 
                        WHERE book_isbn = %s AND return_date IS NULL"""
        result = self.db.execute_query(check_query, (isbn,), fetch=True)

        if result and result[0]['active_borrows'] > 0:
            return False, "Cannot delete: Book is currently borrowed"

        delete_query = "DELETE FROM books WHERE isbn = %s"
        self.db.execute_query(delete_query, (isbn,))
        return True, "Book deleted successfully"

    def search_books(self, title=None, author=None, genre=None, available_only=False):
        """Search books with filters"""
        query = "SELECT * FROM books WHERE 1=1"
        params = []

        if title:
            query += " AND title LIKE %s"
            params.append(f"%{title}%")
        if author:
            query += " AND author LIKE %s"
            params.append(f"%{author}%")
        if genre:
            query += " AND genre = %s"
            params.append(genre)
        if available_only:
            query += " AND available_copies > 0"

        query += " ORDER BY title"
        results = self.db.execute_query(query, params, fetch=True)

        books = []
        for data in results:
            book = Book(data['isbn'], data['title'], data['author'],
                        data['publication_year'], data['total_copies'],
                        data.get('genre'), data.get('price', 0.00),
                        data.get('description', ''))
            book.available_copies = data['available_copies']
            books.append(book)
        return books

    # ============= USER OPERATIONS =============

    def add_user(self, user):
        """Add a new user to database"""
        """Add a new user with SECURE password hashing"""
        # 1. Hash the password
        hashed_password = self._hash_password(user.password)
        query = """INSERT INTO users 
                   (username, password, name, email, phone, role, membership_type, is_active) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        params = (user.username, hashed_password, user.name,
                  user.email, user.phone, user.role,
                  user.membership_type, user.is_active)
        return self.db.execute_query(query, params)

    def _hash_password(self, plain_password):
        """Hash a password for security"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode(), salt)
        return hashed.decode()  # Convert bytes to string for database

    def get_user(self, user_id):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.db.execute_query(query, (user_id,), fetch=True)

        if result and len(result) > 0:
            data = result[0]
            if data['role'] == 'admin':
                return Admin(data['user_id'], data['username'], data['name'],
                             data['email'], data['phone'],
                             data.get('department', 'General'),
                             data['is_active'])
            else:
                return User(data['user_id'], data['username'], data['name'],
                            data['email'], data['phone'], data['role'],
                            data['membership_type'], data['is_active'])
        return None

    def get_user_by_username(self, username):
        """Get user by username (for login)"""
        query = "SELECT * FROM users WHERE username = %s"
        result = self.db.execute_query(query, (username,), fetch=True)

        if result and len(result) > 0:
            data = result[0]
            if data['role'] == 'admin':
                return Admin(data['user_id'], data['username'], data['name'],
                             data['email'], data['phone'],
                             data.get('department', 'General'),
                             data['is_active'])
            else:
                return User(data['user_id'], data['username'], data['name'],
                            data['email'], data['phone'], data['role'],
                            data['membership_type'], data['is_active'])
        return None

    def get_all_users(self):
        """Get all users"""
        query = "SELECT * FROM users ORDER BY name"
        results = self.db.execute_query(query, fetch=True)

        users = []
        for data in results:
            if data['role'] == 'admin':
                user = Admin(data['user_id'], data['username'], data['name'],
                             data['email'], data['phone'],
                             data.get('department', 'General'),
                             data['is_active'])
            else:
                user = User(data['user_id'], data['username'], data['name'],
                            data['email'], data['phone'], data['role'],
                            data['membership_type'], data['is_active'])
            users.append(user)
        return users

    def update_user(self, user_id, **updates):
        """Update user information"""
        if not updates:
            return False

        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        query = f"UPDATE users SET {set_clause} WHERE user_id = %s"

        values = list(updates.values())
        values.append(user_id)

        return self.db.execute_query(query, values)

    def delete_user(self, user_id):
        """Delete a user"""
        # Check if user has active borrowings
        check_query = """SELECT COUNT(*) as active_borrows FROM transactions 
                        WHERE user_id = %s AND return_date IS NULL"""
        result = self.db.execute_query(check_query, (user_id,), fetch=True)

        if result and result[0]['active_borrows'] > 0:
            return False, "Cannot delete: User has active book borrowings"

        delete_query = "DELETE FROM users WHERE user_id = %s"
        self.db.execute_query(delete_query, (user_id,))
        return True, "User deleted successfully"

# Test function


def test_crud():
    print("🧪 Testing CRUD Manager...")
    crud = CRUDManager()

    print("\n📚 Testing BOOK operations:")

    # Test 1: Add a book
    book = Book("978-0132350884", "Clean Code", "Robert C. Martin",
                2008, 5, "Programming", 45.99, "Software craftsmanship")

    book_id = crud.add_book(book, added_by=1)  # Admin with ID 1
    print(f"✅ Added book: {book.title}")

    # Test 2: Get the book back
    retrieved = crud.get_book("978-0132350884")
    if retrieved:
        print(f"✅ Retrieved: {retrieved.title} by {retrieved.author}")

    # Test 3: Get all books
    all_books = crud.get_all_books()
    print(f"✅ Total books in library: {len(all_books)}")

    # Test 4: Search books
    search_results = crud.search_books(author="Robert")
    print(f"✅ Found {len(search_results)} books by 'Robert'")

    # Test 5: Update book
    crud.update_book("978-0132350884", total_copies=8, price=49.99)
    print("✅ Updated book details")

    print("\n👤 Testing USER operations:")

    # Test 6: Get admin user (from your SQL insert)
    admin = crud.get_user(1)  # Should be the admin you inserted
    if admin:
        print(f"✅ Found admin: {admin.name} ({admin.role})")

    # Test 7: Get user by username
    admin_by_username = crud.get_user_by_username("admin")
    if admin_by_username:
        print(f"✅ Found by username: {admin_by_username.name}")

    # Test 8: Get all users
    all_users = crud.get_all_users()
    print(f"✅ Total users: {len(all_users)}")

    print("\n🎉 CRUD tests completed!")
    print("⚠️ Note: Password hashing not implemented yet (will do in authentication.py)")


if __name__ == "__main__":
    test_crud()
