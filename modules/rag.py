import streamlit as st
from groq import Groq
import pdfplumber
import chromadb
from chromadb.config import Settings
import hashlib

def show(api_key):
    """RAG - PDF Chat with ChromaDB"""
    st.title("💬 RAG – PDF Chat")
    st.markdown("### Chat with your study materials using RAG")
    
    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar.")
        return
    
    st.markdown("---")
    
    # Initialize ChromaDB
    if 'chroma_client' not in st.session_state:
        st.session_state.chroma_client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            is_persistent=False
        ))
        st.session_state.collection = st.session_state.chroma_client.create_collection(
            name="study_docs",
            metadata={"description": "Study documents collection"}
        )
        st.session_state.doc_chunks = []
    
    # File upload
    st.subheader("📁 Upload Documents")
    
    uploaded_files = st.file_uploader("Upload PDFs", type=['pdf'], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("📥 Process Documents", type="primary"):
            with st.spinner("Processing and indexing documents..."):
                process_documents(uploaded_files, st.session_state.collection)
                st.success(f"✅ Processed {len(uploaded_files)} documents")
    
    # Show indexed documents
    if st.session_state.doc_chunks:
        st.info(f"📚 {len(st.session_state.doc_chunks)} chunks indexed from {len(set([c['source'] for c in st.session_state.doc_chunks]))} documents")
    
    st.markdown("---")
    
    # Chat interface
    st.subheader("💬 Chat with Documents")
    
    if not st.session_state.doc_chunks:
        st.warning("⚠️ Please upload and process documents first")
        return
    
    # Chat history
    if 'rag_messages' not in st.session_state:
        st.session_state.rag_messages = []
    
    # Display chat history
    for msg in st.session_state.rag_messages:
        with st.chat_message(msg['role']):
            st.write(msg['content'])
            if 'sources' in msg:
                with st.expander("📄 Sources"):
                    for source in msg['sources']:
                        st.caption(f"• {source}")
    
    # Chat input
    user_query = st.chat_input("Ask a question about your documents...")
    
    if user_query:
        # Add user message
        st.session_state.rag_messages.append({'role': 'user', 'content': user_query})
        
        with st.spinner("Searching documents..."):
            try:
                # Query ChromaDB
                results = st.session_state.collection.query(
                    query_texts=[user_query],
                    n_results=3
                )
                
                if results['documents'] and results['documents'][0]:
                    context = "\n\n".join(results['documents'][0])
                    metadatas = results['metadatas'][0]
                    
                    # Generate response with Groq
                    client = Groq(api_key=api_key)
                    
                    prompt = f"""Based on the following context from study documents, answer the question.
If the answer cannot be found in the context, clearly state that.

Context:
{context}

Question: {user_query}

Provide a clear, accurate answer based only on the given context."""

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a helpful study assistant. Answer questions strictly based on provided context."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    
                    answer = response.choices[0].message.content
                    
                    # Extract sources
                    sources = [f"{m['source']} (Page {m['page']})" for m in metadatas]
                    
                    st.session_state.rag_messages.append({
                        'role': 'assistant',
                        'content': answer,
                        'sources': sources
                    })
                else:
                    st.session_state.rag_messages.append({
                        'role': 'assistant',
                        'content': "❌ I couldn't find relevant information in the uploaded documents to answer this question."
                    })
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def process_documents(uploaded_files, collection):
    """Process PDFs and store in ChromaDB"""
    all_chunks = []
    
    for uploaded_file in uploaded_files:
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        # Simple chunking by paragraphs
                        paragraphs = text.split('\n\n')
                        for i, para in enumerate(paragraphs):
                            if len(para.strip()) > 50:  # Skip very short chunks
                                chunk_id = hashlib.md5(f"{uploaded_file.name}_{page_num}_{i}".encode()).hexdigest()
                                
                                all_chunks.append({
                                    'id': chunk_id,
                                    'text': para.strip(),
                                    'source': uploaded_file.name,
                                    'page': page_num + 1
                                })
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    
    # Add to ChromaDB
    if all_chunks:
        collection.add(
            ids=[c['id'] for c in all_chunks],
            documents=[c['text'] for c in all_chunks],
            metadatas=[{'source': c['source'], 'page': c['page']} for c in all_chunks]
        )
        
        st.session_state.doc_chunks.extend(all_chunks)
