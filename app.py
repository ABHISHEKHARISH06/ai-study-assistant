import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Import modules
from modules import brain, scheduler, study_buddy, visualizer, rag, analytics
from utils.data_handler import DataHandler

# Page configuration
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = None
if 'data_handler' not in st.session_state:
    st.session_state.data_handler = DataHandler()
if 'study_streak' not in st.session_state:
    st.session_state.study_streak = 0

def check_api_key():
    """Check if Groq API key is set"""
    if not st.session_state.groq_api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar to use AI features.")
        return False
    return True

def main():
    # Sidebar
    with st.sidebar:
        st.title("🎓 AI Study Assistant")
        st.markdown("---")
        
        # API Key Input
        st.subheader("🔑 API Configuration")
        api_key_input = st.text_input(
            "Enter your Groq API Key",
            type="password",
            value=st.session_state.groq_api_key or "",
            help="Get your free API key from https://console.groq.com"
        )
        
        if api_key_input and api_key_input != st.session_state.groq_api_key:
            st.session_state.groq_api_key = api_key_input
            st.success("✅ API Key saved!")
        
        st.markdown("---")
        
        # Navigation
        st.subheader("📚 Navigation")
        page = st.radio(
            "Select Module",
            [
                "🏠 Home",
                "🧠 Brain – Study Intelligence",
                "📅 ML Study Scheduler",
                "📝 Study Buddy",
                "🎨 Visualizer",
                "💬 RAG – PDF Chat",
                "📊 Analytics"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Stats
        st.subheader("📈 Quick Stats")
        data = st.session_state.data_handler.load_data()
        st.metric("Total Records", len(data))
        st.metric("Study Streak", f"{st.session_state.study_streak} days")
        
        st.markdown("---")
        st.caption("Built for placement readiness 🎯")
    
    # Main content area
    if page == "🏠 Home":
        show_home()
    elif page == "🧠 Brain – Study Intelligence":
        brain.show(st.session_state.groq_api_key)
    elif page == "📅 ML Study Scheduler":
        scheduler.show(st.session_state.data_handler)
    elif page == "📝 Study Buddy":
        study_buddy.show(st.session_state.groq_api_key)
    elif page == "🎨 Visualizer":
        visualizer.show()
    elif page == "💬 RAG – PDF Chat":
        rag.show(st.session_state.groq_api_key)
    elif page == "📊 Analytics":
        analytics.show(st.session_state.data_handler)

def show_home():
    """Home page with data entry and overview"""
    st.title("🎓 AI Study Assistant")
    st.markdown("""
    ### Welcome to your Decision-Support Learning Platform
    
    This system helps you:
    - 📚 Analyze academic performance using ML
    - 🎯 Predict exam scores and identify weak areas
    - 📅 Generate personalized study timetables
    - 🧠 Get AI-powered concept explanations
    - 💬 Chat with your study materials using RAG
    - 📊 Track progress with analytics
    """)
    
    st.markdown("---")
    
    # Data Entry Section
    st.header("📝 Enter Study Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add New Record")
        
        with st.form("data_entry_form"):
            subject = st.text_input("Subject Name", placeholder="e.g., Mathematics")
            study_hours = st.number_input("Study Hours", min_value=0.0, max_value=24.0, step=0.5)
            previous_score = st.number_input("Previous Score (%)", min_value=0, max_value=100, step=1)
            days_before_exam = st.number_input("Days Before Exam", min_value=1, max_value=365, step=1)
            difficulty = st.slider("Difficulty Level", min_value=1, max_value=10, value=5)
            final_score = st.number_input("Final Score (%)", min_value=0, max_value=100, step=1, 
                                         help="Leave as 0 if exam not yet taken")
            
            submitted = st.form_submit_button("➕ Add Record")
            
            if submitted:
                if subject.strip():
                    st.session_state.data_handler.add_record(
                        subject=subject.strip(),
                        study_hours=study_hours,
                        previous_score=previous_score,
                        days_before_exam=days_before_exam,
                        difficulty=difficulty,
                        final_score=final_score
                    )
                    st.success(f"✅ Added record for {subject}")
                    st.rerun()
                else:
                    st.error("❌ Subject name cannot be empty")
    
    with col2:
        st.subheader("Current Dataset")
        data = st.session_state.data_handler.load_data()
        
        if len(data) > 0:
            st.dataframe(data, use_container_width=True, height=400)
            
            if st.button("🗑️ Clear All Data", type="secondary"):
                if st.session_state.data_handler.clear_data():
                    st.success("✅ All data cleared")
                    st.rerun()
        else:
            st.info("📋 No data yet. Add your first record to get started!")
    
    st.markdown("---")
    
    # Quick insights
    if len(data) > 0:
        st.header("📊 Quick Insights")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Subjects", data['subject'].nunique())
        
        with col2:
            st.metric("Avg Study Hours", f"{data['study_hours'].mean():.1f}h")
        
        with col3:
            st.metric("Avg Score", f"{data['final_score'].mean():.1f}%")
        
        with col4:
            completed = len(data[data['final_score'] > 0])
            st.metric("Completed Exams", completed)

if __name__ == "__main__":
    main()
