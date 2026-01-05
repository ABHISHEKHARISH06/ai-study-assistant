import pandas as pd
import os
from pathlib import Path

class DataHandler:
    """Handle data persistence with CSV"""
    
    def __init__(self, data_file='study_data.csv'):
        self.data_file = data_file
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Create empty CSV if it doesn't exist"""
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'subject', 'study_hours', 'previous_score', 
                'days_before_exam', 'difficulty', 'final_score'
            ])
            df.to_csv(self.data_file, index=False)
    
    def load_data(self):
        """Load data from CSV"""
        try:
            df = pd.read_csv(self.data_file)
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame(columns=[
                'subject', 'study_hours', 'previous_score', 
                'days_before_exam', 'difficulty', 'final_score'
            ])
    
    def add_record(self, subject, study_hours, previous_score, 
                   days_before_exam, difficulty, final_score):
        """Add a new record"""
        try:
            df = self.load_data()
            
            new_record = pd.DataFrame([{
                'subject': subject,
                'study_hours': study_hours,
                'previous_score': previous_score,
                'days_before_exam': days_before_exam,
                'difficulty': difficulty,
                'final_score': final_score
            }])
            
            df = pd.concat([df, new_record], ignore_index=True)
            df.to_csv(self.data_file, index=False)
            
            return True
        except Exception as e:
            print(f"Error adding record: {e}")
            return False
    
    def clear_data(self):
        """Clear all data"""
        try:
            df = pd.DataFrame(columns=[
                'subject', 'study_hours', 'previous_score', 
                'days_before_exam', 'difficulty', 'final_score'
            ])
            df.to_csv(self.data_file, index=False)
            return True
        except Exception as e:
            print(f"Error clearing data: {e}")
            return False
