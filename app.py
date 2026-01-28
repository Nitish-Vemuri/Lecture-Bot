"""
LectureBot - Streamlit Application
AI-powered study assistant for last-minute exam preparation
"""
import streamlit as st
from pathlib import Path
import time

from config import settings, get_user_uploads_dir, get_user_vectorstore_dir
from core import DocumentProcessor, VectorStoreManager, RAGEngine
from auth import CognitoAuth
from utils.logger import log


# Page configuration
st.set_page_config(
    page_title=settings.app_title,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def initialize_auth_state():
    """Initialize authentication-related session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'auth_view' not in st.session_state:
        st.session_state.auth_view = 'login'  # login, register, verify, forgot_password
    if 'pending_username' not in st.session_state:
        st.session_state.pending_username = None


def initialize_session_state(username: str):
    """Initialize Streamlit session state"""
    # Use username as the session/user ID for persistent storage
    if 'session_id' not in st.session_state or st.session_state.session_id != username:
        st.session_state.session_id = username
        log.info(f"User session initialized: {username}")
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'rag_engine' not in st.session_state:
        st.session_state.rag_engine = None
    
    if 'vectorstore_manager' not in st.session_state:
        st.session_state.vectorstore_manager = None
    
    if 'document_processor' not in st.session_state:
        # Pass username as session_id for user-scoped uploads
        st.session_state.document_processor = DocumentProcessor(
            session_id=username
        )
    
    if 'documents_loaded' not in st.session_state:
        st.session_state.documents_loaded = False
    
    if 'collection_name' not in st.session_state:
        st.session_state.collection_name = "lecture_docs"


def display_header(name: str = None):
    """Display application header"""
    st.markdown('<p class="main-header">📚 LectureBot</p>', unsafe_allow_html=True)
    if name:
        st.markdown(
            f"<p style='text-align: center; color: #666;'>Welcome back, <strong>{name}</strong>! Ready to study?</p>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<p style='text-align: center; color: #666;'>Your AI Study Assistant for Last-Minute Exam Preparation</p>",
            unsafe_allow_html=True
        )
    st.divider()


def sidebar_setup():
    """Setup sidebar with document upload and configuration"""
    with st.sidebar:
        st.header("⚙️ Setup")
        
        # API Key Input
        with st.expander("🔑 API Configuration", expanded=not settings.openai_api_key):
            # Ensure session flag for showing input exists
            if 'show_api_input' not in st.session_state:
                st.session_state.show_api_input = False

            # If key already set and user is not editing, show placeholder and change button
            if settings.openai_api_key and not st.session_state.show_api_input:
                st.info("✅ API key is set and hidden.")
                if st.button("Change API key"):
                    st.session_state.show_api_input = True
            else:
                # Show secure input when no key or when editing
                api_key = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    value="",
                    placeholder="Enter your OpenAI API key",
                    help="Enter your OpenAI API key to enable the chatbot"
                )

                if api_key:
                    settings.openai_api_key = api_key
                    st.session_state.show_api_input = False
                    st.success("API key updated!")
        
        st.divider()
        
        # Document Upload Section
        st.header("📄 Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Upload lecture materials",
            type=['pdf', 'docx', 'txt', 'md', 'pptx'],
            accept_multiple_files=True,
            help=f"Max file size: {settings.max_file_size_mb}MB"
        )
        
        collection_name = st.text_input(
            "Collection Name",
            value=st.session_state.collection_name,
            help="Name for this set of documents"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Process Documents", use_container_width=True):
                process_documents(uploaded_files, collection_name)
        
        with col2:
            if st.button("🔄 Load Existing", use_container_width=True):
                load_existing_collection(collection_name)
        
        st.divider()
        
        # System Status
        st.header("📊 Status")
        
        if st.session_state.documents_loaded:
            st.success("✅ System Ready")
        else:
            st.warning("⚠️ Please load documents")
        
        # Configuration Display
        with st.expander("⚙️ Current Configuration"):
            st.text(f"Model: {settings.llm_model}")
            st.text(f"Embeddings: {settings.embedding_model}")
            st.text(f"Vector Store: {settings.vector_store_type}")
            st.text(f"Top K Results: {settings.top_k_results}")
            st.text(f"Chunk Size: {settings.chunk_size}")
        
        st.divider()
        
        # Maintenance Buttons
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.rag_engine:
                st.session_state.rag_engine.clear_history()
            st.rerun()
        
        if st.button("🧹 Clean Up Files", use_container_width=True):
            cleanup_uploaded_files()


def process_documents(uploaded_files, collection_name):
    """Process and index uploaded documents"""
    if not uploaded_files:
        st.error("Please upload at least one document")
        return
    
    if not settings.openai_api_key:
        st.error("Please set your OpenAI API key first")
        return
    
    with st.spinner("Processing documents..."):
        try:
            # Save uploaded files
            file_paths = []
            for uploaded_file in uploaded_files:
                file_path = st.session_state.document_processor.save_uploaded_file(uploaded_file)
                file_paths.append(file_path)
            
            # Process documents
            progress_bar = st.progress(0, text="Loading documents...")
            chunks = st.session_state.document_processor.process_multiple_files(file_paths)
            
            if not chunks:
                st.error("No content extracted from documents")
                return
            
            progress_bar.progress(50, text="Creating vector store...")
            
            # Create vector store with session-scoped storage
            vectorstore_manager = VectorStoreManager(
                session_id=st.session_state.session_id
            )
            vectorstore_manager.create_vectorstore(chunks, collection_name)
            
            progress_bar.progress(75, text="Initializing RAG engine...")
            
            # Initialize RAG engine
            retriever = vectorstore_manager.get_retriever()
            rag_engine = RAGEngine(retriever)
            
            # Update session state
            st.session_state.vectorstore_manager = vectorstore_manager
            st.session_state.rag_engine = rag_engine
            st.session_state.documents_loaded = True
            st.session_state.collection_name = collection_name
            
            progress_bar.progress(100, text="Complete!")
            time.sleep(0.5)
            progress_bar.empty()
            
            # Clean up uploaded files after successful processing
            cleanup_count = st.session_state.document_processor.cleanup_uploaded_files()
            
            st.success(f"✅ Processed {len(uploaded_files)} file(s) with {len(chunks)} chunks")
            log.info(f"Successfully processed {len(uploaded_files)} documents")
            
        except Exception as e:
            st.error(f"Error processing documents: {str(e)}")
            log.error(f"Document processing error: {str(e)}")


def load_existing_collection(collection_name):
    """Load existing vector store collection"""
    if not settings.openai_api_key:
        st.error("Please set your OpenAI API key first")
        return
    
    with st.spinner("Loading vector store..."):
        try:
            vectorstore_manager = VectorStoreManager(
                session_id=st.session_state.session_id
            )
            vectorstore = vectorstore_manager.load_vectorstore(collection_name)
            
            if not vectorstore:
                st.error(f"Collection '{collection_name}' not found")
                return
            
            # Initialize RAG engine
            retriever = vectorstore_manager.get_retriever()
            rag_engine = RAGEngine(retriever)
            
            # Update session state
            st.session_state.vectorstore_manager = vectorstore_manager
            st.session_state.rag_engine = rag_engine
            st.session_state.documents_loaded = True
            st.session_state.collection_name = collection_name
            
            st.success(f"✅ Loaded collection: {collection_name}")
            log.info(f"Loaded existing collection: {collection_name}")
            
        except Exception as e:
            st.error(f"Error loading collection: {str(e)}")
            log.error(f"Collection loading error: {str(e)}")


def cleanup_uploaded_files():
    """Clean up uploaded files from disk"""
    if st.session_state.document_processor:
        deleted_count = st.session_state.document_processor.cleanup_uploaded_files()
        if deleted_count > 0:
            st.success(f"🧹 Cleaned up {deleted_count} file(s)")
        else:
            st.info("No files to clean up")
    else:
        st.info("No files to clean up")


def display_chat_interface():
    """Display the main chat interface"""
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display sources if available
            if "sources" in message and message["sources"]:
                with st.expander("📚 View Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        st.markdown(f"""
                        <div class="source-box">
                            <strong>Source {i}:</strong> {source['source']}<br>
                            {f"<strong>Page:</strong> {source['page']}<br>" if source['page'] else ""}
                            <em>{source['content_preview']}</em>
                        </div>
                        """, unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask a question about your lecture materials..."):
        # Sanitize user input to mitigate prompt injection
        prompt = sanitize_input(prompt)

        if not st.session_state.documents_loaded:
            st.error("⚠️ Please upload and process documents first!")
            return

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.rag_engine.ask(prompt)
                    
                    st.markdown(response["answer"])
                    
                    # Display sources
                    if response.get("sources"):
                        with st.expander("📚 View Sources"):
                            for i, source in enumerate(response["sources"], 1):
                                st.markdown(f"""
                                <div class="source-box">
                                    <strong>Source {i}:</strong> {source['source']}<br>
                                    {f"<strong>Page:</strong> {source['page']}<br>" if source['page'] else ""}
                                    <em>{source['content_preview']}</em>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "sources": response.get("sources", [])
                    })
                    
                except Exception as e:
                    error_msg = f"Error generating response: {str(e)}"
                    st.error(error_msg)
                    log.error(error_msg)


def display_login_page(cognito: CognitoAuth):
    """Display login/registration page"""
    st.markdown('<p class="main-header">📚 LectureBot</p>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #666;'>Your AI Study Assistant for Last-Minute Exam Preparation</p>",
        unsafe_allow_html=True
    )
    st.divider()
    
    # Auth view tabs
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "🔑 Forgot Password"])
    
    with tab1:
        display_login_form(cognito)
    
    with tab2:
        display_register_form(cognito)
    
    with tab3:
        display_forgot_password_form(cognito)


def display_login_form(cognito: CognitoAuth):
    """Display login form"""
    st.subheader("Welcome Back!")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login", use_container_width=True):
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                with st.spinner("Signing in..."):
                    success, message, auth_data = cognito.sign_in(username, password)
                
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_info = auth_data['user_info']
                    st.session_state.access_token = auth_data['access_token']
                    st.success(message)
                    time.sleep(0.5)
                    st.rerun()
                else:
                    if "verify your email" in message.lower():
                        st.warning(message)
                        st.session_state.pending_username = username
                        st.info("Need to verify your email? Enter the code sent to your email below.")
                        display_verification_form(cognito, username)
                    else:
                        st.error(message)


def display_register_form(cognito: CognitoAuth):
    """Display registration form"""
    st.subheader("Create Account")
    
    # Check if we need to show verification
    if st.session_state.pending_username:
        display_verification_form(cognito, st.session_state.pending_username)
        if st.button("← Back to Registration"):
            st.session_state.pending_username = None
            st.rerun()
        return
    
    with st.form("register_form"):
        new_username = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password", 
            help="At least 8 characters with uppercase, lowercase, number, and special character")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Register", use_container_width=True):
            # Validation
            if not all([new_username, new_name, new_email, new_password]):
                st.error("All fields are required!")
            elif new_password != confirm_password:
                st.error("Passwords don't match!")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters!")
            else:
                with st.spinner("Creating account..."):
                    success, message = cognito.sign_up(
                        new_username, new_password, new_email, new_name
                    )
                
                if success:
                    st.success(message)
                    st.session_state.pending_username = new_username
                    st.rerun()
                else:
                    st.error(message)


def display_verification_form(cognito: CognitoAuth, username: str):
    """Display email verification form"""
    st.subheader("📧 Verify Your Email")
    st.info(f"A verification code was sent to your email for account: **{username}**")
    
    with st.form("verify_form"):
        code = st.text_input("Verification Code")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Verify", use_container_width=True):
                if not code:
                    st.error("Please enter the verification code")
                else:
                    with st.spinner("Verifying..."):
                        success, message = cognito.confirm_sign_up(username, code)
                    
                    if success:
                        st.success(message)
                        st.session_state.pending_username = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
    
    if st.button("Resend Code"):
        success, message = cognito.resend_confirmation_code(username)
        if success:
            st.success(message)
        else:
            st.error(message)


def display_forgot_password_form(cognito: CognitoAuth):
    """Display forgot password form"""
    st.subheader("Reset Password")
    
    # Step 1: Request reset code
    with st.form("forgot_password_form"):
        username = st.text_input("Username")
        
        if st.form_submit_button("Send Reset Code", use_container_width=True):
            if not username:
                st.error("Please enter your username")
            else:
                with st.spinner("Sending reset code..."):
                    success, message = cognito.forgot_password(username)
                
                if success:
                    st.success(message)
                    st.session_state.reset_username = username
                else:
                    st.error(message)
    
    # Step 2: Reset password with code
    if hasattr(st.session_state, 'reset_username') and st.session_state.reset_username:
        st.divider()
        st.subheader("Enter Reset Code")
        
        with st.form("reset_password_form"):
            code = st.text_input("Reset Code")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Reset Password", use_container_width=True):
                if not all([code, new_password, confirm_password]):
                    st.error("All fields are required")
                elif new_password != confirm_password:
                    st.error("Passwords don't match!")
                else:
                    with st.spinner("Resetting password..."):
                        success, message = cognito.confirm_forgot_password(
                            st.session_state.reset_username, code, new_password
                        )
                    
                    if success:
                        st.success(message)
                        st.session_state.reset_username = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)


def sanitize_input(user_input):
    """
    Sanitize user input to mitigate prompt injection attacks.
    This function removes or escapes potentially harmful characters.
    """
    # Example sanitization: escape HTML tags and remove dangerous patterns
    sanitized = user_input.replace("<", "&lt;").replace(">", "&gt;")
    return sanitized


def main():
    """Main application entry point"""
    initialize_auth_state()
    
    # Check if Cognito is configured
    if not settings.cognito_user_pool_id or not settings.cognito_app_client_id:
        st.error("⚠️ AWS Cognito is not configured. Please set the following in your .env file:")
        st.code("""
COGNITO_USER_POOL_ID=your_user_pool_id
COGNITO_APP_CLIENT_ID=your_app_client_id
COGNITO_APP_CLIENT_SECRET=your_app_client_secret
AWS_REGION=us-east-1
        """)
        st.stop()
    
    # Initialize Cognito
    try:
        cognito = CognitoAuth()
    except Exception as e:
        st.error(f"Failed to initialize Cognito: {str(e)}")
        st.stop()
    
    # Check authentication status
    if not st.session_state.authenticated:
        display_login_page(cognito)
    else:
        # User is logged in
        user_info = st.session_state.user_info
        username = user_info.get('username', 'User')
        name = user_info.get('name', username)
        
        initialize_session_state(username)
        display_header(name)
        
        # Sidebar with logout
        with st.sidebar:
            st.write(f"👤 Logged in as: **{name}**")
            if st.button("🚪 Logout", use_container_width=True):
                # Clear session
                if st.session_state.access_token:
                    cognito.sign_out(st.session_state.access_token)
                st.session_state.authenticated = False
                st.session_state.user_info = None
                st.session_state.access_token = None
                st.session_state.messages = []
                st.session_state.rag_engine = None
                st.session_state.vectorstore_manager = None
                st.session_state.documents_loaded = False
                log.info(f"User logged out: {username}")
                st.rerun()
            st.divider()
        
        sidebar_setup()
        
        # Main content area
        if not st.session_state.documents_loaded:
            # Welcome screen
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                first_name = name.split()[0] if name else "there"
                st.markdown(f"""
                ### 👋 Welcome to LectureBot, {first_name}!
                
                Get started by:
                1. 🔑 Enter your OpenAI API key in the sidebar
                2. 📄 Upload your lecture materials (PDF, DOCX, TXT, MD, PPTX)
                3. 📥 Click "Process Documents" to create your knowledge base
                4. 💬 Start asking questions about your materials!
                
                #### ✨ Features:
                - **Smart Q&A**: Ask questions and get answers from your lecture notes
                - **Source Citations**: See exactly where information comes from
                - **Conversation Memory**: Have natural back-and-forth discussions
                - **Multi-Document Support**: Upload multiple files at once
                - **Your Private Space**: Your documents are stored securely under your account
                
                #### 💡 Tips:
                - Ask specific questions for better answers
                - Request explanations, summaries, or comparisons
                - Ask for key concepts or definitions
                - Request practice questions or exam tips
                """)
        else:
            # Chat interface
            display_chat_interface()


if __name__ == "__main__":
    main()
