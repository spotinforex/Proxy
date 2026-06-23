import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os, logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    def __init__(self):
        try:
            self.connection = psycopg2.connect(DATABASE_URL)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logging.info("Database connected successfully")
        except psycopg2.Error as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    def close(self):
        self.cursor.close()
        self.connection.close()
        logging.info("Database connection closed")

    def get_business(self, business_name: str = None, registration_number: int = None, owner_name: str = None):
        """Look up a business by name or registration number."""
        try:
            if business_name:
                self.cursor.execute(
                    "SELECT * FROM businesses WHERE LOWER(business_name) = LOWER(%s)",
                    (business_name,)
                )
            elif registration_number:
                self.cursor.execute(
                    "SELECT * FROM businesses WHERE registration_number = %s",
                    (registration_number,)
                )
            elif owner_name:
                self.cursor.execute(
                    "SELECT * FROM businesses WHERE LOWER(owner_name) = LOWER(%s)",
                    (owner_name,)
                )
            return self.cursor.fetchone()
        except psycopg2.Error as e:
            logging.error(f"Error fetching business: {e}")
            return None

    def update_business_status(self, business_id: int, status: str, pending_reason: str = None, expected_date=None):
        """Update registration status of a business."""
        try:
            self.cursor.execute(
                """
                UPDATE businesses
                SET status = %s, pending_reason = %s, expected_date = %s
                WHERE id = %s
                """,
                (status, pending_reason, expected_date, business_id)
            )
            self.connection.commit()
        except psycopg2.Error as e:
            logging.error(f"Error updating business status: {e}")
            self.connection.rollback()

    def create_complaint(self, whatsapp_number: int, message: str, business_name: str, complaint_type: str):
        """Log a new incoming complaint."""
        try:
            self.cursor.execute(
                """
                INSERT INTO complaints (whatsapp_number, message, business_name, complaint_type, status, first_response_at)
                VALUES (%s, %s, %s, %s, 'open', %s)
                RETURNING id
                """,
                (whatsapp_number, message, business_name, complaint_type, datetime.now(timezone.utc))
            )
            self.connection.commit()
            return self.cursor.fetchone()["id"]
        except psycopg2.Error as e:
            logging.error(f"Error creating complaint: {e}")
            self.connection.rollback()
            return None

    def get_complaint(self, complaint_id: int):
        """Fetch a single complaint by ID."""
        try:
            self.cursor.execute("SELECT * FROM complaints WHERE id = %s", (complaint_id,))
            return self.cursor.fetchone()
        except psycopg2.Error as e:
            logging.error(f"Error fetching complaint: {e}")
            return None

    def get_open_complaints(self):
        """Fetch all unresolved complaints."""
        try:
            self.cursor.execute("SELECT * FROM complaints WHERE status != 'resolved' ORDER BY first_response_at ASC")
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            logging.error(f"Error fetching open complaints: {e}")
            return []

    def get_all_complaints_past_month(self):
        """Fetch all complaints from the past month for management reporting."""
        try:
            self.cursor.execute(
                """
                SELECT * FROM complaints
                WHERE first_response_at >= NOW() - INTERVAL '1 month'
                ORDER BY first_response_at DESC
                """
            )
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            logging.error(f"Error fetching complaints for past month: {e}")
            return []

    def get_all_actions_past_month(self):
        """Fetch all actions from the past month for management reporting."""
        try:
            self.cursor.execute(
                """
                SELECT * FROM actions
                WHERE taken_at >= NOW() - INTERVAL '1 month'
                ORDER BY taken_at DESC
                """
            )
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            logging.error(f"Error fetching actions for past month: {e}")
            return []

    def resolve_complaint(self, complaint_id: int, resolution_method: str, notes: str = None):
        """Mark a complaint as resolved."""
        try:
            self.cursor.execute(
                """
                UPDATE complaints
                SET status = 'resolved', resolved_at = %s, resolution_method = %s, notes = %s
                WHERE id = %s
                """,
                (datetime.now(timezone.utc), resolution_method, notes, complaint_id)
            )
            self.connection.commit()
        except psycopg2.Error as e:
            logging.error(f"Error resolving complaint: {e}")
            self.connection.rollback()

    def escalate_complaint(self, complaint_id: int, assigned_to: str, notes: str = None):
        """Escalate a complaint to a staff member."""
        try:
            self.cursor.execute(
                """
                UPDATE complaints
                SET status = 'escalated', assigned_to = %s, notes = %s
                WHERE id = %s
                """,
                (assigned_to, notes, complaint_id)
            )
            self.connection.commit()
        except psycopg2.Error as e:
            logging.error(f"Error escalating complaint: {e}")
            self.connection.rollback()

    def export_complaints(self):
        """Export all complaints for spreadsheet download."""
        try:
            self.cursor.execute("SELECT * FROM complaints ORDER BY first_response_at DESC")
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            logging.error(f"Error exporting complaints: {e}")
            return []

    def log_action(self, complaint_id: int, action_type: str, outcome: str = None, staff_notified: str = None):
        """Record every action Proxy takes on a complaint."""
        try:
            self.cursor.execute(
                """
                INSERT INTO actions (complaint_id, action_type, taken_at, outcome, staff_notified)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (complaint_id, action_type, datetime.now(timezone.utc), outcome, staff_notified)
            )
            self.connection.commit()
        except psycopg2.Error as e:
            logging.error(f"Error logging action: {e}")
            self.connection.rollback()

    def get_actions_for_complaint(self, complaint_id: int):
        """Fetch full action history for a complaint."""
        try:
            self.cursor.execute(
                "SELECT * FROM actions WHERE complaint_id = %s ORDER BY taken_at ASC",
                (complaint_id,)
            )
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            logging.error(f"Error fetching actions: {e}")
            return []
        