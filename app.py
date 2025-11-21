import streamlit as st
import requests
import json
import time
from datetime import datetime
import re
import os
from database import MySQLDatabase  # Database import

# Configure the page
st.set_page_config(
    page_title="Smart AI Assistant with Database",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API Keys
try:
    SEARCHAPI_KEY = st.secrets["SEARCHAPI_KEY"]
except:
    SEARCHAPI_KEY = "Q7BwdRHT8JBtMVXX2hNo7fcD"


class SmartAIAssistant:
    def __init__(self, searchapi_key):
        self.searchapi_key = searchapi_key
        self.searchapi_url = "https://www.searchapi.io/api/v1/search"
        self.db = MySQLDatabase()  # Database connection

    def search_with_searchapi(self, query):
        """Get real-time information using SearchApi.io"""
        try:
            params = {
                'q': f"{query}",
                'api_key': self.searchapi_key,
                'engine': 'google'
            }

            with st.spinner(f'🔍 Searching for "{query}"...'):
                response = requests.get(self.searchapi_url, params=params)
                data = response.json()

            return self.extract_search_answer(data, query)

        except Exception as e:
            return f"❌ Search error: {str(e)}"

    def extract_search_answer(self, data, query):
        """Extract answer from SearchApi.io response"""
        try:
            # Try to get knowledge graph first
            if 'knowledge_graph' in data and data['knowledge_graph']:
                kg = data['knowledge_graph']
                if 'description' in kg:
                    return f"**🌐 Search Result**: {kg['description']}"
                elif 'title' in kg:
                    return f"**🌐 {kg['title']}**: {kg.get('description', 'Information found')}"

            # Try organic results
            if 'organic_results' in data and data['organic_results']:
                for result in data['organic_results'][:2]:
                    snippet = result.get('snippet', '')
                    if snippet and len(snippet) > 20:
                        return f"**🌐 Search Result**: {snippet}"

            # Try answer box
            if 'answer_box' in data and data['answer_box']:
                answer = data['answer_box']
                if 'answer' in answer:
                    return f"**🌐 Answer**: {answer['answer']}"
                elif 'snippet' in answer:
                    return f"**🌐 Answer**: {answer['snippet']}"

            return f"🤔 I found information about '{query}' but couldn't extract a clear answer. Try rephrasing your question."

        except Exception as e:
            return f"❌ Error processing search results: {str(e)}"

    def chat_with_ai(self, message, user_name=None):
        """AI responses for conversations"""
        message_lower = message.lower()

        responses = {
            'hi': f"Hello{' ' + user_name if user_name else ''}! 👋 I'm your AI assistant with database memory! Ask me anything!",
            'hello': f"Hello{' ' + user_name if user_name else ''}! 👋 How can I help you today?",
            'hey': f"Hey{' ' + user_name if user_name else ''}! 🎉 Ready to answer your questions!",
            'how are you': "I'm doing great! Thanks for asking! 😄 Our conversation is being saved in the database!",

            'thank you': "You're welcome! 😊 Happy to help!",
            'thanks': "You're welcome! 😊 Let me know if you need anything else!",

            'what can you do': """
🤖 **I can help you with**:
- Answer questions (Who, What, Where, When, Why, How)
- Search for current information
- Explain concepts
- Find definitions
- Remember our conversations in database
- And much more!

Just ask me anything! 🚀
            """,

            'who are you': "I'm your AI assistant powered by real-time web search and MySQL database! I remember all our conversations!",
        }

        # Check for exact matches
        for key, response in responses.items():
            if key in message_lower:
                return response

        # Default conversation response
        return f"🤖 I'd be happy to help! Try asking me a question starting with 'who', 'what', 'where', etc. and I'll search for current information!"

    def smart_response(self, user_input, user_name=None):
        """SMART response that searches for questions and saves to database"""
        user_input_lower = user_input.lower().strip()

        # List of question starters that should ALWAYS trigger search
        question_starters = [
            'who is', 'what is', 'where is', 'when is', 'why is', 'how to',
            'who are', 'what are', 'where are', 'when are', 'why are', 'how are',
            'who was', 'what was', 'where was', 'when was', 'why was', 'how was',
            'define', 'explain', 'tell me about'
        ]

        # Specific people/topics that should trigger search
        search_topics = [
            'elon musk', 'bill gates', 'albert einstein', 'steve jobs',
            'artificial intelligence', 'machine learning', 'quantum computing',
            'current', 'latest', 'news', 'today', 'weather', 'price of',
            'python', 'javascript', 'programming', 'coding'
        ]

        # Check if it starts with a question word
        starts_with_question = any(user_input_lower.startswith(prefix) for prefix in question_starters)

        # Check if it contains searchable topics
        contains_topic = any(topic in user_input_lower for topic in search_topics)

        # Check if it's a clear question
        is_question = ('?' in user_input_lower) or any(
            word in user_input_lower for word in ['who', 'what', 'where', 'when', 'why', 'how'])

        # DECISION: When to search vs when to chat
        if starts_with_question or contains_topic or is_question:
            bot_response = self.search_with_searchapi(user_input)
        else:
            bot_response = self.chat_with_ai(user_input, user_name)

        # ✅ SAVE TO DATABASE
        if user_name:
            save_success = self.db.save_conversation(user_input, bot_response, user_name)
            if save_success:
                st.sidebar.success("💾 Conversation saved to database!")
            else:
                st.sidebar.error("❌ Failed to save to database!")

        return bot_response


def extract_name(user_input):
    """Extract name from user input"""
    patterns = [
        r'my name is (\w+)', r'i am (\w+)', r'call me (\w+)', r"i'm (\w+)",
        r"name's (\w+)", r"this is (\w+)", r"you can call me (\w+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, user_input.lower())
        if match:
            return match.group(1).title()
    return None


def main():
    # Initialize AI assistant with database
    ai = SmartAIAssistant(SEARCHAPI_KEY)

    # DEBUG: Test database connection
    try:
        test_save = ai.db.save_conversation("test message", "test response", "test_user")
        if test_save:
            st.sidebar.success("✅ Database connection working!")
        else:
            st.sidebar.error("❌ Database save failed!")
    except Exception as e:
        st.sidebar.error(f"❌ Database error: {e}")

    # Custom CSS
    st.markdown("""
    <style>
    .chat-container { max-width: 800px; margin: 0 auto; }
    .user-message {
        background-color: #007bff; color: white; padding: 12px;
        border-radius: 15px; margin: 8px 0; max-width: 70%; margin-left: auto;
    }
    .bot-message {
        background-color: #f1f3f4; color: black; padding: 12px;
        border-radius: 15px; margin: 8px 0; max-width: 70%; margin-right: auto;
    }
    .database-badge {
        background: #4ECDC4; color: white; padding: 2px 8px; 
        border-radius: 10px; font-size: 0.7em; margin-left: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("🚀 Smart AI Assistant with MySQL")
    st.markdown("### Real-time Web Search + Database Memory")
    st.markdown("---")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant",
             "content": "Hello! 👋 I'm your **AI Assistant with MySQL Database**! I remember all our conversations! What's your name?"}
        ]

    if "user_name" not in st.session_state:
        st.session_state.user_name = None

    # Display chat
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
            else:
                content = message["content"]
                # Add database badge for saved conversations
                if st.session_state.user_name and "🌐" not in content:
                    content += ' <span class="database-badge">💾 Saved</span>'
                st.markdown(f'<div class="bot-message">🤖 {content}</div>', unsafe_allow_html=True)

    # User info sidebar
    if st.session_state.user_name:
        st.sidebar.markdown(f"### 👋 Welcome, {st.session_state.user_name}!")

        # Show conversation history from database
        if st.sidebar.button("📊 Show My History"):
            history = ai.db.get_conversation_history(st.session_state.user_name, 5)
            if history:
                st.sidebar.markdown("### Your Recent Chats:")
                for chat in reversed(history):
                    st.sidebar.text(f"💬 {chat['user_message'][:50]}...")
                    st.sidebar.text(f"🤖 {chat['ai_response'][:50]}...")
                    st.sidebar.markdown("---")
            else:
                st.sidebar.info("No conversation history yet!")

    # Chat input
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("Your message:", placeholder="Ask me anything...", key="user_input")
    with col2:
        send_button = st.button("Send 🚀")

    # Quick question buttons
    st.markdown("### 💡 Try These Questions:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Who is Elon Musk?"):
            user_input = "Who is Elon Musk"
    with col2:
        if st.button("What is AI?"):
            user_input = "What is artificial intelligence"
    with col3:
        if st.button("Latest Tech"):
            user_input = "Latest technology news"
    with col4:
        if st.button("My History"):
            user_input = "show my history"

    # Handle input
    if send_button and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        name = extract_name(user_input)
        if name and not st.session_state.user_name:
            st.session_state.user_name = name
            # Save user preference
            ai.db.save_user_preference(name, "conversation_style", "friendly")

        bot_response = ai.smart_response(user_input, st.session_state.user_name)
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        st.rerun()

    # Sidebar with database info
    with st.sidebar:
        st.header("🗃️ Database Features")
        st.markdown("""
        **💾 MySQL Storage**:
        - Save all conversations
        - User preferences  
        - Chat history
        - Analytics data
        """)

        # Database analytics
        analytics = ai.db.get_analytics()
        if analytics:
            st.markdown("---")
            st.markdown("### 📈 Analytics")
            st.metric("Total Chats", analytics.get('total_conversations', 0))
            st.metric("Unique Users", analytics.get('unique_users', 0))
            st.metric("Today's Chats", analytics.get('today_conversations', 0))

        st.markdown("---")
        st.markdown(f"**Last update:** {datetime.now().strftime('%H:%M:%S')}")

        if st.button("Clear Chat 🗑️"):
            st.session_state.messages = [
                {"role": "assistant", "content": "Chat cleared! What's your name?"}
            ]
            st.session_state.user_name = None
            st.rerun()


if __name__ == "__main__":
    main()
