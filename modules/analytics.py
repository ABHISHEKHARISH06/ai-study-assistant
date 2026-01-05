import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show(data_handler):
    """Analytics Dashboard"""
    st.title("📊 Analytics Dashboard")
    st.markdown("### Track your learning progress")
    
    st.markdown("---")
    
    # Load data
    data = data_handler.load_data()
    
    if len(data) == 0:
        st.warning("⚠️ No data available. Add study records on the Home page.")
        return
    
    # Overview metrics
    st.subheader("📈 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(data))
    
    with col2:
        st.metric("Unique Subjects", data['subject'].nunique())
    
    with col3:
        completed = len(data[data['final_score'] > 0])
        st.metric("Completed Exams", completed)
    
    with col4:
        avg_score = data[data['final_score'] > 0]['final_score'].mean()
        st.metric("Avg Score", f"{avg_score:.1f}%" if not pd.isna(avg_score) else "N/A")
    
    st.markdown("---")
    
    # Subject-wise performance
    st.subheader("📚 Subject-wise Performance")
    
    subject_data = data.groupby('subject').agg({
        'final_score': 'mean',
        'study_hours': 'sum',
        'difficulty': 'mean'
    }).reset_index()
    
    subject_data = subject_data[subject_data['final_score'] > 0]
    
    if len(subject_data) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(subject_data, x='subject', y='final_score',
                        title='Average Score by Subject',
                        labels={'final_score': 'Score (%)', 'subject': 'Subject'},
                        color='final_score',
                        color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(subject_data, values='study_hours', names='subject',
                        title='Study Hours Distribution')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Complete some exams to see subject-wise performance")
    
    st.markdown("---")
    
    # Study trends
    st.subheader("📊 Study Trends")
    
    if 'predicted_score' in data.columns:
        completed_data = data[data['final_score'] > 0].copy()
        
        if len(completed_data) > 0:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=completed_data.index,
                y=completed_data['final_score'],
                mode='lines+markers',
                name='Actual Score',
                line=dict(color='green', width=2)
            ))
            
            if 'predicted_score' in completed_data.columns:
                fig.add_trace(go.Scatter(
                    x=completed_data.index,
                    y=completed_data['predicted_score'],
                    mode='lines+markers',
                    name='Predicted Score',
                    line=dict(color='blue', width=2, dash='dash')
                ))
            
            fig.update_layout(
                title='Predicted vs Actual Scores',
                xaxis_title='Record Index',
                yaxis_title='Score (%)',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Difficulty vs Performance
    col1, col2 = st.columns(2)
    
    with col1:
        completed = data[data['final_score'] > 0]
        if len(completed) > 0:
            fig = px.scatter(completed, x='difficulty', y='final_score',
                           size='study_hours', color='subject',
                           title='Difficulty vs Score',
                           labels={'difficulty': 'Difficulty Level', 'final_score': 'Score (%)'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if len(completed) > 0:
            fig = px.scatter(completed, x='study_hours', y='final_score',
                           color='subject', size='difficulty',
                           title='Study Hours vs Score',
                           labels={'study_hours': 'Study Hours', 'final_score': 'Score (%)'})
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed data table
    st.subheader("📋 Detailed Records")
    
    display_data = data[['subject', 'study_hours', 'previous_score', 'days_before_exam', 'difficulty', 'final_score']].copy()
    st.dataframe(display_data, use_container_width=True)
    
    # Download data
    csv = data.to_csv(index=False)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name="study_data.csv",
        mime="text/csv"
    )
