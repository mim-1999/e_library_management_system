# models.py
from datetime import datetime, timedelta


class Person:
    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone

    def get_info(self):
        return f"Name: {self.name}, Email: {self.email}, Phone: {self.phone}"


class User(Person):
    def __init__(self, user_id, username, name, email, phone, role="user", memebership_type="Standard", is_active=True):
        super().__init__(name, email, phone)
        self.user_id = user_id
        self.username = username
        self.role = role
        self.membership_type = memebership_type
        # <-- This enables/disables borrowing
        self.is_active = is_active
        self.max_books = 5 if memebership_type == "Premium" else 3

    def can_borrow(self, current_borrowed_count):
        return current_borrowed_count < self.max_books and self.is_active

    def get_user_summary(self):
        status = "Active" if self.is_active else "Inactive"
        return f"ID: {self.user_id}, Username: {self.username}, Role: {self.role}, Status: {status}"


class Admin(User):
    def __init__(self, user_id, username, name, email, phone, department="General", is_active=True):
        super().__init__(user_id, username, name, email,
                         phone, "admin", "Premium", is_active)
        self.department = department

    def get_admin_info(self):
        status = "Active" if self.is_active else "Inactive"
        return f"Admin: {self.name}, Department: {self.department}, Status: {status}"


class Book:
    def __init__(self, isbn, title, author, publication_year, total_copies=1, genre=None, price=0.00, description=""):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.publication_year = publication_year
        self.total_copies = total_copies
        self.available_copies = total_copies
        self.genre = genre
        self.price = price
        self.description = description
        # ← This controls if book is in library catalog
        self.is_available_flag = True

    def is_available(self):
        return self.available_copies > 0 and self.is_available_flag

    def borrow_copy(self):
        if self.is_available():
            self.available_copies -= 1
            return True
        return False

    def return_copy(self):
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            return True
        return False

    def get_book_info(self):
        status = "Available" if self.is_available() else "Not Available"
        return f"ISBN: {self.isbn}, Title: {self.title}, Author: {self.author}, Status: {status}"


# Test function
def test_models():
    print("🧪 Testing Models...")

    # Test Admin without is_active (should use default True)
    admin = Admin(1, "admin_user", "Admin User",
                  "admin@email.com", "123", "IT")
    print(f"✅ Admin is_active: {admin.is_active}")  # Should be True
    print(f"✅ Admin can borrow: {admin.can_borrow(0)}")  # Should be True

    # Test Book availability
    book = Book("123", "Test Book", "Author", 2023, 2)
    print(f"✅ Book available: {book.is_available()}")  # Should be True

    # Test the method doesn't cause recursion
    book.borrow_copy()
    # Should still work
    print(f"✅ After borrow, available: {book.is_available()}")


if __name__ == "__main__":
    test_models()
