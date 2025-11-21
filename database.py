import mysql.connector
import streamlit as st
from datetime import datetime


class MySQLDatabase:
    def __init__(self):
        try:
            # Get database credentials from Streamlit secrets
            self.connection = mysql.connector.connect(
                host=st.secrets["database"]["host"],
                port=st.secrets["database"]["port"],
                user=st.secrets["database"]["username"],
                password=st.secrets["database"]["password"],
                database=st.secrets["database"]["name"]
            )
            self.cursor = self.connection.cursor()
            self._create_tables()
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            self.connection = None
            self.cursor = None

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Conversations table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_message TEXT,
                    ai_response TEXT,
                    user_name VARCHAR(255),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User preferences table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_name VARCHAR(255),
                    preference_key VARCHAR(255),
                    preference_value TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.connection.commit()
        except Exception as e:
            st.error(f"Table creation failed: {e}")

    def save_conversation(self, user_message, ai_response, user_name):
        """Save conversation to database"""
        try:
            if not self.connection:
                return False

            query = """
                INSERT INTO conversations (user_message, ai_response, user_name)
                VALUES (%s, %s, %s)
            """
            self.cursor.execute(query, (user_message, ai_response, user_name))
            self.connection.commit()
            return True
        except Exception as e:
            st.error(f"Save conversation failed: {e}")
            return False

    def get_conversation_history(self, user_name, limit=5):
        """Get conversation history for a user"""
        try:
            if not self.connection:
                return []

            query = """
                SELECT user_message, ai_response, timestamp 
                FROM conversations 
                WHERE user_name = %s 
                ORDER BY timestamp DESC 
                LIMIT %s
            """
            self.cursor.execute(query, (user_name, limit))
            results = self.cursor.fetchall()

            return [
                {
                    "user_message": row[0],
                    "ai_response": row[1],
                    "timestamp": row[2]
                }
                for row in results
            ]
        except Exception as e:
            st.error(f"Get history failed: {e}")
            return []

    def save_user_preference(self, user_name, key, value):
        """Save user preference"""
        try:
            if not self.connection:
                return False

            query = """
                INSERT INTO user_preferences (user_name, preference_key, preference_value)
                VALUES (%s, %s, %s)
            """
            self.cursor.execute(query, (user_name, key, value))
            self.connection.commit()
            return True
        except Exception as e:
            st.error(f"Save preference failed: {e}")
            return False

    def get_analytics(self):
        """Get basic analytics"""
        try:
            if not self.connection:
                return {}

            analytics = {}

            # Total conversations
            self.cursor.execute("SELECT COUNT(*) FROM conversations")
            analytics['total_conversations'] = self.cursor.fetchone()[0]

            # Unique users
            self.cursor.execute("SELECT COUNT(DISTINCT user_name) FROM conversations")
            analytics['unique_users'] = self.cursor.fetchone()[0]

            # Today's conversations
            self.cursor.execute("SELECT COUNT(*) FROM conversations WHERE DATE(timestamp) = CURDATE()")
            analytics['today_conversations'] = self.cursor.fetchone()[0]

            return analytics
        except Exception as e:
            st.error(f"Analytics failed: {e}")
            return {}

    def close(self):
        """Close database connection"""
        if self.connection:
            self.cursor.close()
            self.connection.close()
