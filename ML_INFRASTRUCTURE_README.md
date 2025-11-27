# ML Infrastructure for DLR Power System Analysis

A comprehensive machine learning framework for predictive analysis, classification, clustering, and model monitoring integrated with Dynamic Line Rating (DLR) power system visualization.

## 🎯 Overview

This ML infrastructure provides:

- **Predictive Analysis**: Voltage violation prediction, load forecasting
- **Classification & Clustering**: System state classification, operating pattern analysis
- **Model Monitoring**: Performance tracking, drift detection, automated optimization
- **Deployment Framework**: Model versioning, API serving, automated retraining

## 📁 Project Structure

```
dlr-database-project/
├── ml_infrastructure.py      # Core ML framework
├── ml_deployment.py         # Deployment and configuration
├── ml_demo.py              # Setup and demonstration
├── requirements_ml.txt     # Python dependencies
├── ml_config.yaml         # Configuration file (auto-generated)
├── models/                # Trained models directory
│   ├── deployments/       # Deployed model versions
│   └── monitoring_data.json
├── sample_data/           # Sample dataset (demo only)
└── logs/                  # Logging output
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements_ml.txt

# Or install manually
pip install pandas numpy scikit-learn matplotlib seaborn plotly joblib PyYAML
```

### 2. Run Demo (First Time)

```python
python ml_demo.py
```

This will:
- Create sample power system data
- Setup sample database
- Train all ML models
- Demonstrate all features

### 3. Use with Your Data

```python
from ml_infrastructure import MLInfrastructure

# Connect to your database
ml = MLInfrastructure("your_database.db")

# Start training models...
```

## 📊 Core Components

### 1. MLInfrastructure
Main orchestration class that manages:
- Database connections
- Model storage and retrieval
- Performance tracking
- Logging and monitoring

```python
ml = MLInfrastructure("ndata.db")
```

### 2. PowerSystemDataProcessor
Extracts and engineers features from power system data:
- Bus-level features (voltage, generation, load)
- Branch-level features (power flow, loading)
- SLR/DLR adjustment features
- System-wide statistics

```python
processor = PowerSystemDataProcessor(ml)
features_df = processor.extract_features()
```

### 3. PredictiveAnalysisModel
Implements forecasting models:
- **Voltage Prediction**: Predicts voltage violations
- **Load Forecasting**: Forecasts system load

```python
predictor = PredictiveAnalysisModel(ml)
voltage_results = predictor.train_voltage_prediction_model()
load_results = predictor.train_load_forecasting_model()
```

### 4. ClassificationClusteringModel
Provides pattern recognition:
- **State Classification**: Normal/Alert/Emergency states
- **Pattern Clustering**: Operating pattern discovery

```python
classifier = ClassificationClusteringModel(ml)
classification_results = classifier.classify_system_states()
clustering_results = classifier.cluster_operating_patterns()
```

### 5. ModelMonitoringOptimization
Handles model lifecycle:
- Performance monitoring
- Data drift detection
- Hyperparameter optimization
- Automated retraining recommendations

```python
monitor = ModelMonitoringOptimization(ml)
monitoring_report = monitor.generate_monitoring_report()
```

## 🔧 Configuration

Configuration is managed through `ml_config.yaml`:

```yaml
database:
  path: 'ndata.db'
  connection_timeout: 30

training:
  test_size: 0.2
  random_state: 42
  cross_validation_folds: 5

monitoring:
  drift_threshold: 0.3
  performance_threshold: 0.7
  monitoring_interval_hours: 24

hyperparameter_optimization:
  voltage_prediction:
    random_forest:
      n_estimators: [50, 100, 200]
      max_depth: [5, 10, 15, None]
```

## 🚀 Model Deployment

### Deploy Models

```python
from ml_deployment import ModelDeployment, MLConfig

config = MLConfig()
deployment = ModelDeployment(ml, config)

# Deploy with versioning
result = deployment.deploy_model('voltage_prediction')
print(f"Deployed version: {result['version']}")
```

### Serve Predictions

```python
from ml_deployment import ModelAPI

api = ModelAPI(deployment)

# Make prediction
input_data = {
    'voltage_mean': 1.0,
    'total_load': 1000.0,
    'total_generation': 1100.0,
    'bus_count': 118
}

prediction = api.predict('voltage_prediction', input_data)
print(f"Prediction: {prediction['predictions'][0]}")
```

### List Deployments

```python
deployments = deployment.list_deployments()
for model_name, versions in deployments['deployments'].items():
    print(f"{model_name}: {len(versions)} versions")
```

## 📈 Model Monitoring

### Performance Tracking

```python
# Monitor model performance
new_data = processor.extract_features()
true_values = np.array([...])  # Actual observed values

monitor_result = monitor.monitor_model_performance(
    'voltage_prediction', 
    new_data, 
    true_values
)
```

### Generate Reports

```python
report = monitor.generate_monitoring_report()
print(f"System Health: {report['system_health']}")
print("Recommendations:")
for rec in report['recommendations']:
    print(f"  - {rec}")
```

### Hyperparameter Optimization

```python
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15]
}

optimization_results = monitor.optimize_hyperparameters(
    'voltage_prediction', 
    param_grid
)
```

## 🤖 AutoML Pipeline

Run complete automated pipeline:

```python
from ml_deployment import AutoMLPipeline

automl = AutoMLPipeline(ml, config)

# Run full pipeline
results = automl.run_full_pipeline(retrain_models=True)

# Schedule automatic retraining
automl.schedule_retraining(interval_hours=24)
```

## 📊 Feature Engineering

### Bus-Level Features
- `voltage_mean`, `voltage_std`: Voltage statistics
- `voltage_violations`: Count of voltage violations
- `total_generation`, `total_load`: Power totals
- `power_balance`: Generation-load balance

### Branch-Level Features
- `total_power_flow`: Sum of power flows
- `overloaded_branches`: Count of overloaded lines
- `avg_utilization`: Average line utilization

### SLR/DLR Features
- `slr_gen_adjustments`: SLR generation adjustments
- `dlr_load_adjustments`: DLR load adjustments
- Adjustment magnitudes and frequencies

## 🎯 Model Types

### Regression Models
- **Random Forest Regressor**: For voltage and load prediction
- **Linear Regression**: Baseline comparison
- **Support Vector Regression**: Non-linear patterns

### Classification Models
- **Random Forest Classifier**: System state classification
- **Logistic Regression**: Binary classification tasks

### Clustering Models
- **K-Means**: Operating pattern clustering
- **DBSCAN**: Density-based clustering
- **PCA**: Dimensionality reduction for visualization

## 📝 Logging and Monitoring

All activities are logged to `ml_infrastructure.log`:

```
2025-09-22 10:30:15 - INFO - ML Infrastructure initialized
2025-09-22 10:30:20 - INFO - Extracted 50 feature sets with 25 features
2025-09-22 10:30:45 - INFO - Voltage prediction model trained. Best model: random_forest (R²: 0.847)
```

## 🔄 Integration with DLR Visualization

The ML infrastructure integrates with the existing DLR visualization:

```python
# In your visualization code
from ml_infrastructure import MLInfrastructure
from ml_deployment import ModelAPI, ModelDeployment

class PowerSystemVisualizer:
    def __init__(self, database_path):
        self.ml = MLInfrastructure(database_path)
        self.api = ModelAPI(ModelDeployment(self.ml, MLConfig()))
    
    def predict_voltage_violations(self, current_state):
        return self.api.predict('voltage_prediction', current_state)
    
    def classify_system_state(self, current_state):
        return self.api.predict('state_classification', current_state)
```

## 🚨 Alerts and Recommendations

The system provides actionable recommendations:

- **High Drift Detected**: Retrain models with recent data
- **Low Accuracy**: Review feature engineering
- **Performance Degradation**: Schedule optimization
- **Data Quality Issues**: Check input data

## 📊 Performance Metrics

### Regression Metrics
- **MSE**: Mean Squared Error
- **MAE**: Mean Absolute Error
- **R²**: Coefficient of determination

### Classification Metrics
- **Accuracy**: Overall classification accuracy
- **Precision/Recall**: Class-specific performance
- **F1-Score**: Balanced performance measure

### Clustering Metrics
- **Silhouette Score**: Cluster quality
- **Inertia**: Within-cluster sum of squares

## 🔒 Best Practices

### Data Quality
- Handle missing values appropriately
- Validate input data ranges
- Monitor data drift continuously

### Model Management
- Version all model deployments
- Maintain model lineage
- Regular performance validation

### Monitoring
- Set appropriate thresholds
- Automate alert systems
- Regular model retraining

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements_ml.txt
   ```

2. **Database Connection Issues**
   ```python
   # Check database path
   db_path = Path("ndata.db")
   print(f"Database exists: {db_path.exists()}")
   ```

3. **Memory Issues with Large Datasets**
   ```python
   # Limit training samples
   config.set('training.max_training_samples', 5000)
   ```

4. **Model Performance Issues**
   ```python
   # Run hyperparameter optimization
   monitor.optimize_hyperparameters(model_name, param_grid)
   ```

## 📈 Extending the Framework

### Adding New Models

```python
class CustomModel:
    def __init__(self, ml_infrastructure):
        self.ml = ml_infrastructure
    
    def train_custom_model(self):
        # Implement your model
        pass
```

### Custom Feature Engineering

```python
def extract_custom_features(self, case_id):
    # Add your domain-specific features
    return custom_features
```

### Custom Monitoring Metrics

```python
def custom_drift_detection(self, new_data, historical_data):
    # Implement custom drift detection
    return drift_score
```

## 🎯 Future Enhancements

- Deep learning models (TensorFlow/PyTorch)
- Real-time streaming predictions
- Advanced ensemble methods
- Cloud deployment capabilities
- Integration with MLOps platforms

## 📞 Support

For issues and questions:
1. Check the logs in `ml_infrastructure.log`
2. Review configuration in `ml_config.yaml`
3. Run the demo script to verify setup
4. Examine sample data for format requirements

---

*This ML infrastructure provides a solid foundation for power system analysis with room for customization and extension based on specific requirements.*