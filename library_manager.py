# library_manager.py
from models import Transaction
from database import DatabaseManager
from datetime import datetime, timedelta


class LibraryManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def borrow_book(self, user_id, book_isbn):
        """Borrow a book for a user"""
        try:
            # Check user exists and is active
            user_query = "SELECT * FROM users WHERE user_id = %s AND is_active = TRUE"
            user_result = self.db_manager.execute_query(
                user_query, (user_id,), fetch=True)
            if not user_result:
                return False, "User not found or inactive"

            # Check book exists and is available
            book_query = "SELECT * FROM books WHERE isbn = %s AND available_copies > 0"
            book_result = self.db_manager.execute_query(
                book_query, (book_isbn,), fetch=True)
            if not book_result:
                return False, "Book not found or not available"

            book = book_result[0]

            # Check user's current borrowings
            borrow_query = """SELECT COUNT(*) as active_borrows FROM transactions 
                             WHERE user_id = %s AND transaction_type = 'borrow' 
                             AND return_date IS NULL"""
            active_borrows = self.db_manager.execute_query(
                borrow_query, (user_id,), fetch=True)[0]['active_borrows']

            user = user_result[0]
            max_books = 5 if user['membership_type'] == 'Premium' else 3

            if active_borrows >= max_books:
                return False, f"Borrowing limit reached. Maximum {max_books} books allowed."

            # Create transaction
            due_date = (datetime.now() + timedelta(days=14)
                        ).strftime('%Y-%m-%d')
            transaction_query = """INSERT INTO transactions 
                                  (user_id, book_isbn, transaction_type, due_date, status) 
                                  VALUES (%s, %s, 'borrow', %s, 'active')"""
            transaction_id = self.db_manager.execute_query(
                transaction_query,
                (user_id, book_isbn, due_date)
            )

            # Update book availability
            update_book_query = "UPDATE books SET available_copies = available_copies - 1 WHERE isbn = %s"
            self.db_manager.execute_query(update_book_query, (book_isbn,))

            return True, f"Book '{book['title']}' borrowed successfully. Due date: {due_date}"

        except Exception as e:
            return False, f"Error borrowing book: {str(e)}"

    def return_book(self, user_id, book_isbn):
        """Return a borrowed book"""
        try:
            # Find active borrow transaction
            transaction_query = """SELECT t.*, b.title 
                                  FROM transactions t
                                  JOIN books b ON t.book_isbn = b.isbn
                                  WHERE t.user_id = %s AND t.book_isbn = %s 
                                  AND t.transaction_type = 'borrow' 
                                  AND t.return_date IS NULL 
                                  ORDER BY t.transaction_date DESC LIMIT 1"""
            transaction_result = self.db_manager.execute_query(
                transaction_query, (user_id, book_isbn), fetch=True
            )

            if not transaction_result:
                return False, "No active borrow transaction found"

            transaction = transaction_result[0]
            transaction_id = transaction['transaction_id']
            book_title = transaction['title']

            # Calculate fine if overdue
            fine_amount = 0.00
            due_date = transaction['due_date']
            return_date = datetime.now().date()

            if due_date and return_date > due_date:
                days_overdue = (return_date - due_date).days
                fine_amount = days_overdue * 2.00  # $2 per day

            # Update transaction
            update_transaction = """UPDATE transactions 
                                   SET return_date = %s, fine_amount = %s, 
                                   status = 'completed' 
                                   WHERE transaction_id = %s"""
            self.db_manager.execute_query(
                update_transaction,
                (return_date, fine_amount, transaction_id)
            )

            # Update book availability
            update_book = "UPDATE books SET available_copies = available_copies + 1 WHERE isbn = %s"
            self.db_manager.execute_query(update_book, (book_isbn,))

            # Add to fines table
            if fine_amount > 0:
                fine_query = """INSERT INTO fines 
                               (user_id, transaction_id, amount, issue_date, status) 
                               VALUES (%s, %s, %s, %s, 'pending')"""
                self.db_manager.execute_query(
                    fine_query,
                    (user_id, transaction_id, fine_amount, return_date)
                )

            message = f"Book '{book_title}' returned successfully."
            if fine_amount > 0:
                message += f" Overdue fine: ${fine_amount:.2f}"

            return True, message

        except Exception as e:
            return False, f"Error returning book: {str(e)}"

    def get_user_transactions(self, user_id):
        """Get all transactions for a user"""
        query = """SELECT t.*, b.title, b.author 
                  FROM transactions t 
                  JOIN books b ON t.book_isbn = b.isbn 
                  WHERE t.user_id = %s 
                  ORDER BY t.transaction_date DESC"""
        return self.db_manager.execute_query(query, (user_id,), fetch=True)

    def get_overdue_books(self):
        """Get all overdue books"""
        query = """SELECT u.name as user_name, u.email, b.title, 
                  t.due_date, DATEDIFF(CURDATE(), t.due_date) as days_overdue
                  FROM transactions t
                  JOIN users u ON t.user_id = u.user_id
                  JOIN books b ON t.book_isbn = b.isbn
                  WHERE t.transaction_type = 'borrow' 
                  AND t.return_date IS NULL 
                  AND t.due_date < CURDATE()"""
        return self.db_manager.execute_query(query, fetch=True)

    def search_books(self, title=None, author=None, genre=None, available_only=False):
        """Search for books with filters"""
        try:
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
            return self.db_manager.execute_query(query, params, fetch=True)

        except Exception as e:
            print(f"Error searching books: {e}")
            return []

    def calculate_fine(self, transaction_id):
        """Calculate fine for a specific transaction"""
        query = """SELECT due_date, return_date, fine_amount 
                  FROM transactions 
                  WHERE transaction_id = %s"""
        result = self.db_manager.execute_query(
            query, (transaction_id,), fetch=True)

        if not result:
            return 0.00

        transaction = result[0]

        if transaction['return_date'] is None and transaction['due_date']:
            # Still borrowed, check if overdue
            if datetime.now().date() > transaction['due_date']:
                days_overdue = (datetime.now().date() -
                                transaction['due_date']).days
                return days_overdue * 2.00

        return transaction.get('fine_amount', 0.00)
