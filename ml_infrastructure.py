"""
ML Infrastructure for DLR Power System Analysis
Comprehensive machine learning framework for predictive analysis, classification, clustering,
and model monitoring with integration to existing DLR visualization system.
"""

import pandas as pd
import numpy as np
import sqlite3
import joblib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Any, Optional

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.svm import SVR, SVC
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    classification_report, confusion_matrix, silhouette_score
)
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_infrastructure.log'),
        logging.StreamHandler()
    ]
)

class MLInfrastructure:
    """Comprehensive ML Infrastructure for DLR Analysis"""
    
    def __init__(self, database_path: str, models_dir: str = "models"):
        self.database_path = database_path
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Model storage
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
        # Performance tracking
        self.model_performance = {}
        self.prediction_history = []
        
        # Connect to database
        self.conn = None
        self.connect_database()
        
        logging.info(f"ML Infrastructure initialized with database: {database_path}")
    
    def connect_database(self):
        """Connect to SQLite database"""
        try:
            self.conn = sqlite3.connect(self.database_path)
            logging.info("Database connection established")
            return True
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            return False
    
    def disconnect_database(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")

class PowerSystemDataProcessor:
    """Data preprocessing and feature engineering for power system data"""
    
    def __init__(self, ml_infrastructure: MLInfrastructure):
        self.ml = ml_infrastructure
    
    def extract_features(self, base_case_ids: List[int] = None) -> pd.DataFrame:
        """Extract comprehensive features from power system data"""
        try:
            if base_case_ids is None:
                # Get all available case IDs
                query = "SELECT DISTINCT base_case_id FROM BaseBusData ORDER BY base_case_id"
                case_df = pd.read_sql_query(query, self.ml.conn)
                base_case_ids = case_df['base_case_id'].tolist()[:100]  # Limit for performance
            
            features_list = []
            
            for case_id in base_case_ids:
                # Extract bus data features
                bus_features = self._extract_bus_features(case_id)
                
                # Extract branch data features
                branch_features = self._extract_branch_features(case_id)
                
                # Extract SLR/DLR features if available
                slr_features = self._extract_slr_features(case_id)
                dlr_features = self._extract_dlr_features(case_id)
                
                # Combine all features
                case_features = {
                    'case_id': case_id,
                    'timestamp': datetime.now(),
                    **bus_features,
                    **branch_features,
                    **slr_features,
                    **dlr_features
                }
                
                features_list.append(case_features)
            
            features_df = pd.DataFrame(features_list)
            logging.info(f"Extracted {len(features_df)} feature sets with {len(features_df.columns)} features")
            
            return features_df
            
        except Exception as e:
            logging.error(f"Error extracting features: {e}")
            return pd.DataFrame()
    
    def _extract_bus_features(self, case_id: int) -> Dict:
        """Extract bus-level features"""
        query = f"""
        SELECT VM, VA, PG, QG, PD, QD, BASE_KV
        FROM BaseBusData 
        WHERE base_case_id = {case_id}
        """
        
        df = pd.read_sql_query(query, self.ml.conn)
        
        if df.empty:
            return {}
        
        return {
            # Voltage features
            'voltage_mean': df['VM'].mean(),
            'voltage_std': df['VM'].std(),
            'voltage_min': df['VM'].min(),
            'voltage_max': df['VM'].max(),
            'voltage_range': df['VM'].max() - df['VM'].min(),
            'voltage_violations': len(df[(df['VM'] < 0.95) | (df['VM'] > 1.05)]),
            'voltage_violation_ratio': len(df[(df['VM'] < 0.95) | (df['VM'] > 1.05)]) / len(df),
            
            # Power generation features
            'total_generation': df['PG'].sum(),
            'max_generation': df['PG'].max(),
            'generation_diversity': (df['PG'] > 0).sum() / len(df),
            'reactive_generation': df['QG'].sum(),
            
            # Load features
            'total_load': df['PD'].sum(),
            'max_load': df['PD'].max(),
            'load_diversity': (df['PD'] > 0).sum() / len(df),
            'reactive_load': df['QD'].sum(),
            
            # System balance
            'power_balance': abs(df['PG'].sum() - df['PD'].sum()),
            'reactive_balance': abs(df['QG'].sum() - df['QD'].sum()),
            'gen_load_ratio': df['PG'].sum() / df['PD'].sum() if df['PD'].sum() > 0 else 0,
            
            # Network characteristics
            'bus_count': len(df),
            'avg_base_kv': df['BASE_KV'].mean(),
            'voltage_level_diversity': df['BASE_KV'].nunique()
        }
    
    def _extract_branch_features(self, case_id: int) -> Dict:
        """Extract branch-level features"""
        # Note: This assumes branch data is linked to case_id via file_id
        # You might need to adjust the query based on your schema
        query = f"""
        SELECT b.PF, b.QF, b.MVA, b.RATE, b.VIO
        FROM BaseBranchData b
        JOIN BaseCaseFiles f ON b.file_id = f.Id
        WHERE f.scenario_id = {case_id}
        """
        
        try:
            df = pd.read_sql_query(query, self.ml.conn)
            
            if df.empty:
                return {}
            
            return {
                # Power flow features
                'total_power_flow': df['PF'].abs().sum(),
                'max_power_flow': df['PF'].abs().max(),
                'power_flow_std': df['PF'].std(),
                
                # Loading features
                'avg_loading': df['MVA'].mean(),
                'max_loading': df['MVA'].max(),
                'overloaded_branches': (df['VIO'] > 0).sum(),
                'overload_ratio': (df['VIO'] > 0).sum() / len(df),
                
                # System stress
                'branch_count': len(df),
                'avg_utilization': (df['MVA'] / df['RATE']).mean() if (df['RATE'] > 0).any() else 0,
                'max_utilization': (df['MVA'] / df['RATE']).max() if (df['RATE'] > 0).any() else 0
            }
        except:
            return {}
    
    def _extract_slr_features(self, case_id: int) -> Dict:
        """Extract SLR-specific features"""
        # Generator adjustments
        gen_query = f"""
        SELECT MW_CHANGE FROM SLR_Generator 
        WHERE base_case_id = {case_id}
        """
        
        # Load adjustments
        load_query = f"""
        SELECT MW_CHANGE FROM SLR_Load 
        WHERE base_case_id = {case_id}
        """
        
        try:
            gen_df = pd.read_sql_query(gen_query, self.ml.conn)
            load_df = pd.read_sql_query(load_query, self.ml.conn)
            
            features = {}
            
            if not gen_df.empty:
                features.update({
                    'slr_gen_adjustments': len(gen_df),
                    'slr_total_gen_change': gen_df['MW_CHANGE'].abs().sum(),
                    'slr_max_gen_change': gen_df['MW_CHANGE'].abs().max()
                })
            
            if not load_df.empty:
                features.update({
                    'slr_load_adjustments': len(load_df),
                    'slr_total_load_change': load_df['MW_CHANGE'].abs().sum(),
                    'slr_max_load_change': load_df['MW_CHANGE'].abs().max()
                })
            
            return features
            
        except:
            return {}
    
    def _extract_dlr_features(self, case_id: int) -> Dict:
        """Extract DLR-specific features"""
        # Generator adjustments
        gen_query = f"""
        SELECT MW_CHANGE FROM DLR_Generator 
        WHERE base_case_id = {case_id}
        """
        
        # Load adjustments
        load_query = f"""
        SELECT MW_CHANGE FROM DLR_Load 
        WHERE base_case_id = {case_id}
        """
        
        try:
            gen_df = pd.read_sql_query(gen_query, self.ml.conn)
            load_df = pd.read_sql_query(load_query, self.ml.conn)
            
            features = {}
            
            if not gen_df.empty:
                features.update({
                    'dlr_gen_adjustments': len(gen_df),
                    'dlr_total_gen_change': gen_df['MW_CHANGE'].abs().sum(),
                    'dlr_max_gen_change': gen_df['MW_CHANGE'].abs().max()
                })
            
            if not load_df.empty:
                features.update({
                    'dlr_load_adjustments': len(load_df),
                    'dlr_total_load_change': load_df['MW_CHANGE'].abs().sum(),
                    'dlr_max_load_change': load_df['MW_CHANGE'].abs().max()
                })
            
            return features
            
        except:
            return {}

class PredictiveAnalysisModel:
    """Predictive analysis models for power system forecasting"""
    
    def __init__(self, ml_infrastructure: MLInfrastructure):
        self.ml = ml_infrastructure
        self.processor = PowerSystemDataProcessor(ml_infrastructure)
    
    def train_voltage_prediction_model(self, lookback_days: int = 30) -> Dict:
        """Train model to predict voltage violations"""
        try:
            # Extract features
            features_df = self.processor.extract_features()
            
            if features_df.empty:
                return {'error': 'No data available for training'}
            
            # Prepare data for voltage prediction
            X = features_df.select_dtypes(include=[np.number]).drop(['case_id', 'voltage_violations'], axis=1, errors='ignore')
            y = features_df['voltage_violations'] if 'voltage_violations' in features_df.columns else np.zeros(len(features_df))
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train multiple models
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'linear_regression': LinearRegression(),
                'svr': SVR(kernel='rbf')
            }
            
            results = {}
            best_model = None
            best_score = float('-inf')
            
            for name, model in models.items():
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Predict
                y_pred = model.predict(X_test_scaled)
                
                # Evaluate
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                results[name] = {
                    'mse': mse,
                    'mae': mae,
                    'r2': r2,
                    'model': model
                }
                
                if r2 > best_score:
                    best_score = r2
                    best_model = name
            
            # Save best model
            self.ml.models['voltage_prediction'] = models[best_model]
            self.ml.scalers['voltage_prediction'] = scaler
            
            # Save model to disk
            model_path = self.ml.models_dir / 'voltage_prediction_model.joblib'
            scaler_path = self.ml.models_dir / 'voltage_prediction_scaler.joblib'
            
            joblib.dump(models[best_model], model_path)
            joblib.dump(scaler, scaler_path)
            
            logging.info(f"Voltage prediction model trained. Best model: {best_model} (R²: {best_score:.3f})")
            
            return {
                'best_model': best_model,
                'best_score': best_score,
                'results': results,
                'feature_names': list(X.columns),
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logging.error(f"Error training voltage prediction model: {e}")
            return {'error': str(e)}
    
    def train_load_forecasting_model(self) -> Dict:
        """Train model for load forecasting"""
        try:
            features_df = self.processor.extract_features()
            
            if features_df.empty:
                return {'error': 'No data available for training'}
            
            # Prepare data for load forecasting
            X = features_df.select_dtypes(include=[np.number]).drop(['case_id', 'total_load'], axis=1, errors='ignore')
            y = features_df['total_load'] if 'total_load' in features_df.columns else np.zeros(len(features_df))
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Random Forest model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Predict and evaluate
            y_pred = model.predict(X_test_scaled)
            
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Save model
            self.ml.models['load_forecasting'] = model
            self.ml.scalers['load_forecasting'] = scaler
            
            model_path = self.ml.models_dir / 'load_forecasting_model.joblib'
            scaler_path = self.ml.models_dir / 'load_forecasting_scaler.joblib'
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            logging.info(f"Load forecasting model trained (R²: {r2:.3f})")
            
            return {
                'mse': mse,
                'mae': mae,
                'r2': r2,
                'feature_importance': dict(zip(X.columns, model.feature_importances_)),
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logging.error(f"Error training load forecasting model: {e}")
            return {'error': str(e)}

class ClassificationClusteringModel:
    """Classification and clustering models for power system analysis"""
    
    def __init__(self, ml_infrastructure: MLInfrastructure):
        self.ml = ml_infrastructure
        self.processor = PowerSystemDataProcessor(ml_infrastructure)
    
    def classify_system_states(self) -> Dict:
        """Classify power system states (normal, alert, emergency)"""
        try:
            features_df = self.processor.extract_features()
            
            if features_df.empty:
                return {'error': 'No data available for classification'}
            
            # Create labels based on system conditions
            def create_state_labels(row):
                if row.get('voltage_violation_ratio', 0) > 0.1 or row.get('overload_ratio', 0) > 0.05:
                    return 'emergency'
                elif row.get('voltage_violation_ratio', 0) > 0.05 or row.get('overload_ratio', 0) > 0.02:
                    return 'alert'
                else:
                    return 'normal'
            
            features_df['system_state'] = features_df.apply(create_state_labels, axis=1)
            
            # Prepare features
            X = features_df.select_dtypes(include=[np.number]).drop(['case_id'], axis=1, errors='ignore')
            y = features_df['system_state']
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Encode labels
            label_encoder = LabelEncoder()
            y_encoded = label_encoder.fit_transform(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Random Forest classifier
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Predict and evaluate
            y_pred = model.predict(X_test_scaled)
            
            # Classification report
            report = classification_report(y_test, y_pred, target_names=label_encoder.classes_, output_dict=True)
            
            # Save model
            self.ml.models['state_classification'] = model
            self.ml.scalers['state_classification'] = scaler
            self.ml.encoders['state_classification'] = label_encoder
            
            model_path = self.ml.models_dir / 'state_classification_model.joblib'
            scaler_path = self.ml.models_dir / 'state_classification_scaler.joblib'
            encoder_path = self.ml.models_dir / 'state_classification_encoder.joblib'
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            joblib.dump(label_encoder, encoder_path)
            
            logging.info(f"State classification model trained. Accuracy: {report['accuracy']:.3f}")
            
            return {
                'accuracy': report['accuracy'],
                'classification_report': report,
                'feature_importance': dict(zip(X.columns, model.feature_importances_)),
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logging.error(f"Error training classification model: {e}")
            return {'error': str(e)}
    
    def cluster_operating_patterns(self, n_clusters: int = 5) -> Dict:
        """Cluster power system operating patterns"""
        try:
            features_df = self.processor.extract_features()
            
            if features_df.empty:
                return {'error': 'No data available for clustering'}
            
            # Prepare features for clustering
            X = features_df.select_dtypes(include=[np.number]).drop(['case_id'], axis=1, errors='ignore')
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Apply K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Calculate silhouette score
            silhouette_avg = silhouette_score(X_scaled, cluster_labels)
            
            # Apply DBSCAN for comparison
            dbscan = DBSCAN(eps=0.5, min_samples=5)
            dbscan_labels = dbscan.fit_predict(X_scaled)
            
            # PCA for visualization
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            # Save clustering models
            self.ml.models['kmeans_clustering'] = kmeans
            self.ml.models['dbscan_clustering'] = dbscan
            self.ml.scalers['clustering'] = scaler
            
            # Analyze clusters
            features_df['kmeans_cluster'] = cluster_labels
            features_df['dbscan_cluster'] = dbscan_labels
            
            cluster_analysis = {}
            for i in range(n_clusters):
                cluster_data = features_df[features_df['kmeans_cluster'] == i]
                cluster_analysis[f'cluster_{i}'] = {
                    'size': len(cluster_data),
                    'avg_voltage_violations': cluster_data['voltage_violations'].mean() if 'voltage_violations' in cluster_data.columns else 0,
                    'avg_total_load': cluster_data['total_load'].mean() if 'total_load' in cluster_data.columns else 0,
                    'characteristics': self._analyze_cluster_characteristics(cluster_data)
                }
            
            logging.info(f"Clustering completed. Silhouette score: {silhouette_avg:.3f}")
            
            return {
                'kmeans_silhouette_score': silhouette_avg,
                'n_clusters': n_clusters,
                'dbscan_clusters': len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0),
                'cluster_analysis': cluster_analysis,
                'pca_components': X_pca,
                'pca_explained_variance': pca.explained_variance_ratio_
            }
            
        except Exception as e:
            logging.error(f"Error in clustering analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_cluster_characteristics(self, cluster_data: pd.DataFrame) -> Dict:
        """Analyze characteristics of a cluster"""
        numeric_cols = cluster_data.select_dtypes(include=[np.number]).columns
        
        characteristics = {}
        for col in numeric_cols:
            if col not in ['case_id', 'kmeans_cluster', 'dbscan_cluster']:
                characteristics[col] = {
                    'mean': cluster_data[col].mean(),
                    'std': cluster_data[col].std(),
                    'min': cluster_data[col].min(),
                    'max': cluster_data[col].max()
                }
        
        return characteristics

class ModelMonitoringOptimization:
    """Model monitoring and optimization framework"""
    
    def __init__(self, ml_infrastructure: MLInfrastructure):
        self.ml = ml_infrastructure
        self.monitoring_data = []
    
    def monitor_model_performance(self, model_name: str, new_data: pd.DataFrame, true_values: np.ndarray = None) -> Dict:
        """Monitor model performance over time"""
        try:
            if model_name not in self.ml.models:
                return {'error': f'Model {model_name} not found'}
            
            model = self.ml.models[model_name]
            scaler = self.ml.scalers.get(model_name)
            
            # Prepare data
            X = new_data.select_dtypes(include=[np.number])
            X = X.fillna(X.mean())
            
            if scaler:
                X_scaled = scaler.transform(X)
            else:
                X_scaled = X
            
            # Make predictions
            predictions = model.predict(X_scaled)
            
            # Calculate performance metrics if true values available
            metrics = {}
            if true_values is not None:
                if hasattr(model, 'predict_proba'):  # Classification
                    # For classification models
                    accuracy = (predictions == true_values).mean()
                    metrics['accuracy'] = accuracy
                else:  # Regression
                    mse = mean_squared_error(true_values, predictions)
                    mae = mean_absolute_error(true_values, predictions)
                    r2 = r2_score(true_values, predictions)
                    
                    metrics.update({
                        'mse': mse,
                        'mae': mae,
                        'r2': r2
                    })
            
            # Data drift detection (simplified)
            drift_score = self._detect_data_drift(X_scaled, model_name)
            
            # Record monitoring data
            monitoring_record = {
                'timestamp': datetime.now(),
                'model_name': model_name,
                'n_samples': len(predictions),
                'metrics': metrics,
                'drift_score': drift_score,
                'predictions_stats': {
                    'mean': predictions.mean(),
                    'std': predictions.std(),
                    'min': predictions.min(),
                    'max': predictions.max()
                }
            }
            
            self.monitoring_data.append(monitoring_record)
            
            # Save monitoring data
            self._save_monitoring_data()
            
            logging.info(f"Model {model_name} monitored. Drift score: {drift_score:.3f}")
            
            return monitoring_record
            
        except Exception as e:
            logging.error(f"Error monitoring model {model_name}: {e}")
            return {'error': str(e)}
    
    def _detect_data_drift(self, new_data: np.ndarray, model_name: str) -> float:
        """Simple data drift detection using statistical measures"""
        try:
            # Load historical data statistics (simplified)
            # In practice, you'd maintain running statistics
            historical_mean = new_data.mean(axis=0)
            historical_std = new_data.std(axis=0)
            
            # Calculate drift score as relative change in distribution
            current_mean = new_data.mean(axis=0)
            current_std = new_data.std(axis=0)
            
            mean_drift = np.abs((current_mean - historical_mean) / (historical_std + 1e-8))
            std_drift = np.abs((current_std - historical_std) / (historical_std + 1e-8))
            
            drift_score = (mean_drift + std_drift).mean()
            
            return float(drift_score)
            
        except:
            return 0.0
    
    def optimize_hyperparameters(self, model_name: str, param_grid: Dict) -> Dict:
        """Optimize model hyperparameters"""
        try:
            # Re-extract features for optimization
            processor = PowerSystemDataProcessor(self.ml)
            features_df = processor.extract_features()
            
            if features_df.empty:
                return {'error': 'No data available for optimization'}
            
            # Prepare data based on model type
            if model_name == 'voltage_prediction':
                X = features_df.select_dtypes(include=[np.number]).drop(['case_id', 'voltage_violations'], axis=1, errors='ignore')
                y = features_df['voltage_violations'] if 'voltage_violations' in features_df.columns else np.zeros(len(features_df))
                
                # Use appropriate model
                if 'random_forest' in param_grid:
                    base_model = RandomForestRegressor(random_state=42)
                else:
                    base_model = LinearRegression()
                    
            elif model_name == 'state_classification':
                X = features_df.select_dtypes(include=[np.number]).drop(['case_id'], axis=1, errors='ignore')
                
                # Create labels
                def create_state_labels(row):
                    if row.get('voltage_violation_ratio', 0) > 0.1:
                        return 'emergency'
                    elif row.get('voltage_violation_ratio', 0) > 0.05:
                        return 'alert'
                    else:
                        return 'normal'
                
                y = features_df.apply(create_state_labels, axis=1)
                
                label_encoder = LabelEncoder()
                y = label_encoder.fit_transform(y)
                
                base_model = RandomForestClassifier(random_state=42)
            
            else:
                return {'error': f'Optimization not implemented for {model_name}'}
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Grid search with cross-validation
            grid_search = GridSearchCV(
                base_model,
                param_grid,
                cv=5,
                scoring='r2' if 'prediction' in model_name else 'accuracy',
                n_jobs=-1
            )
            
            grid_search.fit(X_scaled, y)
            
            # Update model with best parameters
            best_model = grid_search.best_estimator_
            self.ml.models[model_name] = best_model
            
            # Save optimized model
            model_path = self.ml.models_dir / f'{model_name}_optimized.joblib'
            joblib.dump(best_model, model_path)
            
            logging.info(f"Model {model_name} optimized. Best score: {grid_search.best_score_:.3f}")
            
            return {
                'best_params': grid_search.best_params_,
                'best_score': grid_search.best_score_,
                'cv_results': grid_search.cv_results_,
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logging.error(f"Error optimizing model {model_name}: {e}")
            return {'error': str(e)}
    
    def _save_monitoring_data(self):
        """Save monitoring data to file"""
        try:
            monitoring_file = self.ml.models_dir / 'monitoring_data.json'
            
            # Convert datetime objects to strings for JSON serialization
            serializable_data = []
            for record in self.monitoring_data:
                record_copy = record.copy()
                record_copy['timestamp'] = record_copy['timestamp'].isoformat()
                serializable_data.append(record_copy)
            
            with open(monitoring_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving monitoring data: {e}")
    
    def generate_monitoring_report(self) -> Dict:
        """Generate comprehensive monitoring report"""
        try:
            if not self.monitoring_data:
                return {'error': 'No monitoring data available'}
            
            # Analyze performance trends
            performance_trends = {}
            
            for model_name in set(record['model_name'] for record in self.monitoring_data):
                model_records = [r for r in self.monitoring_data if r['model_name'] == model_name]
                
                if model_records:
                    latest_record = model_records[-1]
                    
                    performance_trends[model_name] = {
                        'latest_metrics': latest_record['metrics'],
                        'latest_drift_score': latest_record['drift_score'],
                        'total_predictions': sum(r['n_samples'] for r in model_records),
                        'avg_drift_score': np.mean([r['drift_score'] for r in model_records]),
                        'monitoring_periods': len(model_records)
                    }
            
            # Overall system health
            avg_drift = np.mean([r['drift_score'] for r in self.monitoring_data])
            
            health_status = 'healthy' if avg_drift < 0.1 else 'warning' if avg_drift < 0.3 else 'critical'
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_health': health_status,
                'avg_drift_score': avg_drift,
                'performance_trends': performance_trends,
                'total_monitoring_records': len(self.monitoring_data),
                'recommendations': self._generate_recommendations(performance_trends, avg_drift)
            }
            
            return report
            
        except Exception as e:
            logging.error(f"Error generating monitoring report: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, performance_trends: Dict, avg_drift: float) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if avg_drift > 0.3:
            recommendations.append("High data drift detected. Consider retraining models with recent data.")
        
        for model_name, trends in performance_trends.items():
            if trends['latest_drift_score'] > 0.5:
                recommendations.append(f"Model {model_name} shows significant drift. Schedule retraining.")
            
            if 'accuracy' in trends['latest_metrics'] and trends['latest_metrics']['accuracy'] < 0.8:
                recommendations.append(f"Model {model_name} accuracy below threshold. Review feature engineering.")
            
            if 'r2' in trends['latest_metrics'] and trends['latest_metrics']['r2'] < 0.7:
                recommendations.append(f"Model {model_name} R² score below threshold. Consider model optimization.")
        
        if not recommendations:
            recommendations.append("All models performing within acceptable parameters.")
        
        return recommendations

class MLVisualization:
    """Visualization tools for ML models and results"""
    
    def __init__(self, ml_infrastructure: MLInfrastructure):
        self.ml = ml_infrastructure
    
    def create_model_performance_dashboard(self, monitoring_data: List[Dict]) -> go.Figure:
        """Create interactive dashboard for model performance"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Model Performance Over Time', 'Data Drift Monitoring', 
                           'Prediction Distribution', 'Feature Importance'],
            specs=[[{"secondary_y": True}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Performance over time
        timestamps = [record['timestamp'] for record in monitoring_data]
        drift_scores = [record['drift_score'] for record in monitoring_data]
        
        fig.add_trace(
            go.Scatter(x=timestamps, y=drift_scores, name='Drift Score', mode='lines+markers'),
            row=1, col=1
        )
        
        # Add more visualizations...
        
        fig.update_layout(
            title="ML Model Performance Dashboard",
            height=800
        )
        
        return fig
    
    def plot_clustering_results(self, features_df: pd.DataFrame, cluster_labels: np.ndarray, 
                               pca_components: np.ndarray) -> go.Figure:
        """Plot clustering results"""
        fig = px.scatter(
            x=pca_components[:, 0],
            y=pca_components[:, 1],
            color=cluster_labels,
            title='Power System Operating Pattern Clusters',
            labels={'x': 'First Principal Component', 'y': 'Second Principal Component'}
        )
        
        return fig

def main():
    """Main function to demonstrate ML infrastructure"""
    # Configuration
    DATABASE_PATH = "ndata.db"  # Update with your database path
    MODELS_DIR = "models"
    
    # Initialize ML infrastructure
    ml_infra = MLInfrastructure(DATABASE_PATH, MODELS_DIR)
    
    try:
        # Initialize components
        predictor = PredictiveAnalysisModel(ml_infra)
        classifier = ClassificationClusteringModel(ml_infra)
        monitor = ModelMonitoringOptimization(ml_infra)
        
        print("🤖 ML Infrastructure Setup Complete!")
        print("=" * 50)
        
        # Train models
        print("\n1. Training Predictive Models...")
        voltage_results = predictor.train_voltage_prediction_model()
        print(f"   Voltage Prediction: {voltage_results.get('best_model', 'Failed')}")
        
        load_results = predictor.train_load_forecasting_model()
        print(f"   Load Forecasting R²: {load_results.get('r2', 'Failed'):.3f}")
        
        # Classification and Clustering
        print("\n2. Classification and Clustering...")
        classification_results = classifier.classify_system_states()
        print(f"   State Classification Accuracy: {classification_results.get('accuracy', 'Failed'):.3f}")
        
        clustering_results = classifier.cluster_operating_patterns()
        print(f"   Clustering Silhouette Score: {clustering_results.get('kmeans_silhouette_score', 'Failed'):.3f}")
        
        # Model Monitoring
        print("\n3. Model Monitoring Setup...")
        monitoring_report = monitor.generate_monitoring_report()
        print(f"   System Health: {monitoring_report.get('system_health', 'Unknown')}")
        
        print("\n✅ ML Infrastructure Ready!")
        print(f"   Models saved in: {MODELS_DIR}/")
        print(f"   Log file: ml_infrastructure.log")
        
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        print(f"❌ Error: {e}")
    
    finally:
        ml_infra.disconnect_database()

if __name__ == "__main__":
    main()