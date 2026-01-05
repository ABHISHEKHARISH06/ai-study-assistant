import streamlit as st
import pandas as pd
import numpy as np
from utils.ml_utils import MLScheduler
from datetime import datetime, time, timedelta

def show(data_handler):
    """ML Study Scheduler"""
    st.title("📅 ML Study Scheduler")
    st.markdown("### Generate personalized study timetables using ML")
    
    st.markdown("---")
    
    # Load data
    data = data_handler.load_data()
    
    if len(data) < 5:
        st.warning(f"⚠️ Need at least 5 records to train ML model. Current: {len(data)}")
        st.info("💡 Add more study records on the Home page to enable predictions.")
        return
    
    # Check if we have completed exams
    completed_data = data[data['final_score'] > 0]
    
    if len(completed_data) < 3:
        st.warning(f"⚠️ Need at least 3 completed exams (final_score > 0) for accurate predictions. Current: {len(completed_data)}")
        st.info("💡 Update existing records with final scores once exams are completed.")
        return
    
    # ML Model Training
    st.subheader("🤖 ML Model Training")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Train ML Model", type="primary"):
            with st.spinner("Training models..."):
                ml_scheduler = MLScheduler()
                results = ml_scheduler.train_models(completed_data)
                
                st.session_state.ml_results = results
                st.session_state.ml_scheduler = ml_scheduler
                
                st.success("✅ Models trained successfully!")
    
    with col2:
        if 'ml_results' in st.session_state:
            results = st.session_state.ml_results
            st.metric("Best Model", "Random Forest")
            st.metric("RMSE", f"{results['best_rmse']:.2f}")
    
    st.markdown("---")
    
    # Predictions
    if 'ml_scheduler' in st.session_state:
        st.subheader("🎯 Score Predictions & Weakness Analysis")
        
        # Get all subjects
        all_subjects = data['subject'].unique()
        
        predictions = []
        
        for subject in all_subjects:
            subject_data = data[data['subject'] == subject].iloc[-1]
            
            pred_score = st.session_state.ml_scheduler.predict_score(subject_data)
            weakness = max(0, (70 - pred_score)) * subject_data['difficulty']
            
            predictions.append({
                'subject': subject,
                'predicted_score': pred_score,
                'difficulty': subject_data['difficulty'],
                'weakness_score': weakness,
                'study_hours': subject_data['study_hours'],
                'days_before_exam': subject_data['days_before_exam']
            })
        
        pred_df = pd.DataFrame(predictions).sort_values('weakness_score', ascending=False)
        st.session_state.predictions = pred_df
        
        # Display predictions
        st.dataframe(
            pred_df.style.background_gradient(subset=['weakness_score'], cmap='Reds'),
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Timetable Generation
        st.subheader("📆 Weekly Study Timetable Generator")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            wake_time = st.time_input("Wake-up Time", value=time(6, 0))
        
        with col2:
            sleep_time = st.time_input("Sleep Time", value=time(23, 0))
        
        with col3:
            break_duration = st.selectbox("Break Duration (min)", [15, 30, 45, 60], index=1)
        
        # Additional settings
        col4, col5 = st.columns(2)
        
        with col4:
            max_sessions_per_day = st.slider("Max Study Sessions/Day", 2, 8, 6)
        
        with col5:
            session_duration = st.selectbox("Session Duration (hours)", [0.5, 1.0, 1.5, 2.0], index=1)
        
        # Meal times configuration
        st.markdown("#### 🍽️ Meal Times")
        meal_col1, meal_col2, meal_col3 = st.columns(3)
        
        with meal_col1:
            breakfast_time = st.time_input("Breakfast Time", value=time(7, 30))
            breakfast_duration = st.number_input("Breakfast Duration (min)", 15, 60, 30)
        
        with meal_col2:
            lunch_time = st.time_input("Lunch Time", value=time(13, 0))
            lunch_duration = st.number_input("Lunch Duration (min)", 20, 90, 60)
        
        with meal_col3:
            dinner_time = st.time_input("Dinner Time", value=time(20, 0))
            dinner_duration = st.number_input("Dinner Duration (min)", 20, 90, 45)
        
        # Morning routine
        morning_routine = st.number_input("Morning Routine (min after waking)", 15, 120, 45, 
                                         help="Time for freshen up, exercise, etc.")
        
        if st.button("📅 Generate Timetable", type="primary"):
            with st.spinner("Generating personalized timetable..."):
                meal_times = {
                    'breakfast': (breakfast_time, breakfast_duration),
                    'lunch': (lunch_time, lunch_duration),
                    'dinner': (dinner_time, dinner_duration),
                    'morning_routine': morning_routine
                }
                
                timetable = generate_smart_timetable(
                    pred_df,
                    wake_time,
                    sleep_time,
                    break_duration,
                    max_sessions_per_day,
                    session_duration,
                    meal_times
                )
                
                st.session_state.timetable = timetable
                st.success("✅ Timetable generated!")
        
        # Display timetable
        if 'timetable' in st.session_state:
            display_timetable(st.session_state.timetable)

def calculate_subject_distribution(predictions, total_days=6):
    """
    Calculate how many days each subject should appear based on weakness scores.
    Weakest subjects get more days, stronger subjects get fewer days.
    """
    # Normalize weakness scores
    total_weakness = predictions['weakness_score'].sum()
    
    if total_weakness == 0:
        # If no weakness detected, distribute equally
        days_per_subject = {subject: 3 for subject in predictions['subject']}
    else:
        # Calculate proportional days (minimum 1, maximum 6)
        days_per_subject = {}
        for _, row in predictions.iterrows():
            # Proportion of total weakness
            proportion = row['weakness_score'] / total_weakness
            # Convert to days (scale to total available days * 6 slots)
            days = max(1, min(6, int(proportion * total_days * 2)))
            days_per_subject[row['subject']] = days
    
    return days_per_subject

def generate_smart_timetable(predictions, wake_time, sleep_time, break_duration, 
                             max_sessions_per_day, session_duration, meal_times):
    """
    Generate a smart weekly study timetable with varied daily schedules.
    - Includes morning routine and meal breaks
    - Weakest subjects appear more frequently across the week
    - Each day has different subjects
    - Intelligent spacing and breaks
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    timetable = {day: [] for day in days}
    
    # Convert times to datetime for calculations
    wake_dt = datetime.combine(datetime.today(), wake_time)
    sleep_dt = datetime.combine(datetime.today(), sleep_time)
    
    # Handle sleep after midnight
    if sleep_dt <= wake_dt:
        sleep_dt += timedelta(days=1)
    
    # Extract meal times
    breakfast_time, breakfast_duration = meal_times['breakfast']
    lunch_time, lunch_duration = meal_times['lunch']
    dinner_time, dinner_duration = meal_times['dinner']
    morning_routine_duration = meal_times['morning_routine']
    
    # Convert meal times to datetime
    breakfast_dt = datetime.combine(datetime.today(), breakfast_time)
    lunch_dt = datetime.combine(datetime.today(), lunch_time)
    dinner_dt = datetime.combine(datetime.today(), dinner_time)
    
    # Calculate subject distribution
    days_per_subject = calculate_subject_distribution(predictions)
    
    # Create a pool of subject sessions based on weakness
    subject_pool = []
    for subject, days_count in days_per_subject.items():
        subject_pool.extend([subject] * days_count)
    
    # Shuffle for variety while maintaining distribution
    np.random.seed(42)  # For reproducibility
    np.random.shuffle(subject_pool)
    
    # Track which subjects are assigned to which days
    subject_assignments = {day: [] for day in days[:-1]}  # Exclude Sunday initially
    
    # Distribute subjects across days ensuring variety
    pool_index = 0
    for day in days[:-1]:  # Monday to Saturday
        sessions_for_day = min(max_sessions_per_day, 4)  # Cap at 4 subjects per day
        day_subjects = []
        
        # Try to assign different subjects to this day
        attempts = 0
        while len(day_subjects) < sessions_for_day and pool_index < len(subject_pool) and attempts < 20:
            subject = subject_pool[pool_index % len(subject_pool)]
            
            # Avoid too many repetitions of same subject in one day
            if day_subjects.count(subject) < 2:  # Max 2 sessions of same subject per day
                day_subjects.append(subject)
                pool_index += 1
            else:
                pool_index += 1
                
            attempts += 1
        
        subject_assignments[day] = day_subjects
    
    # Generate time slots for each day
    for day in days[:-1]:  # Monday to Saturday
        slots = []
        
        # Morning routine
        routine_start = wake_dt
        routine_end = routine_start + timedelta(minutes=morning_routine_duration)
        slots.append({
            'time': f"{routine_start.strftime('%H:%M')} - {routine_end.strftime('%H:%M')}",
            'subject': '🌅 Morning Routine (Freshen up, Exercise)',
            'type': 'Routine',
            'duration': morning_routine_duration / 60
        })
        
        # Breakfast
        breakfast_end = breakfast_dt + timedelta(minutes=breakfast_duration)
        slots.append({
            'time': f"{breakfast_dt.strftime('%H:%M')} - {breakfast_end.strftime('%H:%M')}",
            'subject': '🍳 Breakfast',
            'type': 'Meal',
            'duration': breakfast_duration / 60
        })
        
        # Start study sessions after breakfast
        current_time = breakfast_end
        subjects_today = subject_assignments[day]
        
        for i, subject in enumerate(subjects_today):
            # Check if we need to insert lunch
            session_end = current_time + timedelta(hours=session_duration)
            
            # If current session would overlap with lunch, insert lunch first
            if current_time < lunch_dt < session_end or (current_time < lunch_dt and (lunch_dt - current_time).total_seconds() / 3600 < 0.5):
                lunch_end = lunch_dt + timedelta(minutes=lunch_duration)
                slots.append({
                    'time': f"{lunch_dt.strftime('%H:%M')} - {lunch_end.strftime('%H:%M')}",
                    'subject': '🍛 Lunch',
                    'type': 'Meal',
                    'duration': lunch_duration / 60
                })
                current_time = lunch_end
                session_end = current_time + timedelta(hours=session_duration)
            
            # Check if we need to insert dinner
            if current_time < dinner_dt < session_end or (current_time < dinner_dt and (dinner_dt - current_time).total_seconds() / 3600 < 0.5):
                dinner_end = dinner_dt + timedelta(minutes=dinner_duration)
                slots.append({
                    'time': f"{dinner_dt.strftime('%H:%M')} - {dinner_end.strftime('%H:%M')}",
                    'subject': '🍽️ Dinner',
                    'type': 'Meal',
                    'duration': dinner_duration / 60
                })
                current_time = dinner_end
                session_end = current_time + timedelta(hours=session_duration)
            
            # Add study session
            slots.append({
                'time': f"{current_time.strftime('%H:%M')} - {session_end.strftime('%H:%M')}",
                'subject': subject,
                'type': 'Study',
                'duration': session_duration
            })
            
            current_time = session_end
            
            # Add short break after each session (except the last one)
            if i < len(subjects_today) - 1:
                break_end = current_time + timedelta(minutes=break_duration)
                slots.append({
                    'time': f"{current_time.strftime('%H:%M')} - {break_end.strftime('%H:%M')}",
                    'subject': '☕ Break',
                    'type': 'Break',
                    'duration': break_duration / 60
                })
                current_time = break_end
        
        # Ensure dinner is included if not yet added
        if not any(slot['type'] == 'Meal' and 'Dinner' in slot['subject'] for slot in slots):
            if current_time < dinner_dt:
                # Add remaining study or free time
                if (dinner_dt - current_time).total_seconds() / 3600 >= 1:
                    slots.append({
                        'time': f"{current_time.strftime('%H:%M')} - {dinner_dt.strftime('%H:%M')}",
                        'subject': '🎯 Self-Study / Review',
                        'type': 'Study',
                        'duration': (dinner_dt - current_time).total_seconds() / 3600
                    })
                
                dinner_end = dinner_dt + timedelta(minutes=dinner_duration)
                slots.append({
                    'time': f"{dinner_dt.strftime('%H:%M')} - {dinner_end.strftime('%H:%M')}",
                    'subject': '🍽️ Dinner',
                    'type': 'Meal',
                    'duration': dinner_duration / 60
                })
        
        timetable[day] = slots
    
    # Sunday - Revision and Assessment with meals
    weak_subjects = predictions.nlargest(3, 'weakness_score')['subject'].tolist()
    
    routine_end = wake_dt + timedelta(minutes=morning_routine_duration)
    breakfast_end = breakfast_dt + timedelta(minutes=breakfast_duration)
    
    sunday_slots = [
        {'time': f"{wake_dt.strftime('%H:%M')} - {routine_end.strftime('%H:%M')}", 
         'subject': '🌅 Morning Routine', 'type': 'Routine', 'duration': morning_routine_duration / 60},
        {'time': f"{breakfast_dt.strftime('%H:%M')} - {breakfast_end.strftime('%H:%M')}", 
         'subject': '🍳 Breakfast', 'type': 'Meal', 'duration': breakfast_duration / 60},
        {'time': f"{breakfast_end.strftime('%H:%M')} - {(breakfast_end + timedelta(hours=1.5)).strftime('%H:%M')}", 
         'subject': f'📚 Revision: {weak_subjects[0]}', 'type': 'Revision', 'duration': 1.5},
        {'time': f"{(breakfast_end + timedelta(hours=1.5)).strftime('%H:%M')} - {(breakfast_end + timedelta(hours=2)).strftime('%H:%M')}", 
         'subject': '☕ Break', 'type': 'Break', 'duration': 0.5},
        {'time': f"{(breakfast_end + timedelta(hours=2)).strftime('%H:%M')} - {(breakfast_end + timedelta(hours=3.5)).strftime('%H:%M')}", 
         'subject': f'📚 Revision: {weak_subjects[1] if len(weak_subjects) > 1 else weak_subjects[0]}', 
         'type': 'Revision', 'duration': 1.5},
        {'time': f"{lunch_dt.strftime('%H:%M')} - {(lunch_dt + timedelta(minutes=lunch_duration)).strftime('%H:%M')}", 
         'subject': '🍛 Lunch', 'type': 'Meal', 'duration': lunch_duration / 60},
        {'time': f"{(lunch_dt + timedelta(minutes=lunch_duration)).strftime('%H:%M')} - {(lunch_dt + timedelta(minutes=lunch_duration, hours=2)).strftime('%H:%M')}", 
         'subject': '📝 Mock Test / Practice Problems', 'type': 'Assessment', 'duration': 2.0},
        {'time': f"{dinner_dt.strftime('%H:%M')} - {(dinner_dt + timedelta(minutes=dinner_duration)).strftime('%H:%M')}", 
         'subject': '🍽️ Dinner', 'type': 'Meal', 'duration': dinner_duration / 60},
        {'time': f"{(dinner_dt + timedelta(minutes=dinner_duration)).strftime('%H:%M')} - {sleep_dt.strftime('%H:%M')}", 
         'subject': '🎮 Leisure / Relaxation', 'type': 'Free', 'duration': (sleep_dt - (dinner_dt + timedelta(minutes=dinner_duration))).total_seconds() / 3600}
    ]
    
    timetable['Sunday'] = sunday_slots
    
    return timetable

def display_timetable(timetable):
    """Display the generated timetable with statistics"""
    st.markdown("---")
    st.subheader("📅 Your Personalized Weekly Timetable")
    
    # Calculate weekly statistics
    total_study_hours = 0
    subject_hours = {}
    
    for day, slots in timetable.items():
        for slot in slots:
            if slot['type'] in ['Study', 'Revision', 'Assessment']:
                duration = slot.get('duration', 1.0)
                total_study_hours += duration
                
                # Extract subject name (remove "Revision: " prefix if present)
                subject = slot['subject'].replace('Revision: ', '').replace('Mock Test / Practice Problems', 'Assessment')
                subject_hours[subject] = subject_hours.get(subject, 0) + duration
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Study Hours", f"{total_study_hours:.1f} hrs")
    with col2:
        st.metric("📚 Study Days", "6 days")
    with col3:
        st.metric("📝 Subjects Covered", len([s for s in subject_hours.keys() if s != 'Assessment']))
    
    # Show subject-wise breakdown
    if subject_hours:
        st.markdown("#### 📊 Subject-wise Study Hours")
        subject_df = pd.DataFrame([
            {'Subject': subject, 'Hours': hours} 
            for subject, hours in sorted(subject_hours.items(), key=lambda x: x[1], reverse=True)
        ])
        st.dataframe(subject_df, use_container_width=True)
    
    st.markdown("---")
    
    # Display daily timetable
    for day, slots in timetable.items():
        with st.expander(f"📆 {day}", expanded=(day == 'Monday')):
            if slots:
                for slot in slots:
                    slot_type = slot['type']
                    duration = slot.get('duration', 1.0)
                    duration_str = f"({duration:.1f}h)" if duration >= 1 else f"({int(duration*60)}min)"
                    
                    if slot_type == 'Routine':
                        st.info(f"🌅 {slot['time']} {duration_str} - **{slot['subject']}**")
                    elif slot_type == 'Meal':
                        st.success(f"🍽️ {slot['time']} {duration_str} - **{slot['subject']}**")
                    elif slot_type == 'Break':
                        st.info(f"☕ {slot['time']} {duration_str} - **{slot['subject']}**")
                    elif slot_type == 'Revision':
                        st.warning(f"📚 {slot['time']} {duration_str} - **{slot['subject']}**")
                    elif slot_type == 'Assessment':
                        st.error(f"📝 {slot['time']} {duration_str} - **{slot['subject']}**")
                    elif slot_type == 'Free':
                        st.success(f"🎮 {slot['time']} {duration_str} - **{slot['subject']}**")
                    else:
                        st.write(f"📖 {slot['time']} {duration_str} - **{slot['subject']}**")
            else:
                st.write("No sessions scheduled")
    
    # Download option
    st.markdown("---")
    if st.button("📥 Download Timetable as Text"):
        timetable_text = generate_timetable_text(timetable)
        st.download_button(
            label="Download",
            data=timetable_text,
            file_name="study_timetable.txt",
            mime="text/plain"
        )

def generate_timetable_text(timetable):
    """Generate a text version of the timetable for download"""
    text = "📅 WEEKLY STUDY TIMETABLE\n"
    text += "=" * 50 + "\n\n"
    
    for day, slots in timetable.items():
        text += f"{day.upper()}\n"
        text += "-" * 50 + "\n"
        if slots:
            for slot in slots:
                duration = slot.get('duration', 1.0)
                duration_str = f" ({duration:.1f}h)"
                text += f"{slot['time']}{duration_str} - {slot['subject']}\n"
        else:
            text += "No sessions scheduled\n"
        text += "\n"
    
    return text