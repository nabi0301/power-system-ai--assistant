"""
ML Model Configuration and Deployment
Advanced configuration management and deployment utilities for the ML infrastructure
"""

import json
import yaml
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class MLConfig:
    """Configuration management for ML infrastructure"""
    
    def __init__(self, config_path: str = "ml_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default configuration"""
        default_config = {
            'database': {
                'path': 'ndata.db',
                'connection_timeout': 30
            },
            'models': {
                'directory': 'models',
                'auto_save': True,
                'versioning': True
            },
            'training': {
                'test_size': 0.2,
                'random_state': 42,
                'cross_validation_folds': 5,
                'max_training_samples': 10000
            },
            'monitoring': {
                'drift_threshold': 0.3,
                'performance_threshold': 0.7,
                'monitoring_interval_hours': 24,
                'alert_email': None
            },
            'feature_engineering': {
                'fill_missing_with_mean': True,
                'scale_features': True,
                'feature_selection': True,
                'max_features': 50
            },
            'hyperparameter_optimization': {
                'voltage_prediction': {
                    'random_forest': {
                        'n_estimators': [50, 100, 200],
                        'max_depth': [5, 10, 15, None],
                        'min_samples_split': [2, 5, 10],
                        'min_samples_leaf': [1, 2, 4]
                    }
                },
                'load_forecasting': {
                    'random_forest': {
                        'n_estimators': [50, 100, 200],
                        'max_depth': [5, 10, 15],
                        'min_samples_split': [2, 5, 10]
                    }
                },
                'state_classification': {
                    'random_forest': {
                        'n_estimators': [50, 100, 200],
                        'max_depth': [5, 10, 15],
                        'min_samples_split': [2, 5, 10],
                        'class_weight': ['balanced', None]
                    }
                }
            },
            'clustering': {
                'kmeans': {
                    'n_clusters_range': [3, 4, 5, 6, 7, 8],
                    'max_iter': 300,
                    'n_init': 10
                },
                'dbscan': {
                    'eps_range': [0.3, 0.5, 0.7, 1.0],
                    'min_samples_range': [3, 5, 7, 10]
                }
            },
            'visualization': {
                'save_plots': True,
                'plot_format': 'png',
                'plot_dpi': 300,
                'interactive_plots': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'ml_infrastructure.log',
                'max_file_size_mb': 50,
                'backup_count': 5
            }
        }
        
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict = None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self.save_config()

class ModelDeployment:
    """Model deployment and serving utilities"""
    
    def __init__(self, ml_infrastructure, config: MLConfig):
        self.ml = ml_infrastructure
        self.config = config
        self.deployment_info = {}
    
    def deploy_model(self, model_name: str, version: str = None) -> Dict:
        """Deploy a trained model for production use"""
        try:
            if model_name not in self.ml.models:
                return {'error': f'Model {model_name} not found'}
            
            if version is None:
                version = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create deployment directory
            deploy_dir = Path(self.config.get('models.directory')) / 'deployments' / model_name / version
            deploy_dir.mkdir(parents=True, exist_ok=True)
            
            # Save model artifacts
            model_path = deploy_dir / 'model.joblib'
            scaler_path = deploy_dir / 'scaler.joblib'
            metadata_path = deploy_dir / 'metadata.json'
            
            # Save model
            import joblib
            joblib.dump(self.ml.models[model_name], model_path)
            
            # Save scaler if exists
            if model_name in self.ml.scalers:
                joblib.dump(self.ml.scalers[model_name], scaler_path)
            
            # Save encoder if exists
            if model_name in self.ml.encoders:
                encoder_path = deploy_dir / 'encoder.joblib'
                joblib.dump(self.ml.encoders[model_name], encoder_path)
            
            # Create metadata
            metadata = {
                'model_name': model_name,
                'version': version,
                'deployment_timestamp': datetime.now().isoformat(),
                'model_type': type(self.ml.models[model_name]).__name__,
                'has_scaler': model_name in self.ml.scalers,
                'has_encoder': model_name in self.ml.encoders,
                'deployment_path': str(deploy_dir)
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update deployment registry
            self.deployment_info[model_name] = metadata
            
            logging.info(f"Model {model_name} v{version} deployed successfully")
            
            return {
                'status': 'success',
                'deployment_path': str(deploy_dir),
                'version': version,
                'metadata': metadata
            }
            
        except Exception as e:
            logging.error(f"Error deploying model {model_name}: {e}")
            return {'error': str(e)}
    
    def load_deployed_model(self, model_name: str, version: str = 'latest') -> Dict:
        """Load a deployed model"""
        try:
            deploy_base = Path(self.config.get('models.directory')) / 'deployments' / model_name
            
            if version == 'latest':
                # Find latest version
                version_dirs = [d for d in deploy_base.iterdir() if d.is_dir()]
                if not version_dirs:
                    return {'error': f'No deployments found for {model_name}'}
                
                latest_dir = max(version_dirs, key=lambda x: x.name)
                deploy_dir = latest_dir
            else:
                deploy_dir = deploy_base / version
            
            if not deploy_dir.exists():
                return {'error': f'Deployment {model_name} v{version} not found'}
            
            # Load artifacts
            import joblib
            
            model_path = deploy_dir / 'model.joblib'
            model = joblib.load(model_path)
            
            scaler = None
            scaler_path = deploy_dir / 'scaler.joblib'
            if scaler_path.exists():
                scaler = joblib.load(scaler_path)
            
            encoder = None
            encoder_path = deploy_dir / 'encoder.joblib'
            if encoder_path.exists():
                encoder = joblib.load(encoder_path)
            
            # Load metadata
            metadata_path = deploy_dir / 'metadata.json'
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            logging.info(f"Loaded deployed model {model_name} v{metadata['version']}")
            
            return {
                'status': 'success',
                'model': model,
                'scaler': scaler,
                'encoder': encoder,
                'metadata': metadata
            }
            
        except Exception as e:
            logging.error(f"Error loading deployed model {model_name}: {e}")
            return {'error': str(e)}
    
    def list_deployments(self) -> Dict:
        """List all available model deployments"""
        try:
            deploy_base = Path(self.config.get('models.directory')) / 'deployments'
            
            if not deploy_base.exists():
                return {'deployments': {}}
            
            deployments = {}
            
            for model_dir in deploy_base.iterdir():
                if model_dir.is_dir():
                    model_name = model_dir.name
                    versions = []
                    
                    for version_dir in model_dir.iterdir():
                        if version_dir.is_dir():
                            metadata_path = version_dir / 'metadata.json'
                            if metadata_path.exists():
                                with open(metadata_path, 'r') as f:
                                    metadata = json.load(f)
                                versions.append(metadata)
                    
                    deployments[model_name] = sorted(versions, 
                                                   key=lambda x: x['deployment_timestamp'], 
                                                   reverse=True)
            
            return {'deployments': deployments}
            
        except Exception as e:
            logging.error(f"Error listing deployments: {e}")
            return {'error': str(e)}

class ModelAPI:
    """REST API interface for model serving"""
    
    def __init__(self, deployment: ModelDeployment):
        self.deployment = deployment
        self.loaded_models = {}
    
    def predict(self, model_name: str, input_data: Dict, version: str = 'latest') -> Dict:
        """Make prediction using deployed model"""
        try:
            # Load model if not already loaded
            model_key = f"{model_name}_{version}"
            
            if model_key not in self.loaded_models:
                result = self.deployment.load_deployed_model(model_name, version)
                if 'error' in result:
                    return result
                
                self.loaded_models[model_key] = result
            
            model_info = self.loaded_models[model_key]
            model = model_info['model']
            scaler = model_info['scaler']
            encoder = model_info['encoder']
            
            # Prepare input data
            import pandas as pd
            import numpy as np
            
            if isinstance(input_data, dict):
                input_df = pd.DataFrame([input_data])
            else:
                input_df = pd.DataFrame(input_data)
            
            # Handle missing values
            input_df = input_df.fillna(input_df.mean())
            
            # Scale if scaler available
            if scaler is not None:
                input_scaled = scaler.transform(input_df)
            else:
                input_scaled = input_df
            
            # Make prediction
            prediction = model.predict(input_scaled)
            
            # Handle encoder for classification
            if encoder is not None and hasattr(model, 'predict_proba'):
                prediction_labels = encoder.inverse_transform(prediction)
                probabilities = model.predict_proba(input_scaled)
                
                return {
                    'status': 'success',
                    'predictions': prediction_labels.tolist(),
                    'probabilities': probabilities.tolist(),
                    'model_version': model_info['metadata']['version']
                }
            else:
                return {
                    'status': 'success',
                    'predictions': prediction.tolist(),
                    'model_version': model_info['metadata']['version']
                }
            
        except Exception as e:
            logging.error(f"Error making prediction with {model_name}: {e}")
            return {'error': str(e)}
    
    def batch_predict(self, model_name: str, input_data: List[Dict], version: str = 'latest') -> Dict:
        """Make batch predictions"""
        return self.predict(model_name, input_data, version)
    
    def get_model_info(self, model_name: str, version: str = 'latest') -> Dict:
        """Get information about a deployed model"""
        try:
            result = self.deployment.load_deployed_model(model_name, version)
            if 'error' in result:
                return result
            
            metadata = result['metadata']
            
            return {
                'status': 'success',
                'model_info': {
                    'name': metadata['model_name'],
                    'version': metadata['version'],
                    'type': metadata['model_type'],
                    'deployment_date': metadata['deployment_timestamp'],
                    'has_scaler': metadata.get('has_scaler', False),
                    'has_encoder': metadata.get('has_encoder', False)
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting model info for {model_name}: {e}")
            return {'error': str(e)}

class AutoMLPipeline:
    """Automated machine learning pipeline"""
    
    def __init__(self, ml_infrastructure, config: MLConfig):
        self.ml = ml_infrastructure
        self.config = config
    
    def run_full_pipeline(self, retrain_models: bool = False) -> Dict:
        """Run complete ML pipeline"""
        try:
            results = {}
            
            print("🚀 Starting AutoML Pipeline...")
            
            # 1. Data Extraction and Preprocessing
            print("📊 Step 1: Data Extraction and Feature Engineering...")
            from ml_infrastructure import PowerSystemDataProcessor
            processor = PowerSystemDataProcessor(self.ml)
            features_df = processor.extract_features()
            
            if features_df.empty:
                return {'error': 'No data available for pipeline'}
            
            results['data_summary'] = {
                'total_samples': len(features_df),
                'total_features': len(features_df.columns),
                'missing_values': features_df.isnull().sum().sum()
            }
            
            # 2. Model Training
            if retrain_models or not self.ml.models:
                print("🤖 Step 2: Training Predictive Models...")
                
                from ml_infrastructure import PredictiveAnalysisModel
                predictor = PredictiveAnalysisModel(self.ml)
                
                # Train voltage prediction
                voltage_results = predictor.train_voltage_prediction_model()
                results['voltage_prediction'] = voltage_results
                
                # Train load forecasting
                load_results = predictor.train_load_forecasting_model()
                results['load_forecasting'] = load_results
                
                print("🎯 Step 3: Classification and Clustering...")
                
                from ml_infrastructure import ClassificationClusteringModel
                classifier = ClassificationClusteringModel(self.ml)
                
                # State classification
                classification_results = classifier.classify_system_states()
                results['state_classification'] = classification_results
                
                # Clustering analysis
                clustering_results = classifier.cluster_operating_patterns()
                results['clustering'] = clustering_results
            
            # 3. Model Optimization
            print("⚡ Step 4: Hyperparameter Optimization...")
            
            from ml_infrastructure import ModelMonitoringOptimization
            monitor = ModelMonitoringOptimization(self.ml)
            
            # Optimize each model
            for model_name in ['voltage_prediction', 'state_classification']:
                if model_name in self.config.get('hyperparameter_optimization', {}):
                    param_grid = self.config.get(f'hyperparameter_optimization.{model_name}')
                    if param_grid:
                        optimization_results = monitor.optimize_hyperparameters(model_name, param_grid)
                        results[f'{model_name}_optimization'] = optimization_results
            
            # 4. Model Deployment
            print("🚀 Step 5: Model Deployment...")
            
            deployment = ModelDeployment(self.ml, self.config)
            
            for model_name in self.ml.models.keys():
                deploy_result = deployment.deploy_model(model_name)
                results[f'{model_name}_deployment'] = deploy_result
            
            # 5. Monitoring Setup
            print("📈 Step 6: Setting up Monitoring...")
            
            monitoring_report = monitor.generate_monitoring_report()
            results['monitoring'] = monitoring_report
            
            # 6. Generate Summary Report
            pipeline_summary = {
                'pipeline_completion_time': datetime.now().isoformat(),
                'models_trained': len(self.ml.models),
                'models_deployed': len([r for r in results.values() if isinstance(r, dict) and r.get('status') == 'success']),
                'overall_status': 'success'
            }
            
            results['pipeline_summary'] = pipeline_summary
            
            print("✅ AutoML Pipeline Complete!")
            print(f"   Models Trained: {pipeline_summary['models_trained']}")
            print(f"   Models Deployed: {pipeline_summary['models_deployed']}")
            
            return results
            
        except Exception as e:
            logging.error(f"Error in AutoML pipeline: {e}")
            return {'error': str(e)}
    
    def schedule_retraining(self, interval_hours: int = 24) -> Dict:
        """Schedule automatic model retraining"""
        try:
            import schedule
            import time
            import threading
            
            def retrain_job():
                print("🔄 Scheduled retraining started...")
                results = self.run_full_pipeline(retrain_models=True)
                
                if 'error' not in results:
                    print("✅ Scheduled retraining completed successfully")
                else:
                    print(f"❌ Scheduled retraining failed: {results['error']}")
            
            # Schedule the job
            schedule.every(interval_hours).hours.do(retrain_job)
            
            # Run scheduler in background thread
            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            
            logging.info(f"Scheduled retraining every {interval_hours} hours")
            
            return {
                'status': 'success',
                'interval_hours': interval_hours,
                'next_run': schedule.next_run()
            }
            
        except Exception as e:
            logging.error(f"Error scheduling retraining: {e}")
            return {'error': str(e)}

def main():
    """Demonstrate ML configuration and deployment"""
    
    # Initialize configuration
    config = MLConfig()
    
    # Initialize ML infrastructure
    from ml_infrastructure import MLInfrastructure
    ml_infra = MLInfrastructure(config.get('database.path'))
    
    try:
        # Create deployment manager
        deployment = ModelDeployment(ml_infra, config)
        
        # Create API interface
        api = ModelAPI(deployment)
        
        # Create AutoML pipeline
        automl = AutoMLPipeline(ml_infra, config)
        
        print("🔧 ML Configuration and Deployment Setup")
        print("=" * 50)
        
        # Run AutoML pipeline
        print("\n🚀 Running AutoML Pipeline...")
        pipeline_results = automl.run_full_pipeline()
        
        if 'error' not in pipeline_results:
            print("✅ Pipeline completed successfully!")
            
            # List deployments
            deployments = deployment.list_deployments()
            print(f"\n📦 Available Deployments:")
            for model_name, versions in deployments['deployments'].items():
                latest_version = versions[0] if versions else None
                if latest_version:
                    print(f"   {model_name}: v{latest_version['version']}")
            
            # Example prediction
            if 'voltage_prediction' in ml_infra.models:
                print(f"\n🔮 Testing Prediction API...")
                
                # Create sample input
                sample_input = {
                    'voltage_mean': 1.0,
                    'total_load': 1000.0,
                    'total_generation': 1100.0,
                    'bus_count': 118
                }
                
                prediction_result = api.predict('voltage_prediction', sample_input)
                if 'error' not in prediction_result:
                    print(f"   Sample prediction: {prediction_result['predictions'][0]:.3f}")
                
        else:
            print(f"❌ Pipeline failed: {pipeline_results['error']}")
        
        print(f"\n📋 Configuration saved to: {config.config_path}")
        print(f"📊 Models directory: {config.get('models.directory')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Error in main execution: {e}")
    
    finally:
        ml_infra.disconnect_database()

if __name__ == "__main__":
    main()