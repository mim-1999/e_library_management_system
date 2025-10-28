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
        self.is_active = is_active           # <-- This enables/disables borrowing
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


class Transaction:
    def __init__(self, transaction_id, user_id, book_isbn, transaction_type):
        # Basic transaction information
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.book_isbn = book_isbn
        self.transaction_type = transaction_type  # 'borrow' or 'return'

        # Timestamp - when transaction occurred
        self.transaction_date = datetime.now()

        # Due date logic - only for borrow transactions
        if transaction_type == 'borrow':
            self.due_date = self.transaction_date + \
                timedelta(days=14)  # 2 weeks
            self.return_date = None  # ← Not returned yet
            self.status = 'active'    # ← Currently borrowed
        else:
            # For return transactions
            self.due_date = None      # ← No due date for returns
            self.return_date = self.transaction_date  # ← Returned now!
            self.status = 'completed'  # ← Immediately completed

        # Fine information
        self.fine_amount = 0.00
        self.fine_paid = False

    def is_overdue(self):
        """Check if a borrow transaction is overdue"""
        if (self.transaction_type == 'borrow' and
            self.return_date is None and  # Book still borrowed
            self.due_date and
                datetime.now() > self.due_date):
            return True
        return False

    def calculate_fine(self):
        """Calculate fine for overdue books"""
        if self.is_overdue():
            days_overdue = (datetime.now().date() - self.due_date.date()).days
            return days_overdue * 2.00  # $2 per day
        return 0.00

    def mark_returned(self):
        """Mark a borrow transaction as returned (only for borrow transactions)"""
        if self.transaction_type == 'borrow' and self.return_date is None:
            self.return_date = datetime.now()
            self.status = 'completed'

            # Calculate fine if overdue
            if self.is_overdue():
                self.fine_amount = self.calculate_fine()

            return True
        return False  # Cannot mark return transactions as returned

    def pay_fine(self, amount_paid):
        """Mark fine as paid"""
        if amount_paid >= self.fine_amount:
            self.fine_paid = True
            return True
        elif amount_paid > 0:
            self.fine_amount -= amount_paid
            return True
        return False

    def get_transaction_info(self):
        """Get formatted transaction information"""
        if self.transaction_type == 'borrow':
            if self.return_date:
                status = "Returned"
                return_info = f" on {self.return_date.strftime('%Y-%m-%d')}"
            else:
                status = "Overdue" if self.is_overdue() else "Active"
                return_info = ""

            due_info = f", Due: {self.due_date.strftime('%Y-%m-%d')}" if self.due_date else ""
            fine_info = f", Fine: ${self.fine_amount:.2f}" if self.fine_amount > 0 else ""

            return f"Borrow - {status}{due_info}{fine_info}{return_info}"
        else:
            # For return transactions
            return f"Return - {self.transaction_date.strftime('%Y-%m-%d %H:%M')} (Book ISBN: {self.book_isbn})"

    def get_days_remaining(self):
        """Get days remaining until due date (for active borrows only)"""
        if (self.transaction_type == 'borrow' and
            self.return_date is None and
                self.due_date):
            days_left = (self.due_date.date() - datetime.now().date()).days
            return max(0, days_left)
        return None  # Not applicable for return transactions

# Test function


def test_models():
    print("🧪 Testing Models...")

    # Test Admin
    admin = Admin(1, "admin_user", "Admin User",
                  "admin@email.com", "123", "IT")
    print(f"✅ Admin is_active: {admin.is_active}")

    # Test Book
    book = Book("123", "Test Book", "Author", 2023, 2)
    print(f"✅ Book available: {book.is_available()}")

    # Test Transaction
    transaction = Transaction(1, 101, "123", "borrow")
    print(f"✅ Transaction type: {transaction.transaction_type}")
    print(f"✅ Due date: {transaction.due_date}")
    print(f"✅ Is overdue: {transaction.is_overdue()}")

    # Test return transaction
    return_transaction = Transaction(2, 101, "123", "return")
    # Should be None
    print(f"✅ Return transaction due date: {return_transaction.due_date}")


if __name__ == "__main__":
    test_models()
