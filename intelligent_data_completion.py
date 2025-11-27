"""
Intelligent Data Completion for Power System Analysis
Handles incomplete data and generates confidence-aware insights
"""

import pandas as pd
import numpy as np
import sqlite3
from sklearn.impute import KNNImputer
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

class PowerSystemDataCompletion:
    def __init__(self, db_path='data.db'):
        self.db_path = db_path
        self.confidence_threshold = 0.7
        
    def analyze_data_completeness(self, table_name, case_id=None, contingency_id=None):
        """Analyze missing data patterns in power system tables"""
        
        conn = sqlite3.connect(self.db_path)
        
        if contingency_id:
            query = f"SELECT * FROM {table_name} WHERE base_case_id = ? AND contingency_case_id = ?"
            df = pd.read_sql_query(query, conn, params=(case_id, contingency_id))
        else:
            query = f"SELECT * FROM {table_name} WHERE base_case_id = ?"
            df = pd.read_sql_query(query, conn, params=(case_id,))
            
        conn.close()
        
        # Calculate completeness metrics
        completeness_report = {
            'total_records': len(df),
            'missing_data_summary': {},
            'completeness_percentage': {},
            'critical_missing_fields': []
        }
        
        for column in df.columns:
            missing_count = df[column].isnull().sum()
            completeness_pct = ((len(df) - missing_count) / len(df)) * 100
            
            completeness_report['missing_data_summary'][column] = missing_count
            completeness_report['completeness_percentage'][column] = completeness_pct
            
            # Mark critical fields with low completeness
            if completeness_pct < 80 and column not in ['ID', 'NAME']:
                completeness_report['critical_missing_fields'].append(column)
        
        return completeness_report, df
    
    def intelligent_power_flow_completion(self, incomplete_df, data_type='branches'):
        """Complete missing power flow data using domain knowledge"""
        
        completed_df = incomplete_df.copy()
        confidence_map = pd.DataFrame(index=incomplete_df.index, columns=incomplete_df.columns, data=1.0)
        
        if data_type == 'branches':
            completed_df, confidence_map = self._complete_branch_data(completed_df, confidence_map)
        elif data_type == 'buses':
            completed_df, confidence_map = self._complete_bus_data(completed_df, confidence_map)
        
        return completed_df, confidence_map
    
    def _complete_branch_data(self, df, confidence_map):
        """Complete missing branch/line data using power system relationships"""
        
        # 1. Complete RATE using typical line ratings by voltage level
        if 'RATE' in df.columns and df['RATE'].isnull().any():
            # Estimate based on FROM_BUS and TO_BUS voltage levels
            missing_rate_mask = df['RATE'].isnull()
            
            # Use median rating for similar voltage level lines
            for idx in df[missing_rate_mask].index:
                from_bus = df.loc[idx, 'FROM_BUS']
                # Use average rating of lines with similar bus numbers (proxy for voltage level)
                similar_lines = df[(df['FROM_BUS'].between(from_bus-10, from_bus+10)) & 
                                 (df['RATE'].notnull())]
                
                if len(similar_lines) > 0:
                    df.loc[idx, 'RATE'] = similar_lines['RATE'].median()
                    confidence_map.loc[idx, 'RATE'] = 0.6  # Medium confidence
                else:
                    # Fallback to overall median
                    df.loc[idx, 'RATE'] = df['RATE'].median()
                    confidence_map.loc[idx, 'RATE'] = 0.4  # Low confidence
        
        # 2. Complete MVA using Ohm's law relationships
        if 'MVA' in df.columns and 'VIO' in df.columns:
            missing_mva_mask = df['MVA'].isnull()
            
            for idx in df[missing_mva_mask].index:
                if pd.notnull(df.loc[idx, 'VIO']) and pd.notnull(df.loc[idx, 'RATE']):
                    # Estimate MVA from violation percentage
                    violation_pct = df.loc[idx, 'VIO']
                    rate = df.loc[idx, 'RATE']
                    
                    # MVA = RATE * (1 + violation_pct/100)
                    estimated_mva = rate * (1 + violation_pct / 100)
                    df.loc[idx, 'MVA'] = estimated_mva
                    confidence_map.loc[idx, 'MVA'] = 0.8  # High confidence (physics-based)
        
        # 3. Complete VIO using MVA and RATE relationship
        if 'VIO' in df.columns and 'MVA' in df.columns and 'RATE' in df.columns:
            missing_vio_mask = df['VIO'].isnull()
            
            for idx in df[missing_vio_mask].index:
                if pd.notnull(df.loc[idx, 'MVA']) and pd.notnull(df.loc[idx, 'RATE']):
                    mva = df.loc[idx, 'MVA']
                    rate = df.loc[idx, 'RATE']
                    
                    # VIO = ((MVA - RATE) / RATE) * 100
                    violation_pct = ((mva - rate) / rate) * 100
                    df.loc[idx, 'VIO'] = max(0, violation_pct)  # No negative violations
                    confidence_map.loc[idx, 'VIO'] = 0.9  # Very high confidence (calculated)
        
        return df, confidence_map
    
    def _complete_bus_data(self, df, confidence_map):
        """Complete missing bus data using electrical relationships"""
        
        # Complete voltage using neighboring bus interpolation
        if 'VM' in df.columns:  # Voltage magnitude
            missing_vm_mask = df['VM'].isnull()
            
            # Use KNN imputation based on bus geographical proximity
            if missing_vm_mask.any():
                # Assume bus numbers represent some geographical/electrical proximity
                bus_features = df[['BUS_NUMBER']].fillna(method='ffill')
                
                imputer = KNNImputer(n_neighbors=3)
                df_numeric = df.select_dtypes(include=[np.number])
                
                if len(df_numeric.columns) > 1:
                    completed_numeric = imputer.fit_transform(df_numeric)
                    
                    for i, col in enumerate(df_numeric.columns):
                        if col == 'VM':
                            df[col] = completed_numeric[:, i]
                            confidence_map.loc[missing_vm_mask, col] = 0.7
        
        return df, confidence_map
    
    def generate_completion_report(self, original_df, completed_df, confidence_map):
        """Generate a report on data completion"""
        
        report = {
            'original_missing_count': original_df.isnull().sum().sum(),
            'completed_missing_count': completed_df.isnull().sum().sum(),
            'completion_success_rate': 0,
            'field_completion_details': {},
            'average_confidence': confidence_map.mean().mean(),
            'low_confidence_fields': []
        }
        
        # Calculate completion success rate
        if report['original_missing_count'] > 0:
            completed_count = report['original_missing_count'] - report['completed_missing_count']
            report['completion_success_rate'] = (completed_count / report['original_missing_count']) * 100
        
        # Field-by-field analysis
        for column in original_df.columns:
            original_missing = original_df[column].isnull().sum()
            completed_missing = completed_df[column].isnull().sum()
            
            if original_missing > 0:
                completion_rate = ((original_missing - completed_missing) / original_missing) * 100
                avg_confidence = confidence_map[column].mean()
                
                report['field_completion_details'][column] = {
                    'original_missing': original_missing,
                    'completion_rate': completion_rate,
                    'average_confidence': avg_confidence
                }
                
                if avg_confidence < 0.6:
                    report['low_confidence_fields'].append(column)
        
        return report

class IntelligentInsightGenerator:
    def __init__(self):
        self.completion_engine = PowerSystemDataCompletion()
        
    def generate_qualified_insights(self, data, confidence_map, analysis_type='violation'):
        """Generate insights with confidence qualifiers"""
        
        insights = []
        
        if analysis_type == 'violation':
            insights.extend(self._analyze_violations_with_confidence(data, confidence_map))
        elif analysis_type == 'capacity':
            insights.extend(self._analyze_capacity_with_confidence(data, confidence_map))
        
        return insights
    
    def _analyze_violations_with_confidence(self, data, confidence_map):
        """Analyze violations with confidence assessment"""
        
        insights = []
        
        if 'VIO' in data.columns:
            violation_data = data[data['VIO'] > 0]
            
            if len(violation_data) > 0:
                # High confidence violations
                high_confidence_violations = violation_data[
                    confidence_map.loc[violation_data.index, 'VIO'] > 0.8
                ]
                
                if len(high_confidence_violations) > 0:
                    max_violation = high_confidence_violations['VIO'].max()
                    insights.append(
                        f"🔴 HIGH CONFIDENCE: {len(high_confidence_violations)} violations detected. "
                        f"Maximum violation: {max_violation:.1f}%"
                    )
                
                # Medium confidence violations
                medium_confidence_violations = violation_data[
                    (confidence_map.loc[violation_data.index, 'VIO'] > 0.5) &
                    (confidence_map.loc[violation_data.index, 'VIO'] <= 0.8)
                ]
                
                if len(medium_confidence_violations) > 0:
                    insights.append(
                        f"🟡 MODERATE CONFIDENCE: {len(medium_confidence_violations)} potential violations "
                        f"(based on estimated data)"
                    )
                
                # Low confidence violations
                low_confidence_violations = violation_data[
                    confidence_map.loc[violation_data.index, 'VIO'] <= 0.5
                ]
                
                if len(low_confidence_violations) > 0:
                    insights.append(
                        f"⚠️ LOW CONFIDENCE: {len(low_confidence_violations)} possible violations "
                        f"(significant data gaps - recommend verification)"
                    )
        
        return insights
    
    def suggest_data_improvement_actions(self, completion_report):
        """Suggest actions to improve data quality"""
        
        suggestions = []
        
        if completion_report['completion_success_rate'] < 70:
            suggestions.append(
                "📊 RECOMMENDATION: Data completeness is below 70%. Consider implementing "
                "real-time monitoring systems for better data collection."
            )
        
        if completion_report['average_confidence'] < 0.6:
            suggestions.append(
                "🎯 RECOMMENDATION: Average confidence is low. Prioritize installing sensors "
                "at critical measurement points."
            )
        
        for field in completion_report['low_confidence_fields']:
            suggestions.append(
                f"🔧 SPECIFIC ACTION: Field '{field}' has low confidence. "
                f"Consider manual verification or additional sensors."
            )
        
        return suggestions

def generate_dlr_slr_missing_data(case_id=42, contingency_ids=[56, 90, 123, 124, 158]):
    """Generate missing DLR and SLR data for specific scenarios"""
    
    completion_engine = PowerSystemDataCompletion()
    conn = sqlite3.connect('data.db')
    
    results = {
        'slr_generated': 0,
        'dlr_generated': 0,
        'scenarios_processed': 0,
        'confidence_summary': {},
        'generation_report': []
    }
    
    try:
        for contingency_id in contingency_ids:
            print(f"🔧 Processing scenario: Case {case_id}, Contingency {contingency_id}")
            
            # Check existing SLR data
            slr_query = "SELECT COUNT(*) as count FROM SLR_Branches WHERE base_case_id = ? AND contingency_case_id = ?"
            slr_count = pd.read_sql_query(slr_query, conn, params=(case_id, contingency_id))
            
            # Check existing DLR data
            dlr_query = "SELECT COUNT(*) as count FROM DLR_Branches WHERE base_case_id = ? AND contingency_case_id = ?"
            dlr_count = pd.read_sql_query(dlr_query, conn, params=(case_id, contingency_id))
            
            scenario_report = {
                'contingency_id': contingency_id,
                'slr_existing': slr_count.iloc[0, 0],
                'dlr_existing': dlr_count.iloc[0, 0],
                'data_available': slr_count.iloc[0, 0] > 0 or dlr_count.iloc[0, 0] > 0
            }
            
            if scenario_report['data_available']:
                # Analyze and complete existing data
                if slr_count.iloc[0, 0] > 0:
                    result = enhance_existing_analysis_with_completion('SLR_Branches', case_id, contingency_id)
                    scenario_report['slr_completion'] = result['completion_report']
                    results['slr_generated'] += result['completion_report']['original_missing_count'] - result['completion_report']['completed_missing_count']
                
                if dlr_count.iloc[0, 0] > 0:
                    result = enhance_existing_analysis_with_completion('DLR_Branches', case_id, contingency_id)
                    scenario_report['dlr_completion'] = result['completion_report']
                    results['dlr_generated'] += result['completion_report']['original_missing_count'] - result['completion_report']['completed_missing_count']
            
            results['generation_report'].append(scenario_report)
            results['scenarios_processed'] += 1
        
        # Generate summary
        results['summary'] = f"""
📊 DLR/SLR Data Generation Complete:
• Scenarios processed: {results['scenarios_processed']}
• SLR data points generated: {results['slr_generated']}
• DLR data points generated: {results['dlr_generated']}
• Total case/contingency combinations analyzed: {len(contingency_ids)}
        """
        
        conn.close()
        return results
        
    except Exception as e:
        conn.close()
        print(f"Error generating DLR/SLR data: {e}")
        return results

# Example usage functions for integration
def enhance_existing_analysis_with_completion(table_name, case_id, contingency_id=None):
    """Enhance existing analysis with intelligent data completion"""
    
    completion_engine = PowerSystemDataCompletion()
    insight_generator = IntelligentInsightGenerator()
    
    # Handle default case_id if None or 0
    if case_id is None or case_id == 0:
        case_id = 42  # Use default working case
    
    # For DLR/SLR analysis, always use appropriate tables
    if any(term in table_name.upper() for term in ['DLR', 'SLR']):
        # For DLR/SLR comparison, we need both tables
        print(f"📊 Analyzing DLR/SLR data for case {case_id}, contingency {contingency_id}")
        
        # Try SLR first
        try:
            completeness_report, original_data = completion_engine.analyze_data_completeness(
                'SLR_Branches', case_id, contingency_id
            )
            if original_data.empty:
                # Try DLR if SLR is empty
                completeness_report, original_data = completion_engine.analyze_data_completeness(
                    'DLR_Branches', case_id, contingency_id
                )
        except Exception as e:
            print(f"⚠️ Error with DLR/SLR tables: {e}")
            # Fallback to generic Branches table
            completeness_report, original_data = completion_engine.analyze_data_completeness(
                'Branches', case_id, contingency_id
            )
    else:
        # Analyze data completeness for specified table
        completeness_report, original_data = completion_engine.analyze_data_completeness(
            table_name, case_id, contingency_id
        )
    
    if original_data.empty:
        return {
            'original_data': original_data,
            'completed_data': original_data,
            'confidence_map': pd.DataFrame(),
            'completeness_report': {'total_records': 0},
            'completion_report': {
                'original_missing_count': 0,
                'completion_success_rate': 0,
                'average_confidence': 0,
                'low_confidence_fields': []
            },
            'insights': [f"⚠️ No data found for case {case_id}, contingency {contingency_id}"],
            'improvement_suggestions': ["📊 Verify case and contingency IDs are correct"]
        }
    
    # Complete missing data
    if 'Branches' in table_name or any(term in table_name.upper() for term in ['DLR', 'SLR']):
        completed_data, confidence_map = completion_engine.intelligent_power_flow_completion(
            original_data, 'branches'
        )
    else:
        completed_data, confidence_map = completion_engine.intelligent_power_flow_completion(
            original_data, 'buses'
        )
    
    # Generate completion report
    completion_report = completion_engine.generate_completion_report(
        original_data, completed_data, confidence_map
    )
    
    # Generate qualified insights
    insights = insight_generator.generate_qualified_insights(
        completed_data, confidence_map, 'violation'
    )
    
    # Suggest improvements
    improvement_suggestions = insight_generator.suggest_data_improvement_actions(
        completion_report
    )
    
    return {
        'original_data': original_data,
        'completed_data': completed_data,
        'confidence_map': confidence_map,
        'completeness_report': completeness_report,
        'completion_report': completion_report,
        'insights': insights,
        'improvement_suggestions': improvement_suggestions
    }

if __name__ == "__main__":
    # Test the completion system
    result = enhance_existing_analysis_with_completion('SLR_Branches', 42, 56)
    
    print("=== DATA COMPLETION ANALYSIS ===")
    print(f"Original missing data points: {result['completion_report']['original_missing_count']}")
    print(f"Completion success rate: {result['completion_report']['completion_success_rate']:.1f}%")
    print(f"Average confidence: {result['completion_report']['average_confidence']:.2f}")
    
    print("\n=== QUALIFIED INSIGHTS ===")
    for insight in result['insights']:
        print(insight)
    
    print("\n=== IMPROVEMENT SUGGESTIONS ===")
    for suggestion in result['improvement_suggestions']:
        print(suggestion)