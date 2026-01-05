import streamlit as st
import json
import re
from groq import Groq

def clean_markdown_code_blocks(text):
    """Remove markdown code block formatting from text"""
    if not isinstance(text, str):
        return text
    
    # Remove code blocks with language specifiers (```json, ```python, etc.)
    text = re.sub(r'```[a-z]*\n', '', text)
    # Remove closing code blocks
    text = re.sub(r'```', '', text)
    # Remove inline code backticks if the entire text is wrapped
    text = text.strip('`')
    
    return text.strip()

def format_step_by_step(content):
    """Format step-by-step explanations from dict, JSON, or structured text"""
    # If it's already a dictionary, format it directly
    if isinstance(content, dict):
        formatted_steps = []
        for key, value in sorted(content.items()):
            if key.lower().startswith('step'):
                # Extract step number if present
                step_name = key.replace('_', ' ').title()
                formatted_steps.append(f"**{step_name}:**\n\n{value}\n")
        return "\n".join(formatted_steps) if formatted_steps else str(content)
    
    # If it's a string, try to parse it
    if not isinstance(content, str):
        return content
    
    # First clean markdown code blocks
    text = clean_markdown_code_blocks(content)
    text = text.strip()
    
    # Try to parse as JSON if it looks like JSON
    if text.startswith('{') and text.endswith('}'):
        try:
            data = json.loads(text)
            formatted_steps = []
            for key, value in sorted(data.items()):
                if key.lower().startswith('step'):
                    step_name = key.replace('_', ' ').title()
                    formatted_steps.append(f"**{step_name}:**\n\n{value}\n")
            return "\n".join(formatted_steps) if formatted_steps else text
        except (json.JSONDecodeError, ValueError):
            pass
    
    return text

def show(api_key):
    """Brain - Study Intelligence Agent"""
    st.title("🧠 Brain – Study Intelligence Agent")
    st.markdown("### Your AI-powered concept explanation assistant")
    
    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar to use this feature.")
        return
    
    # Initialize Groq client
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        st.error(f"❌ Invalid API key: {str(e)}")
        return
    
    st.markdown("---")
    
    # Initialize session state for concept data
    if 'concept_data' not in st.session_state:
        st.session_state.concept_data = None
    if 'current_concept' not in st.session_state:
        st.session_state.current_concept = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Concept input
    concept = st.text_input(
        "Enter a concept to learn",
        placeholder="e.g., Photosynthesis, Quadratic Equations, Newton's Laws"
    )
    
    subject_area = st.selectbox(
        "Subject Area",
        ["General", "Mathematics", "Science", "Computer Science", "History", "Literature", "Other"]
    )
    
    explanation_types = st.multiselect(
        "Select explanation types",
        ["Simple Explanation", "Real-World Analogy", "Step-by-Step Breakdown", "Example-Based"],
        default=["Simple Explanation", "Real-World Analogy"]
    )
    
    if st.button("🧠 Explain Concept", type="primary"):
        if not concept.strip():
            st.error("❌ Please enter a concept")
            return
        
        # Reset chat history when new concept is explained
        if st.session_state.current_concept != concept:
            st.session_state.chat_history = []
            st.session_state.current_concept = concept
        
        with st.spinner("🤔 Analyzing concept..."):
            try:
                # Construct prompt
                prompt = f"""You are a study assistant. Explain the concept: "{concept}" in the subject area: {subject_area}.

Provide the following:
1. Difficulty Level (1-10)
2. Prerequisites (list 2-3 topics to know first)
3. Explanations in these formats: {', '.join(explanation_types)}

Format your response as JSON with this structure:
{{
  "difficulty": <number>,
  "prerequisites": [<array of strings>],
  "explanations": {{
    "simple_explanation": "<text>",
    "real_world_analogy": "<text>",
    "step_by_step_breakdown": "<text with Step 1:, Step 2:, etc>",
    "example_based": "<text>"
  }}
}}

IMPORTANT: Each explanation value should be plain text (string), not nested JSON objects. For step-by-step, write it as natural text with "Step 1:", "Step 2:", etc.

Be clear, concise, and educational. Focus on helping students understand."""

                # Call Groq API
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert educational AI assistant focused on clear, structured explanations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content
                
                # Remove markdown code blocks if present
                content = re.sub(r'^```json\s*', '', content)
                content = re.sub(r'^```\s*', '', content)
                content = re.sub(r'\s*```$', '', content)
                content = content.strip()
                
                # Try to parse JSON
                try:
                    data = json.loads(content)
                    st.session_state.concept_data = data
                    
                except json.JSONDecodeError:
                    # If JSON parsing fails, store as plain text
                    st.session_state.concept_data = {"raw_content": content}
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                return
    
    # Display concept explanation if available
    if st.session_state.concept_data:
        data = st.session_state.concept_data
        
        # Check if it's structured JSON data
        if "raw_content" not in data:
            # Display difficulty
            st.subheader("📊 Concept Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                difficulty = data.get('difficulty', 5)
                st.metric("Difficulty Level", f"{difficulty}/10")
            
            with col2:
                prereqs = data.get('prerequisites', [])
                st.write("**Prerequisites:**")
                for prereq in prereqs:
                    st.write(f"• {prereq}")
            
            st.markdown("---")
            
            # Display explanations
            st.subheader("📚 Explanations")
            explanations = data.get('explanations', {})
            
            for exp_type in explanation_types:
                # Try multiple key formats
                possible_keys = [
                    exp_type.lower().replace('-', '_').replace(' ', '_'),
                    exp_type.lower().replace(' ', '_'),
                    exp_type,
                    exp_type.replace(' ', '')
                ]
                
                exp_text = None
                for key in possible_keys:
                    if key in explanations:
                        exp_text = explanations[key]
                        break
                
                if exp_text:
                    # Special handling for Step-by-Step Breakdown
                    if "step" in exp_type.lower() and "breakdown" in exp_type.lower():
                        exp_text = format_step_by_step(exp_text)
                    else:
                        exp_text = clean_markdown_code_blocks(exp_text)
                    
                    with st.expander(f"📖 {exp_type}", expanded=True):
                        st.markdown(exp_text)
        else:
            # Display raw content
            st.subheader("📚 Explanation")
            st.write(clean_markdown_code_blocks(data["raw_content"]))
        
        # Follow-up questions section
        st.markdown("---")
        st.subheader("💬 Follow-up Questions")
        
        # Display chat history first
        if st.session_state.chat_history:
            for i, chat in enumerate(st.session_state.chat_history):
                with st.container():
                    st.write(f"**Q:** {chat['q']}")
                    # Clean markdown from answers
                    st.write(f"**A:** {clean_markdown_code_blocks(chat['a'])}")
                    if i < len(st.session_state.chat_history) - 1:
                        st.markdown("---")
        
        # Follow-up question input
        with st.form(key="followup_form"):
            follow_up = st.text_input("Ask a follow-up question", key="follow_up_input")
            submit_button = st.form_submit_button("Ask")
            
            if submit_button and follow_up.strip():
                with st.spinner("Thinking..."):
                    try:
                        followup_response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": f"You are explaining the concept: {st.session_state.current_concept}. Answer follow-up questions clearly and concisely."},
                                {"role": "user", "content": follow_up}
                            ],
                            temperature=0.7,
                            max_tokens=1000
                        )
                        
                        answer = followup_response.choices[0].message.content
                        st.session_state.chat_history.append({"q": follow_up, "a": answer})
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")