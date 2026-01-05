import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class MLScheduler:
    """ML-based study scheduler and score predictor"""
    
    def __init__(self):
        self.lr_model = None
        self.rf_model = None
        self.encoder = None
        self.feature_columns = None
        self.best_model = None
    
    def prepare_features(self, data):
        """Prepare features with one-hot encoding for subjects"""
        df = data.copy()
        
        # One-hot encode subject
        if self.encoder is None:
            self.encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            subject_encoded = self.encoder.fit_transform(df[['subject']])
        else:
            subject_encoded = self.encoder.transform(df[['subject']])
        
        # Create feature names
        subject_features = [f'subject_{cat}' for cat in self.encoder.categories_[0]]
        
        # Combine with numerical features
        numerical_features = ['study_hours', 'previous_score', 'days_before_exam', 'difficulty']
        
        X = np.hstack([
            subject_encoded,
            df[numerical_features].values
        ])
        
        self.feature_columns = subject_features + numerical_features
        
        return X
    
    def train_models(self, data):
        """Train Linear Regression and Random Forest models"""
        # Prepare data
        X = self.prepare_features(data)
        y = data['final_score'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Linear Regression
        self.lr_model = LinearRegression()
        self.lr_model.fit(X_train, y_train)
        lr_pred = self.lr_model.predict(X_test)
        lr_rmse = np.sqrt(mean_squared_error(y_test, lr_pred))
        
        # Train Random Forest
        self.rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.rf_model.fit(X_train, y_train)
        rf_pred = self.rf_model.predict(X_test)
        rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
        
        # Select best model
        if rf_rmse < lr_rmse:
            self.best_model = self.rf_model
            best_rmse = rf_rmse
        else:
            self.best_model = self.lr_model
            best_rmse = lr_rmse
        
        return {
            'lr_rmse': lr_rmse,
            'rf_rmse': rf_rmse,
            'best_rmse': best_rmse,
            'best_model': 'Random Forest' if rf_rmse < lr_rmse else 'Linear Regression'
        }
    
    def predict_score(self, record):
        """Predict score for a single record"""
        if self.best_model is None:
            return 0
        
        # Convert to DataFrame for consistent processing
        df = pd.DataFrame([{
            'subject': record['subject'],
            'study_hours': record['study_hours'],
            'previous_score': record['previous_score'],
            'days_before_exam': record['days_before_exam'],
            'difficulty': record['difficulty']
        }])
        
        X = self.prepare_features(df)
        prediction = self.best_model.predict(X)[0]
        
        # Return score range (clip to 0-100)
        return max(0, min(100, prediction))
