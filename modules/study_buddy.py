import streamlit as st
from gtts import gTTS
import os
import tempfile
from groq import Groq
import json

def show(api_key):
    """Study Buddy - Flashcards and Voice Explanations"""
    st.title("📝 Study Buddy")
    st.markdown("### Flashcards, summaries, and voice explanations")
    
    # Add custom CSS for card flip animation
    st.markdown("""
    <style>
    .flashcard-container {
        perspective: 1000px;
        margin: 20px 0;
    }
    
    .flashcard {
        position: relative;
        width: 100%;
        min-height: 250px;
        transition: transform 0.6s;
        transform-style: preserve-3d;
    }
    
    .flashcard.flipped {
        transform: rotateY(180deg);
    }
    
    .card-face {
        position: absolute;
        width: 100%;
        min-height: 250px;
        backface-visibility: hidden;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    
    .card-front {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .card-back {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        transform: rotateY(180deg);
    }
    
    .card-content {
        font-size: 1.2em;
        line-height: 1.6;
    }
    
    .card-label {
        font-size: 0.9em;
        font-weight: bold;
        margin-bottom: 15px;
        opacity: 0.9;
    }
    
    .flip-button {
        margin: 20px 0;
        padding: 12px 30px;
        font-size: 1.1em;
        background: #667eea;
        color: white;
        border: none;
        border-radius: 25px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .flip-button:hover {
        background: #764ba2;
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📇 Flashcard Generator", "🔊 Voice Explanations"])
    
    with tab1:
        show_flashcard_generator(api_key)
    
    with tab2:
        show_voice_explanations()

def show_flashcard_generator(api_key):
    """Generate flashcards from text or PDF"""
    st.subheader("📇 Flashcard Generator")
    
    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar.")
        return
    
    input_type = st.radio("Input Type", ["Text", "Upload PDF"], horizontal=True)
    
    if input_type == "Text":
        content = st.text_area("Enter study content", height=200, 
                               placeholder="Paste your study material here...")
    else:
        uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
        if uploaded_file:
            try:
                import pdfplumber
                with pdfplumber.open(uploaded_file) as pdf:
                    content = ""
                    for page in pdf.pages[:10]:  # Limit to first 10 pages
                        content += page.extract_text() or ""
                st.success(f"✅ Extracted text from PDF ({len(content)} characters)")
            except Exception as e:
                st.error(f"❌ Error reading PDF: {str(e)}")
                content = ""
        else:
            content = ""
    
    num_flashcards = st.slider("Number of flashcards", 3, 15, 5)
    
    if st.button("🎴 Generate Flashcards", type="primary"):
        if not content.strip():
            st.error("❌ Please provide content")
            return
        
        with st.spinner("Generating flashcards..."):
            try:
                client = Groq(api_key=api_key)
                
                prompt = f"""Generate exactly {num_flashcards} educational flashcards from this content.

Content:
{content[:3000]}

Return as JSON array with objects having 'question' and 'answer' fields.
Make questions clear and answers concise but complete."""

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a flashcard creation expert. Generate clear, educational flashcards."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                flashcards_text = response.choices[0].message.content
                
                # Try to parse JSON
                try:
                    flashcards = json.loads(flashcards_text)
                except:
                    # Fallback parsing
                    flashcards = []
                    lines = flashcards_text.split('\n')
                    current_q = None
                    for line in lines:
                        if 'question' in line.lower() or 'q:' in line.lower():
                            current_q = line.split(':', 1)[-1].strip()
                        elif 'answer' in line.lower() or 'a:' in line.lower():
                            current_a = line.split(':', 1)[-1].strip()
                            if current_q:
                                flashcards.append({'question': current_q, 'answer': current_a})
                                current_q = None
                
                st.session_state.flashcards = flashcards
                st.session_state.current_card = 0
                st.session_state.show_answer = False
                st.success(f"✅ Generated {len(flashcards)} flashcards!")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display flashcards with flip animation
    if 'flashcards' in st.session_state and st.session_state.flashcards:
        st.markdown("---")
        st.subheader("📚 Your Flashcards")
        
        if 'current_card' not in st.session_state:
            st.session_state.current_card = 0
        if 'show_answer' not in st.session_state:
            st.session_state.show_answer = False
        
        flashcards = st.session_state.flashcards
        current = st.session_state.current_card
        
        if current < len(flashcards):
            card = flashcards[current]
            
            st.info(f"Card {current + 1} of {len(flashcards)}")
            
            # Create the animated flashcard
            flip_class = "flipped" if st.session_state.show_answer else ""
            
            st.markdown(f"""
            <div class="flashcard-container">
                <div class="flashcard {flip_class}">
                    <div class="card-face card-front">
                        <div>
                            <div class="card-label">❓ QUESTION</div>
                            <div class="card-content">{card['question']}</div>
                        </div>
                    </div>
                    <div class="card-face card-back">
                        <div>
                            <div class="card-label">✅ ANSWER</div>
                            <div class="card-content">{card['answer']}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Flip button
            col_flip = st.columns([1, 2, 1])[1]
            with col_flip:
                if st.button("🔄 Flip Card", key="flip", use_container_width=True):
                    st.session_state.show_answer = not st.session_state.show_answer
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Navigation buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("⏮️ First", disabled=(current == 0)):
                    st.session_state.current_card = 0
                    st.session_state.show_answer = False
                    st.rerun()
            
            with col2:
                if st.button("⬅️ Previous", disabled=(current == 0)):
                    st.session_state.current_card -= 1
                    st.session_state.show_answer = False
                    st.rerun()
            
            with col3:
                if st.button("➡️ Next", disabled=(current >= len(flashcards) - 1)):
                    st.session_state.current_card += 1
                    st.session_state.show_answer = False
                    st.rerun()
            
            with col4:
                if st.button("⏭️ Last", disabled=(current >= len(flashcards) - 1)):
                    st.session_state.current_card = len(flashcards) - 1
                    st.session_state.show_answer = False
                    st.rerun()

def show_voice_explanations():
    """Text-to-speech for study content with improved quality"""
    st.subheader("🔊 Voice Explanations")
    st.markdown("Convert your study notes into clear audio explanations")
    
    text_to_speak = st.text_area("Enter text to convert to speech", height=200,
                                 placeholder="Enter study notes or explanations...")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Enhanced English accents for better quality
        accent = st.selectbox("Voice Accent", 
                             ["com", "co.uk", "com.au", "co.in", "ca"],
                             format_func=lambda x: {
                                 "com": "🇺🇸 US English",
                                 "co.uk": "🇬🇧 British English",
                                 "com.au": "🇦🇺 Australian English",
                                 "co.in": "🇮🇳 Indian English",
                                 "ca": "🇨🇦 Canadian English"
                             }[x])
    
    with col2:
        slow_speed = st.checkbox("🐢 Slower pace (better for learning)", value=False)
    
    if st.button("🔊 Generate Audio", type="primary", use_container_width=True):
        if not text_to_speak.strip():
            st.error("❌ Please enter text")
            return
        
        with st.spinner("Generating high-quality audio..."):
            try:
                # Display text preview
                display_text = text_to_speak[:500] + ("..." if len(text_to_speak) > 500 else "")
                
                # Generate audio with specific TLD for accent
                tts = gTTS(text=text_to_speak, lang='en', tld=accent, slow=slow_speed)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    tts.save(fp.name)
                    audio_file = fp.name
                
                st.success("✅ Audio generated successfully!")
                
                # Show text being spoken
                with st.expander("📄 View Text", expanded=False):
                    st.write(text_to_speak)
                
                # Audio player with custom styling
                st.markdown("### 🎧 Listen to your explanation:")
                with open(audio_file, 'rb') as f:
                    audio_bytes = f.read()
                    st.audio(audio_bytes, format='audio/mp3')
                
                # Download button
                st.download_button(
                    label="⬇️ Download Audio",
                    data=audio_bytes,
                    file_name="study_audio.mp3",
                    mime="audio/mp3"
                )
                
                # Tips
                st.info("💡 **Tip:** Listen while reading along for better retention!")
                
                # Cleanup
                os.unlink(audio_file)
                
            except Exception as e:
                st.error(f"❌ Error generating audio: {str(e)}")
                st.info("💡 Make sure you have an internet connection for text-to-speech.")