"""
Power System Statistical Analysis Engine
=======================================

This module performs comprehensive statistical analyses on power system data
without requiring location or weather data. Uses existing electrical parameters
from the power system database.

Analyses Included:
- Correlation Analysis
- Monte Carlo Risk Assessment  
- Sensitivity Analysis
- Clustering Analysis
- Reliability Statistics
- Economic Analysis
- Power Quality Analysis
"""

import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

class PowerSystemStatisticalAnalyzer:
    """
    Comprehensive statistical analysis engine for power system data
    """
    
    def __init__(self, database_path):
        self.database_path = database_path
        self.scaler = StandardScaler()
        self._all_base_case_ids = None
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.database_path)
    
    def basic_system_summary(self, base_case_id=None):
        """
        Get basic system summary including bus and branch counts, load/generation totals
        If base_case_id is None, automatically selects the best available case
        """
        try:
            # If no base case specified, find the best available case
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {'error': 'No base case data found in database'}
                    
            buses, branches = self.load_base_case_data(base_case_id)
            
            if buses.empty or branches.empty:
                # Try to get data from any available source
                summary = self._get_summary_from_any_available_data()
                if summary:
                    return summary
                return {'error': f'No data found for base case {base_case_id}'}
            
            # Basic system statistics
            summary = {
                'base_case_id': base_case_id,
                'total_buses': len(buses),
                'total_branches': len(branches),
                'total_load_mw': buses['PD'].sum(),
                'total_generation_mw': buses['PG'].sum(),
                'total_reactive_load_mvar': buses['QD'].sum(),
                'total_reactive_generation_mvar': buses['QG'].sum(),
                'generating_buses': (buses['PG'] > 0).sum(),
                'load_buses': (buses['PD'] > 0).sum(),
                'voltage_levels': sorted(buses['BASE_KV'].unique().tolist()) if 'BASE_KV' in buses.columns else [],
                'load_generation_balance_mw': buses['PG'].sum() - buses['PD'].sum(),
                'reactive_balance_mvar': buses['QG'].sum() - buses['QD'].sum()
            }
            
            return summary
            
        except Exception as e:
            print(f"Error in basic system summary: {e}")
            # Try alternative data sources
            return self._get_summary_from_any_available_data()
    
    def _get_best_available_base_case(self):
        """Find the best available base case ID from the database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Try to find base cases with the most complete data
            tables_to_check = [
                ('BaseBusData', 'base_case_id'),
                ('SLR_Buses', 'case_id'), 
                ('DLR_Buses', 'case_id'),
                ('ContingencyBusData', 'base_case_id')
            ]
            
            for table, id_column in tables_to_check:
                try:
                    cursor.execute(f"SELECT {id_column}, COUNT(*) as count FROM {table} GROUP BY {id_column} ORDER BY count DESC LIMIT 1")
                    result = cursor.fetchone()
                    if result:
                        conn.close()
                        print(f"📊 Auto-selected case {result[0]} from {table} with {result[1]} records")
                        return result[0]
                except:
                    continue
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error finding best base case: {e}")
            return None
    
    def _get_summary_from_any_available_data(self):
        """Get system summary from any available data source in the database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get list of all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            summary = {
                'data_source': 'mixed_sources',
                'available_tables': tables,
                'database_overview': {}
            }
            
            # Check each table for data
            for table in tables:
                if 'Bus' in table or 'bus' in table:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            summary['database_overview'][table] = {'record_count': count}
                            
                            # Try to get voltage and power data if available
                            cursor.execute(f"PRAGMA table_info({table})")
                            columns = [col[1] for col in cursor.fetchall()]
                            
                            power_data = {}
                            if 'PD' in columns:
                                cursor.execute(f"SELECT SUM(PD) FROM {table} WHERE PD IS NOT NULL")
                                total_load = cursor.fetchone()[0]
                                power_data['total_load_mw'] = total_load if total_load else 0
                            
                            if 'PG' in columns:
                                cursor.execute(f"SELECT SUM(PG) FROM {table} WHERE PG IS NOT NULL")
                                total_gen = cursor.fetchone()[0]
                                power_data['total_generation_mw'] = total_gen if total_gen else 0
                            
                            if 'VM' in columns:
                                cursor.execute(f"SELECT MIN(VM), MAX(VM), AVG(VM) FROM {table} WHERE VM IS NOT NULL")
                                v_stats = cursor.fetchone()
                                if v_stats and all(v is not None for v in v_stats):
                                    power_data['voltage_stats'] = {
                                        'min': v_stats[0], 'max': v_stats[1], 'avg': v_stats[2]
                                    }
                            
                            if power_data:
                                summary['database_overview'][table]['power_data'] = power_data
                    except:
                        continue
                
                elif 'Branch' in table or 'branch' in table:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        summary['database_overview'][table] = {'record_count': count}
                    except:
                        continue
            
            conn.close()
            
            # Calculate aggregate statistics
            total_buses = sum(info.get('record_count', 0) for name, info in summary['database_overview'].items() if 'Bus' in name)
            total_branches = sum(info.get('record_count', 0) for name, info in summary['database_overview'].items() if 'Branch' in name)
            
            summary['aggregate_stats'] = {
                'estimated_total_buses': total_buses,
                'estimated_total_branches': total_branches,
                'data_sources_found': len([t for t in tables if 'Bus' in t or 'Branch' in t])
            }
            
            return summary
            
        except Exception as e:
            print(f"Error getting summary from available data: {e}")
            return {'error': f'Could not access database: {str(e)}'}

    # =====================================================
    # 🔹 COMPREHENSIVE BUS-LEVEL ANALYSIS METHODS
    # =====================================================
    
    def voltage_profile_analysis(self, base_case_id=None, voltage_limits=(0.95, 1.05)):
        """Comprehensive voltage profile analysis across all buses"""
        try:
            # Auto-select base case if not specified
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return self._get_voltage_analysis_from_any_source(voltage_limits[0], voltage_limits[1])
            
            buses, _ = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                return self._get_voltage_analysis_from_any_source(voltage_limits[0], voltage_limits[1])
            
            # Analyze voltage violations
            min_limit, max_limit = voltage_limits
            voltages = buses['VM']
            bus_numbers = buses['bus_number'] if 'bus_number' in buses.columns else buses.index
            
            under_voltage = []
            over_voltage = []
            normal_voltage = []
            
            voltage_values = voltages.tolist()
            
            for i, (bus_num, vm) in enumerate(zip(bus_numbers, voltages)):
                if vm < min_limit:
                    under_voltage.append((bus_num, vm))
                elif vm > max_limit:
                    over_voltage.append((bus_num, vm))
                else:
                    normal_voltage.append((bus_num, vm))
            
            # Calculate comprehensive statistics
            voltage_stats = {
                "min_voltage": float(voltages.min()),
                "max_voltage": float(voltages.max()),
                "avg_voltage": float(voltages.mean()),
                "voltage_spread": float(voltages.max() - voltages.min()),
                "std_deviation": float(voltages.std())
            }
            
            return {
                "voltage_profile": voltage_values,
                "bus_numbers": bus_numbers.tolist() if hasattr(bus_numbers, 'tolist') else list(bus_numbers),
                "voltage_statistics": voltage_stats,
                "under_voltage_violations": {
                    "count": len(under_voltage),
                    "buses": under_voltage,
                    "percentage": (len(under_voltage) / len(voltages)) * 100 if len(voltages) > 0 else 0
                },
                "over_voltage_violations": {
                    "count": len(over_voltage),
                    "buses": over_voltage,
                    "percentage": (len(over_voltage) / len(voltages)) * 100 if len(voltages) > 0 else 0
                },
                "normal_voltage_buses": {
                    "count": len(normal_voltage),
                    "percentage": (len(normal_voltage) / len(voltages)) * 100 if len(voltages) > 0 else 0
                },
                "total_buses": len(voltages),
                "voltage_limits": voltage_limits,
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in voltage profile analysis: {e}")
            return {"error": str(e)}
    
    def load_analysis(self, base_case_id=None):
        """Analyze active and reactive load demand per bus"""
        try:
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {"error": "No suitable base case found"}
            
            buses, _ = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                return {"error": "No bus data found"}
            
            # Extract load data
            pd_col = 'PD' if 'PD' in buses.columns else 'active_demand'
            qd_col = 'QD' if 'QD' in buses.columns else 'reactive_demand'
            
            if pd_col not in buses.columns or qd_col not in buses.columns:
                return {"error": "Load data columns not found"}
            
            # Analyze load patterns
            active_loads = buses[pd_col].fillna(0)
            reactive_loads = buses[qd_col].fillna(0)
            bus_numbers = buses['bus_number'] if 'bus_number' in buses.columns else buses.index
            
            # Filter only load buses (buses with actual demand)
            load_mask = (active_loads > 0) | (reactive_loads > 0)
            load_buses = bus_numbers[load_mask].tolist()
            active_load_values = active_loads[load_mask].tolist()
            reactive_load_values = reactive_loads[load_mask].tolist()
            
            # Calculate load statistics
            total_active_load = float(active_loads.sum())
            total_reactive_load = float(reactive_loads.sum())
            
            load_stats = {
                "total_active_load_mw": total_active_load,
                "total_reactive_load_mvar": total_reactive_load,
                "average_active_load": total_active_load / len(load_buses) if load_buses else 0,
                "average_reactive_load": total_reactive_load / len(load_buses) if load_buses else 0,
                "max_active_load": float(active_loads.max()) if len(active_loads) > 0 else 0,
                "max_reactive_load": float(reactive_loads.max()) if len(reactive_loads) > 0 else 0,
                "number_of_load_buses": len(load_buses)
            }
            
            # Identify high-load buses (top 10%)
            if len(active_load_values) > 0:
                active_sorted = sorted(active_load_values, reverse=True)
                threshold_90 = active_sorted[int(len(active_sorted) * 0.1)] if len(active_sorted) > 10 else active_sorted[0]
                high_load_buses = [(load_buses[i], active_load_values[i]) for i in range(len(active_load_values)) 
                                 if active_load_values[i] >= threshold_90]
            else:
                high_load_buses = []
            
            return {
                "load_statistics": load_stats,
                "load_buses": load_buses,
                "active_loads": active_load_values,
                "reactive_loads": reactive_load_values,
                "high_load_buses": high_load_buses,
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in load analysis: {e}")
            return {"error": str(e)}
    
    def generation_analysis(self, base_case_id=None):
        """Analyze real and reactive power generation from generators"""
        try:
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {"error": "No suitable base case found"}
            
            buses, _ = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                return {"error": "No bus data found"}
            
            # Extract generation data
            pg_col = 'PG' if 'PG' in buses.columns else 'active_generation'
            qg_col = 'QG' if 'QG' in buses.columns else 'reactive_generation'
            
            if pg_col not in buses.columns or qg_col not in buses.columns:
                return {"error": "Generation data columns not found"}
            
            # Analyze generation patterns
            active_gens = buses[pg_col].fillna(0)
            reactive_gens = buses[qg_col].fillna(0)
            bus_numbers = buses['bus_number'] if 'bus_number' in buses.columns else buses.index
            
            # Filter generator buses (buses with generation)
            gen_mask = (active_gens > 0) | (reactive_gens != 0)
            gen_buses = bus_numbers[gen_mask].tolist()
            active_gen_values = active_gens[gen_mask].tolist()
            reactive_gen_values = reactive_gens[gen_mask].tolist()
            
            # Calculate generation statistics
            total_active_gen = float(active_gens.sum())
            total_reactive_gen = float(reactive_gens.sum())
            
            # Get load data for generation vs demand balance
            load_result = self.load_analysis(base_case_id)
            if "load_statistics" in load_result:
                total_load = load_result["load_statistics"]["total_active_load_mw"]
                total_reactive_load = load_result["load_statistics"]["total_reactive_load_mvar"]
                active_balance = total_active_gen - total_load
                reactive_balance = total_reactive_gen - total_reactive_load
            else:
                active_balance = "Unknown"
                reactive_balance = "Unknown"
            
            gen_stats = {
                "total_active_generation_mw": total_active_gen,
                "total_reactive_generation_mvar": total_reactive_gen,
                "number_of_generators": len(gen_buses),
                "average_active_generation": total_active_gen / len(gen_buses) if gen_buses else 0,
                "max_active_generation": float(active_gens.max()) if len(active_gens) > 0 else 0,
                "active_power_balance": active_balance,
                "reactive_power_balance": reactive_balance
            }
            
            return {
                "generation_statistics": gen_stats,
                "generator_buses": gen_buses,
                "active_generations": active_gen_values,
                "reactive_generations": reactive_gen_values,
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in generation analysis: {e}")
            return {"error": str(e)}
    
    def enhanced_voltage_violation_count(self, base_case_id=None, voltage_limits=(0.95, 1.05)):
        """Enhanced voltage violation counting with comprehensive statistics"""
        try:
            voltage_analysis = self.voltage_profile_analysis(base_case_id, voltage_limits)
            
            if "error" in voltage_analysis:
                return voltage_analysis
            
            total_violations = (
                voltage_analysis["under_voltage_violations"]["count"] + 
                voltage_analysis["over_voltage_violations"]["count"]
            )
            
            return {
                "total_voltage_violations": total_violations,
                "under_voltage_count": voltage_analysis["under_voltage_violations"]["count"],
                "over_voltage_count": voltage_analysis["over_voltage_violations"]["count"],
                "total_buses": voltage_analysis["total_buses"],
                "violation_percentage": (total_violations / voltage_analysis["total_buses"]) * 100 if voltage_analysis["total_buses"] > 0 else 0,
                "voltage_limits": voltage_limits,
                "voltage_statistics": voltage_analysis["voltage_statistics"],
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error counting voltage violations: {e}")
            return {"error": str(e)}

    def voltage_violation_analysis(self, base_case_id=None, v_min=0.95, v_max=1.05):
        """
        Analyze voltage violations in the system
        If base_case_id is None, automatically selects the best available case
        """
        try:
            # Auto-select base case if not specified
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return self._get_voltage_analysis_from_any_source(v_min, v_max)
            
            buses, _ = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                # Try alternative sources
                return self._get_voltage_analysis_from_any_source(v_min, v_max)
            
            voltages = buses['VM']
            
            # Identify violations
            low_voltage_buses = buses[buses['VM'] < v_min]
            high_voltage_buses = buses[buses['VM'] > v_max]
            
            violation_analysis = {
                'base_case_id': base_case_id,
                'voltage_limits': {'min': v_min, 'max': v_max},
                'total_buses': len(buses),
                'buses_in_limits': len(buses[(buses['VM'] >= v_min) & (buses['VM'] <= v_max)]),
                'low_voltage_violations': {
                    'count': len(low_voltage_buses),
                    'percentage': (len(low_voltage_buses) / len(buses)) * 100,
                    'worst_voltage': low_voltage_buses['VM'].min() if not low_voltage_buses.empty else None,
                    'worst_bus': low_voltage_buses.loc[low_voltage_buses['VM'].idxmin(), 'BUS_NUMBER'] if not low_voltage_buses.empty else None,
                    'bus_details': low_voltage_buses[['BUS_NUMBER', 'VM', 'PD', 'QD']].to_dict('records') if not low_voltage_buses.empty else []
                },
                'high_voltage_violations': {
                    'count': len(high_voltage_buses),
                    'percentage': (len(high_voltage_buses) / len(buses)) * 100,
                    'worst_voltage': high_voltage_buses['VM'].max() if not high_voltage_buses.empty else None,
                    'worst_bus': high_voltage_buses.loc[high_voltage_buses['VM'].idxmax(), 'BUS_NUMBER'] if not high_voltage_buses.empty else None,
                    'bus_details': high_voltage_buses[['BUS_NUMBER', 'VM', 'PG', 'QG']].to_dict('records') if not high_voltage_buses.empty else []
                },
                'voltage_statistics': {
                    'min_voltage': voltages.min(),
                    'max_voltage': voltages.max(),
                    'avg_voltage': voltages.mean(),
                    'voltage_std': voltages.std(),
                    'median_voltage': voltages.median()
                }
            }
            
            return violation_analysis
            
        except Exception as e:
            print(f"Error in voltage violation analysis: {e}")
            return self._get_voltage_analysis_from_any_source(v_min, v_max)
    
    def _get_voltage_analysis_from_any_source(self, v_min=0.95, v_max=1.05):
        """Get voltage analysis from any available data source"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Find tables with voltage data
            tables_with_voltage = []
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                if 'Bus' in table:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    if 'VM' in columns:
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE VM IS NOT NULL")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            tables_with_voltage.append((table, count))
            
            if not tables_with_voltage:
                conn.close()
                return {'error': 'No voltage data found in database'}
            
            # Use the table with the most voltage data
            best_table = max(tables_with_voltage, key=lambda x: x[1])[0]
            
            # Get voltage data from best table
            voltage_query = f"""
            SELECT VM, BUS_NUMBER, PD, QD, PG, QG 
            FROM {best_table} 
            WHERE VM IS NOT NULL
            """
            
            buses_df = pd.read_sql_query(voltage_query, conn)
            conn.close()
            
            if buses_df.empty:
                return {'error': 'No valid voltage data found'}
            
            voltages = buses_df['VM']
            low_voltage_buses = buses_df[buses_df['VM'] < v_min]
            high_voltage_buses = buses_df[buses_df['VM'] > v_max]
            
            return {
                'data_source': best_table,
                'voltage_limits': {'min': v_min, 'max': v_max},
                'total_buses': len(buses_df),
                'buses_in_limits': len(buses_df[(buses_df['VM'] >= v_min) & (buses_df['VM'] <= v_max)]),
                'low_voltage_violations': {
                    'count': len(low_voltage_buses),
                    'percentage': (len(low_voltage_buses) / len(buses_df)) * 100,
                    'worst_voltage': low_voltage_buses['VM'].min() if not low_voltage_buses.empty else None,
                    'worst_bus': low_voltage_buses.loc[low_voltage_buses['VM'].idxmin(), 'BUS_NUMBER'] if not low_voltage_buses.empty else None,
                    'bus_details': low_voltage_buses.to_dict('records') if not low_voltage_buses.empty else []
                },
                'high_voltage_violations': {
                    'count': len(high_voltage_buses),
                    'percentage': (len(high_voltage_buses) / len(buses_df)) * 100,
                    'worst_voltage': high_voltage_buses['VM'].max() if not high_voltage_buses.empty else None,
                    'worst_bus': high_voltage_buses.loc[high_voltage_buses['VM'].idxmax(), 'BUS_NUMBER'] if not high_voltage_buses.empty else None,
                    'bus_details': high_voltage_buses.to_dict('records') if not high_voltage_buses.empty else []
                },
                'voltage_statistics': {
                    'min_voltage': voltages.min(),
                    'max_voltage': voltages.max(),
                    'avg_voltage': voltages.mean(),
                    'voltage_std': voltages.std(),
                    'median_voltage': voltages.median()
                }
            }
            
        except Exception as e:
            print(f"Error getting voltage analysis from any source: {e}")
            return {'error': f'Could not analyze voltage data: {str(e)}'}

    # =====================================================
    # 🔹 COMPREHENSIVE BRANCH-LEVEL ANALYSIS METHODS  
    # =====================================================
    
    def power_flow_analysis(self, base_case_id=None):
        """Analyze real and reactive power flow on each branch"""
        try:
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {"error": "No suitable base case found"}
            
            _, branches = self.load_base_case_data(base_case_id)
            
            if branches.empty:
                return {"error": "No branch data found"}
            
            # Extract power flow data
            pf_col = 'PF' if 'PF' in branches.columns else 'real_power_flow'
            qf_col = 'QF' if 'QF' in branches.columns else 'reactive_power_flow'
            
            if pf_col not in branches.columns or qf_col not in branches.columns:
                return {"error": "Power flow data columns not found"}
            
            real_flows = branches[pf_col].fillna(0)
            reactive_flows = branches[qf_col].fillna(0)
            
            # Calculate flow statistics
            flow_stats = {
                "total_real_flow": float(real_flows.abs().sum()),
                "total_reactive_flow": float(reactive_flows.abs().sum()),
                "max_real_flow": float(real_flows.abs().max()),
                "max_reactive_flow": float(reactive_flows.abs().max()),
                "avg_real_flow": float(real_flows.abs().mean()),
                "avg_reactive_flow": float(reactive_flows.abs().mean()),
                "number_of_branches": len(branches)
            }
            
            # Identify heavily loaded lines (top 20%)
            real_flow_abs = real_flows.abs()
            if len(real_flow_abs) > 0:
                flow_sorted = real_flow_abs.sort_values(ascending=False)
                heavy_load_threshold = flow_sorted.iloc[int(len(flow_sorted) * 0.2)] if len(flow_sorted) > 5 else flow_sorted.iloc[0]
                heavily_loaded_indices = real_flow_abs[real_flow_abs >= heavy_load_threshold].index
                
                heavily_loaded_lines = []
                for idx in heavily_loaded_indices:
                    branch_info = branches.loc[idx]
                    from_bus = branch_info.get('FROM_BUS', branch_info.get('from_bus', 'Unknown'))
                    to_bus = branch_info.get('TO_BUS', branch_info.get('to_bus', 'Unknown'))
                    heavily_loaded_lines.append({
                        'from_bus': from_bus,
                        'to_bus': to_bus,
                        'real_flow': float(real_flows.loc[idx]),
                        'reactive_flow': float(reactive_flows.loc[idx])
                    })
            else:
                heavily_loaded_lines = []
            
            return {
                "power_flow": {
                    "p_flow": real_flows.tolist(),
                    "q_flow": reactive_flows.tolist()
                },
                "flow_statistics": flow_stats,
                "heavily_loaded_lines": heavily_loaded_lines,
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in power flow analysis: {e}")
            return {"error": str(e)}
    
    def line_loading_analysis(self, base_case_id=None, loading_threshold=80.0):
        """Analyze line loading and utilization compared to thermal limits"""
        try:
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {"error": "No suitable base case found"}
            
            _, branches = self.load_base_case_data(base_case_id)
            
            if branches.empty:
                return {"error": "No branch data found"}
            
            # Calculate MVA flows and compare to thermal limits
            pf_col = 'PF' if 'PF' in branches.columns else 'real_power_flow'
            qf_col = 'QF' if 'QF' in branches.columns else 'reactive_power_flow'
            rate_col = 'RATE_A' if 'RATE_A' in branches.columns else 'thermal_limit'
            
            if pf_col not in branches.columns or qf_col not in branches.columns:
                return {"error": "Power flow data columns not found"}
            
            real_flows = branches[pf_col].fillna(0)
            reactive_flows = branches[qf_col].fillna(0)
            
            # Calculate MVA flows
            mva_flows = (real_flows**2 + reactive_flows**2)**0.5
            
            # Get thermal limits
            if rate_col in branches.columns:
                thermal_limits = branches[rate_col].fillna(100)  # Default 100 MVA if missing
            else:
                thermal_limits = pd.Series([100] * len(branches))  # Default values
            
            # Calculate loading percentages
            loading_percentages = (mva_flows / thermal_limits * 100).fillna(0)
            
            # Classify lines by loading
            overloaded_lines = []
            heavily_loaded_lines = []
            normal_lines = []
            
            for idx, loading in loading_percentages.items():
                branch_info = branches.loc[idx]
                from_bus = branch_info.get('FROM_BUS', branch_info.get('from_bus', 'Unknown'))
                to_bus = branch_info.get('TO_BUS', branch_info.get('to_bus', 'Unknown'))
                
                line_data = {
                    'from_bus': from_bus,
                    'to_bus': to_bus,
                    'loading_percentage': float(loading),
                    'mva_flow': float(mva_flows.loc[idx]),
                    'thermal_limit': float(thermal_limits.loc[idx])
                }
                
                if loading >= 100:
                    overloaded_lines.append(line_data)
                elif loading >= loading_threshold:
                    heavily_loaded_lines.append(line_data)
                else:
                    normal_lines.append(line_data)
            
            # Calculate loading statistics
            loading_stats = {
                "max_loading_percentage": float(loading_percentages.max()),
                "avg_loading_percentage": float(loading_percentages.mean()),
                "overloaded_lines_count": len(overloaded_lines),
                "heavily_loaded_lines_count": len(heavily_loaded_lines),
                "normal_lines_count": len(normal_lines),
                "total_branches": len(branches)
            }
            
            return {
                "thermal_loading": loading_percentages.tolist(),
                "loading_statistics": loading_stats,
                "overloaded_branches": {
                    "count": len(overloaded_lines),
                    "lines": overloaded_lines
                },
                "heavily_loaded_branches": {
                    "count": len(heavily_loaded_lines),
                    "lines": heavily_loaded_lines
                },
                "normal_branches": {
                    "count": len(normal_lines)
                },
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in line loading analysis: {e}")
            return {"error": str(e)}
    
    def loss_analysis(self, base_case_id=None):
        """Calculate real and reactive power losses across all branches"""
        try:
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {"error": "No suitable base case found"}
            
            _, branches = self.load_base_case_data(base_case_id)
            
            if branches.empty:
                return {"error": "No branch data found"}
            
            # Calculate losses: PF_from + PF_to (losses are the difference)
            pf_from_col = 'PF' if 'PF' in branches.columns else 'real_power_from'
            qf_from_col = 'QF' if 'QF' in branches.columns else 'reactive_power_from'
            pf_to_col = 'PT' if 'PT' in branches.columns else 'real_power_to'
            qf_to_col = 'QT' if 'QT' in branches.columns else 'reactive_power_to'
            
            # If we only have one direction, estimate losses
            if pf_from_col in branches.columns:
                real_flows = branches[pf_from_col].fillna(0)
                reactive_flows = branches[qf_from_col].fillna(0) if qf_from_col in branches.columns else pd.Series([0] * len(branches))
                
                # Estimate losses as percentage of flow (typically 1-3% for transmission lines)
                real_losses = real_flows.abs() * 0.02  # 2% loss estimation
                reactive_losses = reactive_flows.abs() * 0.015  # 1.5% loss estimation
                
                total_real_losses = float(real_losses.sum())
                total_reactive_losses = float(reactive_losses.sum())
                
            else:
                return {"error": "Insufficient power flow data for loss calculation"}
            
            # Calculate loss statistics
            loss_stats = {
                "total_real_losses_mw": total_real_losses,
                "total_reactive_losses_mvar": total_reactive_losses,
                "average_real_loss_per_branch": total_real_losses / len(branches) if len(branches) > 0 else 0,
                "max_real_loss_per_branch": float(real_losses.max()),
                "loss_percentage_of_total_flow": (total_real_losses / real_flows.abs().sum()) * 100 if real_flows.abs().sum() > 0 else 0
            }
            
            return {
                "real_power_losses": real_losses.tolist(),
                "reactive_power_losses": reactive_losses.tolist(),
                "loss_statistics": loss_stats,
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in loss analysis: {e}")
            return {"error": str(e)}
    
    def branch_violation_detection(self, base_case_id=None):
        """Identify branches exceeding flow limits"""
        try:
            loading_analysis = self.line_loading_analysis(base_case_id)
            
            if "error" in loading_analysis:
                return loading_analysis
            
            violations = loading_analysis["overloaded_branches"]["lines"]
            violation_count = loading_analysis["overloaded_branches"]["count"]
            total_branches = loading_analysis["loading_statistics"]["total_branches"]
            
            return {
                "branch_violations": violations,
                "violation_count": violation_count,
                "total_branches": total_branches,
                "violation_percentage": (violation_count / total_branches) * 100 if total_branches > 0 else 0,
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in branch violation detection: {e}")
            return {"error": str(e)}

    def contingency_impact_analysis(self, base_case_id=None, contingency_case_ids=None):
        """
        Analyze the impact of contingencies on system performance
        If base_case_id is None, automatically selects the best available case
        """
        try:
            # Auto-select base case if not specified
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {'error': 'No base case data available for contingency analysis'}
            
            if contingency_case_ids is None:
                # Try to find available contingency cases
                contingency_case_ids = self._get_available_contingency_cases()
                if not contingency_case_ids:
                    contingency_case_ids = [1, 2, 3, 4, 5]  # Default fallback
            
            base_buses, base_branches = self.load_base_case_data(base_case_id)
            contingency_results = []
            
            for cont_id in contingency_case_ids:
                cont_buses, cont_branches = self.load_contingency_data(cont_id, base_case_id)
                
                if not cont_buses.empty and not cont_branches.empty:
                    # Voltage impact
                    voltage_changes = []
                    if not base_buses.empty:
                        base_voltages = base_buses.set_index('BUS_NUMBER')['VM']
                        cont_voltages = cont_buses.set_index('BUS_NUMBER')['VM']
                        
                        # Find common buses
                        common_buses = base_voltages.index.intersection(cont_voltages.index)
                        if len(common_buses) > 0:
                            voltage_changes = (cont_voltages[common_buses] - base_voltages[common_buses]).tolist()
                    
                    # Branch violations
                    violations = 0
                    if 'VIO' in cont_branches.columns:
                        violations = cont_branches['VIO'].sum()
                    
                    # Loading analysis
                    if 'PF' in cont_branches.columns and 'QF' in cont_branches.columns and 'RATE' in cont_branches.columns:
                        apparent_flow = np.sqrt(cont_branches['PF']**2 + cont_branches['QF']**2)
                        loading_pct = (apparent_flow / cont_branches['RATE']) * 100
                        max_loading = loading_pct.max()
                        overloaded_branches = (loading_pct > 100).sum()
                    else:
                        max_loading = 0
                        overloaded_branches = 0
                    
                    contingency_result = {
                        'contingency_id': cont_id,
                        'base_case_id': base_case_id,
                        'voltage_impact': {
                            'max_voltage_change': max(voltage_changes, key=abs) if voltage_changes else 0,
                            'avg_voltage_change': np.mean(voltage_changes) if voltage_changes else 0,
                            'buses_analyzed': len(voltage_changes)
                        },
                        'branch_impact': {
                            'total_violations': violations,
                            'max_loading_pct': max_loading,
                            'overloaded_branches': overloaded_branches,
                            'total_branches': len(cont_branches)
                        },
                        'severity_score': violations + overloaded_branches + (abs(max(voltage_changes, key=abs)) * 100 if voltage_changes else 0)
                    }
                    
                    contingency_results.append(contingency_result)
            
            if not contingency_results:
                return {'error': 'No valid contingency data found'}
            
            # Overall contingency impact summary
            impact_summary = {
                'base_case_id': base_case_id,
                'contingencies_analyzed': len(contingency_results),
                'worst_contingency': max(contingency_results, key=lambda x: x['severity_score'])['contingency_id'] if contingency_results else None,
                'total_violations': sum(r['branch_impact']['total_violations'] for r in contingency_results),
                'avg_max_loading': np.mean([r['branch_impact']['max_loading_pct'] for r in contingency_results]),
                'contingency_details': contingency_results
            }
            
            return impact_summary
            
        except Exception as e:
            print(f"Error in contingency impact analysis: {e}")
            return {'error': f'Contingency analysis failed: {str(e)}'}
    
    # =====================================================
    # 🔹 COMPREHENSIVE SYSTEM-LEVEL ANALYSIS METHODS
    # =====================================================
    
    def power_balance_analysis(self, base_case_id=None):
        """Analyze total generation vs total load (active + reactive)"""
        try:
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {"error": "No suitable base case found"}
            
            # Get generation and load analyses
            gen_result = self.generation_analysis(base_case_id)
            load_result = self.load_analysis(base_case_id)
            
            if "error" in gen_result or "error" in load_result:
                return {"error": "Could not obtain generation or load data"}
            
            gen_stats = gen_result["generation_statistics"]
            load_stats = load_result["load_statistics"]
            
            # Calculate power balance
            active_balance = gen_stats["total_active_generation_mw"] - load_stats["total_active_load_mw"]
            reactive_balance = gen_stats["total_reactive_generation_mvar"] - load_stats["total_reactive_load_mvar"]
            
            # Calculate reserve margins
            active_reserve_margin = (active_balance / load_stats["total_active_load_mw"]) * 100 if load_stats["total_active_load_mw"] > 0 else 0
            
            return {
                "power_balance": {
                    "total_generation_mw": gen_stats["total_active_generation_mw"],
                    "total_load_mw": load_stats["total_active_load_mw"],
                    "active_power_balance_mw": active_balance,
                    "reactive_power_balance_mvar": reactive_balance,
                    "active_reserve_margin_percent": active_reserve_margin,
                    "generation_load_ratio": gen_stats["total_active_generation_mw"] / load_stats["total_active_load_mw"] if load_stats["total_active_load_mw"] > 0 else 0
                },
                "system_status": "Surplus" if active_balance > 0 else "Deficit" if active_balance < 0 else "Balanced",
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in power balance analysis: {e}")
            return {"error": str(e)}
    
    def system_losses_analysis(self, base_case_id=None):
        """Calculate total active & reactive losses across all lines"""
        try:
            loss_result = self.loss_analysis(base_case_id)
            
            if "error" in loss_result:
                return loss_result
            
            loss_stats = loss_result["loss_statistics"]
            
            # Get total system power for loss percentage calculation
            power_balance = self.power_balance_analysis(base_case_id)
            
            if "error" not in power_balance:
                total_generation = power_balance["power_balance"]["total_generation_mw"]
                loss_percentage = (loss_stats["total_real_losses_mw"] / total_generation) * 100 if total_generation > 0 else 0
            else:
                loss_percentage = loss_stats["loss_percentage_of_total_flow"]
            
            return {
                "system_losses": {
                    "total_real_losses_mw": loss_stats["total_real_losses_mw"],
                    "total_reactive_losses_mvar": loss_stats["total_reactive_losses_mvar"],
                    "loss_percentage_of_generation": loss_percentage,
                    "average_loss_per_branch": loss_stats["average_real_loss_per_branch"],
                    "max_loss_per_branch": loss_stats["max_real_loss_per_branch"]
                },
                "loss_assessment": "High" if loss_percentage > 5 else "Medium" if loss_percentage > 2 else "Low",
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in system losses analysis: {e}")
            return {"error": str(e)}
    
    def system_reliability_indices(self, base_case_id=None):
        """Calculate basic reliability indices (% of overloaded lines, % of buses with voltage violations)"""
        try:
            # Get voltage violations
            voltage_violations = self.enhanced_voltage_violation_count(base_case_id)
            
            # Get branch violations
            branch_violations = self.branch_violation_detection(base_case_id)
            
            if "error" in voltage_violations or "error" in branch_violations:
                return {"error": "Could not obtain violation data for reliability analysis"}
            
            # Calculate reliability indices
            voltage_violation_percentage = voltage_violations["violation_percentage"]
            branch_overload_percentage = branch_violations["violation_percentage"]
            
            # Overall system health score (0-100, where 100 is perfect)
            system_health_score = 100 - (voltage_violation_percentage + branch_overload_percentage) / 2
            
            return {
                "reliability_indices": {
                    "voltage_violation_percentage": voltage_violation_percentage,
                    "branch_overload_percentage": branch_overload_percentage,
                    "buses_in_violation": voltage_violations["total_voltage_violations"],
                    "branches_overloaded": branch_violations["violation_count"],
                    "total_buses": voltage_violations["total_buses"],
                    "total_branches": branch_violations["total_branches"],
                    "system_health_score": max(0, system_health_score)
                },
                "reliability_assessment": "Excellent" if system_health_score > 95 else 
                                       "Good" if system_health_score > 85 else
                                       "Fair" if system_health_score > 70 else "Poor",
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating reliability indices: {e}")
            return {"error": str(e)}
    
    def n_minus_1_analysis(self, base_case_id=None):
        """Identify N-1 critical elements based on contingency analysis"""
        try:
            contingency_result = self.contingency_impact_analysis(base_case_id)
            
            if "error" in contingency_result:
                return contingency_result
            
            if "contingency_details" not in contingency_result:
                return {"error": "No contingency details available"}
            
            # Analyze contingency results to find critical elements
            contingencies = contingency_result["contingency_details"]
            
            critical_contingencies = []
            high_impact_contingencies = []
            
            for contingency in contingencies:
                severity_score = contingency.get("severity_score", 0)
                
                if severity_score > 50:  # High severity threshold
                    critical_contingencies.append({
                        "contingency_id": contingency["contingency_id"],
                        "severity_score": severity_score,
                        "voltage_violations": contingency["voltage_impact"]["max_voltage_change"],
                        "branch_violations": contingency["branch_impact"]["total_violations"]
                    })
                elif severity_score > 20:  # Medium severity threshold
                    high_impact_contingencies.append({
                        "contingency_id": contingency["contingency_id"],
                        "severity_score": severity_score
                    })
            
            return {
                "n_minus_1_analysis": {
                    "critical_contingencies": critical_contingencies,
                    "high_impact_contingencies": high_impact_contingencies,
                    "total_contingencies_analyzed": len(contingencies),
                    "critical_percentage": (len(critical_contingencies) / len(contingencies)) * 100 if contingencies else 0
                },
                "system_resilience": "Vulnerable" if len(critical_contingencies) > len(contingencies) * 0.2 else
                                   "Moderate" if len(critical_contingencies) > 0 else "Robust",
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in N-1 analysis: {e}")
            return {"error": str(e)}
    
    # =====================================================
    # 🔹 COMPARATIVE ANALYSIS (Base vs. SLR vs. DLR) 
    # =====================================================
    
    def dlr_benefits_analysis(self, base_case_id=None, slr_case_id=None, dlr_case_id=None):
        """Analyze DLR benefits compared to base case and SLR"""
        try:
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
            
            # Get analyses for different cases
            base_violations = self.branch_violation_detection(base_case_id) if base_case_id else {"error": "No base case"}
            slr_violations = self.branch_violation_detection(slr_case_id) if slr_case_id else {"error": "No SLR case"}
            dlr_violations = self.branch_violation_detection(dlr_case_id) if dlr_case_id else {"error": "No DLR case"}
            
            # Calculate improvements
            benefits = {
                "base_case_violations": base_violations.get("violation_count", "N/A"),
                "slr_case_violations": slr_violations.get("violation_count", "N/A"),
                "dlr_case_violations": dlr_violations.get("violation_count", "N/A")
            }
            
            # Calculate reductions if data is available
            if "error" not in base_violations and "error" not in dlr_violations:
                base_count = base_violations["violation_count"]
                dlr_count = dlr_violations["violation_count"]
                
                violation_reduction = base_count - dlr_count
                violation_reduction_percentage = (violation_reduction / base_count) * 100 if base_count > 0 else 0
                
                benefits.update({
                    "dlr_violation_reduction": violation_reduction,
                    "dlr_violation_reduction_percentage": violation_reduction_percentage,
                    "dlr_effectiveness": "High" if violation_reduction_percentage > 50 else
                                       "Medium" if violation_reduction_percentage > 20 else "Low"
                })
            
            return {
                "dlr_benefits": benefits,
                "transfer_capability_improvement": "Analysis requires load increment data",
                "reliability_improvement": "Calculated from violation reductions"
            }
            
        except Exception as e:
            self.logger.error(f"Error in DLR benefits analysis: {e}")
            return {"error": str(e)}
    
    def stress_points_analysis(self, base_case_id=None):
        """Compare contingency impacts to identify system stress points"""
        try:
            # Get contingency analysis
            contingency_result = self.contingency_impact_analysis(base_case_id)
            
            if "error" in contingency_result:
                return contingency_result
            
            # Get line loading analysis
            loading_result = self.line_loading_analysis(base_case_id)
            
            if "error" in loading_result:
                return loading_result
            
            # Identify stress points
            heavily_loaded = loading_result["heavily_loaded_branches"]["lines"]
            overloaded = loading_result["overloaded_branches"]["lines"]
            
            # Find common stress points between loading and contingencies
            stress_points = []
            
            # High loading branches are stress points
            for line in heavily_loaded + overloaded:
                stress_points.append({
                    "type": "thermal_stress",
                    "from_bus": line["from_bus"],
                    "to_bus": line["to_bus"],
                    "loading_percentage": line["loading_percentage"],
                    "criticality": "High" if line["loading_percentage"] > 100 else "Medium"
                })
            
            return {
                "system_stress_points": stress_points,
                "total_stress_points": len(stress_points),
                "critical_stress_points": len([sp for sp in stress_points if sp["criticality"] == "High"]),
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in stress points analysis: {e}")
            return {"error": str(e)}
    
    # =====================================================
    # 🔹 ADVANCED STATISTICAL ANALYSIS METHODS
    # =====================================================
    
    def correlation_analysis(self, base_case_id=None):
        """Analyze correlations between load growth, voltages, and violations"""
        try:
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {"error": "No suitable base case found"}
            
            buses, branches = self.load_base_case_data(base_case_id)
            
            if buses.empty or branches.empty:
                return {"error": "Insufficient data for correlation analysis"}
            
            # Create correlation datasets
            correlations = {}
            
            # Bus voltage vs load correlation
            if 'VM' in buses.columns and 'PD' in buses.columns:
                voltage_load_corr = buses['VM'].corr(buses['PD'])
                correlations["voltage_vs_load"] = float(voltage_load_corr) if pd.notna(voltage_load_corr) else 0
            
            # Voltage vs reactive load correlation
            if 'VM' in buses.columns and 'QD' in buses.columns:
                voltage_reactive_corr = buses['VM'].corr(buses['QD'])
                correlations["voltage_vs_reactive_load"] = float(voltage_reactive_corr) if pd.notna(voltage_reactive_corr) else 0
            
            # Branch loading vs voltage correlation (using maximum loading per bus)
            if 'PF' in branches.columns and 'VM' in buses.columns:
                # This is a simplified correlation - would need more complex analysis for real correlation
                correlations["loading_vs_voltage"] = "Complex correlation requires detailed analysis"
            
            return {
                "correlation_analysis": correlations,
                "interpretation": {
                    "voltage_load_relationship": "Strong negative correlation indicates voltage drop with increased load" if correlations.get("voltage_vs_load", 0) < -0.5 else "Moderate relationship",
                    "reactive_power_impact": "Reactive power significantly affects voltage" if abs(correlations.get("voltage_vs_reactive_load", 0)) > 0.3 else "Limited reactive power impact"
                },
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in correlation analysis: {e}")
            return {"error": str(e)}
    
    def distribution_analysis(self, base_case_id=None):
        """Analyze distribution of bus voltages and branch loadings"""
        try:
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {"error": "No suitable base case found"}
            
            buses, branches = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                return {"error": "No bus data available for distribution analysis"}
            
            # Voltage distribution analysis
            voltage_distribution = {}
            if 'VM' in buses.columns:
                voltages = buses['VM'].dropna()
                voltage_distribution = {
                    "mean": float(voltages.mean()),
                    "std": float(voltages.std()),
                    "min": float(voltages.min()),
                    "max": float(voltages.max()),
                    "percentile_25": float(voltages.quantile(0.25)),
                    "percentile_50": float(voltages.quantile(0.50)),
                    "percentile_75": float(voltages.quantile(0.75)),
                    "percentile_95": float(voltages.quantile(0.95)),
                    "voltage_bins": {
                        "below_0.95": len(voltages[voltages < 0.95]),
                        "0.95_to_1.00": len(voltages[(voltages >= 0.95) & (voltages < 1.00)]),
                        "1.00_to_1.05": len(voltages[(voltages >= 1.00) & (voltages < 1.05)]),
                        "above_1.05": len(voltages[voltages >= 1.05])
                    }
                }
            
            # Branch loading distribution
            loading_distribution = {}
            if not branches.empty and 'PF' in branches.columns:
                # Calculate loading percentages (simplified)
                power_flows = branches['PF'].abs().dropna()
                loading_distribution = {
                    "mean_flow": float(power_flows.mean()),
                    "std_flow": float(power_flows.std()),
                    "max_flow": float(power_flows.max()),
                    "flow_bins": {
                        "low_flow": len(power_flows[power_flows < power_flows.quantile(0.33)]),
                        "medium_flow": len(power_flows[(power_flows >= power_flows.quantile(0.33)) & (power_flows < power_flows.quantile(0.67))]),
                        "high_flow": len(power_flows[power_flows >= power_flows.quantile(0.67)])
                    }
                }
            
            return {
                "voltage_distribution": voltage_distribution,
                "loading_distribution": loading_distribution,
                "distribution_assessment": {
                    "voltage_spread": "Wide" if voltage_distribution.get("std", 0) > 0.05 else "Narrow",
                    "system_balance": "Well-balanced" if voltage_distribution.get("std", 0) < 0.03 else "Unbalanced"
                },
                "base_case_id": base_case_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in distribution analysis: {e}")
            return {"error": str(e)}
    
    def outlier_detection(self, base_case_id=None):
        """Identify buses/branches consistently causing issues"""
        try:
            # Get voltage violations
            voltage_analysis = self.voltage_profile_analysis(base_case_id)
            
            # Get branch violations  
            branch_analysis = self.branch_violation_detection(base_case_id)
            
            outliers = {
                "problematic_buses": [],
                "problematic_branches": [],
                "outlier_summary": {}
            }
            
            # Voltage outliers
            if "error" not in voltage_analysis:
                under_voltage_buses = voltage_analysis["under_voltage_violations"]["buses"]
                over_voltage_buses = voltage_analysis["over_voltage_violations"]["buses"]
                
                for bus_num, voltage in under_voltage_buses:
                    outliers["problematic_buses"].append({
                        "bus": bus_num,
                        "issue": "under_voltage",
                        "voltage": voltage,
                        "severity": "High" if voltage < 0.90 else "Medium"
                    })
                
                for bus_num, voltage in over_voltage_buses:
                    outliers["problematic_buses"].append({
                        "bus": bus_num,
                        "issue": "over_voltage", 
                        "voltage": voltage,
                        "severity": "High" if voltage > 1.10 else "Medium"
                    })
            
            # Branch outliers
            if "error" not in branch_analysis:
                problematic_branches = branch_analysis["branch_violations"]
                
                for branch in problematic_branches:
                    outliers["problematic_branches"].append({
                        "from_bus": branch["from_bus"],
                        "to_bus": branch["to_bus"],
                        "issue": "overloading",
                        "loading_percentage": branch["loading_percentage"],
                        "severity": "Critical" if branch["loading_percentage"] > 110 else "High"
                    })
            
            # Outlier summary
            outliers["outlier_summary"] = {
                "total_problematic_buses": len(outliers["problematic_buses"]),
                "total_problematic_branches": len(outliers["problematic_branches"]),
                "critical_issues": len([item for sublist in [outliers["problematic_buses"], outliers["problematic_branches"]] 
                                      for item in sublist if item.get("severity") in ["Critical", "High"]])
            }
            
            return outliers
            
        except Exception as e:
            self.logger.error(f"Error in outlier detection: {e}")
            return {"error": str(e)}
    
    def _get_available_contingency_cases(self):
        """Find available contingency case IDs in the database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check ContingencyBusData table
            cursor.execute("SELECT DISTINCT contingency_case_id FROM ContingencyBusData ORDER BY contingency_case_id LIMIT 10")
            case_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if case_ids:
                print(f"📊 Found contingency cases: {case_ids[:5]}{'...' if len(case_ids) > 5 else ''}")
            
            return case_ids[:10]  # Limit to first 10 for performance
            
        except Exception as e:
            print(f"Error finding contingency cases: {e}")
            return []

    def generation_dispatch_analysis(self, base_case_id=None):
        """
        Analyze generation dispatch and patterns
        If base_case_id is None, automatically selects the best available case
        """
        try:
            # Auto-select base case if not specified
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return self._get_generation_analysis_from_any_source()
            
            buses, _ = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                return self._get_generation_analysis_from_any_source()
            
            # Filter generating buses
            generating_buses = buses[buses['PG'] > 0].copy()
            
            if generating_buses.empty:
                return {'message': 'No generating buses found', 'base_case_id': base_case_id}
            
            dispatch_analysis = {
                'base_case_id': base_case_id,
                'total_generators': len(generating_buses),
                'generation_summary': {
                    'total_generation_mw': generating_buses['PG'].sum(),
                    'max_generation_mw': generating_buses['PG'].max(),
                    'min_generation_mw': generating_buses['PG'].min(),
                    'avg_generation_mw': generating_buses['PG'].mean(),
                    'generation_std': generating_buses['PG'].std()
                },
                'reactive_generation': {
                    'total_reactive_mvar': generating_buses['QG'].sum(),
                    'max_reactive_mvar': generating_buses['QG'].max(),
                    'min_reactive_mvar': generating_buses['QG'].min(),
                    'avg_reactive_mvar': generating_buses['QG'].mean()
                },
                'generator_details': generating_buses[['BUS_NUMBER', 'VM', 'PG', 'QG', 'BASE_KV']].to_dict('records'),
                'dispatch_metrics': {
                    'generation_diversity': generating_buses['PG'].std() / generating_buses['PG'].mean(),
                    'capacity_utilization': generating_buses['PG'].sum() / buses['PD'].sum() if buses['PD'].sum() > 0 else 0,
                    'largest_generator_share': generating_buses['PG'].max() / generating_buses['PG'].sum() * 100
                }
            }
            
            return dispatch_analysis
            
        except Exception as e:
            print(f"Error in generation dispatch analysis: {e}")
            return {'error': f'Generation analysis failed: {str(e)}'}
    
    def _get_generation_analysis_from_any_source(self):
        """Fallback method to get generation analysis from any available data source"""
        try:
            conn = self.get_connection()
            
            # Try different tables for generation data
            tables_to_try = ['BaseBusData', 'SLRBusData', 'DLRBusData', 'ContingencyBusData']
            
            for table in tables_to_try:
                try:
                    query = f"SELECT * FROM {table} WHERE PG > 0 LIMIT 100"
                    df = pd.read_sql_query(query, conn)
                    
                    if not df.empty:
                        print(f"📊 Using generation data from {table}")
                        
                        dispatch_summary = {
                            'data_source': table,
                            'total_generators': len(df),
                            'generation_summary': {
                                'total_generation_mw': df['PG'].sum(),
                                'max_generation_mw': df['PG'].max(),
                                'min_generation_mw': df['PG'].min(),
                                'avg_generation_mw': df['PG'].mean(),
                                'generation_std': df['PG'].std()
                            },
                            'reactive_generation': {
                                'total_reactive_mvar': df['QG'].sum() if 'QG' in df.columns else 0,
                                'max_reactive_mvar': df['QG'].max() if 'QG' in df.columns else 0,
                                'min_reactive_mvar': df['QG'].min() if 'QG' in df.columns else 0
                            },
                            'message': f'Generation analysis from {table} ({len(df)} generators found)'
                        }
                        
                        conn.close()
                        return dispatch_summary
                        
                except Exception:
                    continue
            
            conn.close()
            return {'error': 'No generation data found in any database table'}
            
        except Exception as e:
            print(f"Error in generation fallback analysis: {e}")
            return {'error': f'Generation fallback failed: {str(e)}'}

    def load_distribution_analysis(self, base_case_id=None):
        """
        Analyze load distribution across the system
        If base_case_id is None, automatically selects the best available case
        """
        try:
            # Auto-select base case if not specified
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return self._get_load_analysis_from_any_source()
            
            buses, _ = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                return self._get_load_analysis_from_any_source()
            
            # Filter load buses
            load_buses = buses[buses['PD'] > 0].copy()
            
            if load_buses.empty:
                return {'message': 'No load buses found', 'base_case_id': base_case_id}
            
            # Voltage level analysis if available
            voltage_level_analysis = {}
            if 'BASE_KV' in buses.columns:
                voltage_levels = buses['BASE_KV'].unique()
                for vl in voltage_levels:
                    vl_buses = buses[buses['BASE_KV'] == vl]
                    vl_load = vl_buses['PD'].sum()
                    voltage_level_analysis[f'{vl}_kV'] = {
                        'total_load_mw': vl_load,
                        'bus_count': len(vl_buses),
                        'avg_load_per_bus': vl_load / len(vl_buses) if len(vl_buses) > 0 else 0
                    }
            
            load_analysis = {
                'base_case_id': base_case_id,
                'total_load_buses': len(load_buses),
                'load_summary': {
                    'total_load_mw': load_buses['PD'].sum(),
                    'max_load_mw': load_buses['PD'].max(),
                    'min_load_mw': load_buses['PD'].min(),
                    'avg_load_mw': load_buses['PD'].mean(),
                    'load_std': load_buses['PD'].std()
                },
                'reactive_load': {
                    'total_reactive_mvar': load_buses['QD'].sum(),
                    'max_reactive_mvar': load_buses['QD'].max(),
                    'min_reactive_mvar': load_buses['QD'].min(),
                    'avg_reactive_mvar': load_buses['QD'].mean()
                },
                'voltage_level_distribution': voltage_level_analysis,
                'load_metrics': {
                    'load_diversity': load_buses['PD'].std() / load_buses['PD'].mean(),
                    'largest_load_share': load_buses['PD'].max() / load_buses['PD'].sum() * 100,
                    'load_concentration': len(load_buses[load_buses['PD'] > load_buses['PD'].quantile(0.8)]) / len(load_buses) * 100
                },
                'top_loads': load_buses.nlargest(5, 'PD')[['BUS_NUMBER', 'VM', 'PD', 'QD', 'BASE_KV']].to_dict('records') if 'BASE_KV' in load_buses.columns else load_buses.nlargest(5, 'PD')[['BUS_NUMBER', 'VM', 'PD', 'QD']].to_dict('records')
            }
            
            return load_analysis
            
        except Exception as e:
            print(f"Error in load distribution analysis: {e}")
            return {'error': f'Load analysis failed: {str(e)}'}
    
    def _get_load_analysis_from_any_source(self):
        """Fallback method to get load analysis from any available data source"""
        try:
            conn = self.get_connection()
            
            # Try different tables for load data
            tables_to_try = ['BaseBusData', 'SLRBusData', 'DLRBusData', 'ContingencyBusData']
            
            for table in tables_to_try:
                try:
                    query = f"SELECT * FROM {table} WHERE PD > 0 LIMIT 100"
                    df = pd.read_sql_query(query, conn)
                    
                    if not df.empty:
                        print(f"📊 Using load data from {table}")
                        
                        load_summary = {
                            'data_source': table,
                            'total_load_buses': len(df),
                            'load_summary': {
                                'total_load_mw': df['PD'].sum(),
                                'max_load_mw': df['PD'].max(),
                                'min_load_mw': df['PD'].min(),
                                'avg_load_mw': df['PD'].mean(),
                                'load_std': df['PD'].std()
                            },
                            'reactive_load': {
                                'total_reactive_mvar': df['QD'].sum() if 'QD' in df.columns else 0,
                                'max_reactive_mvar': df['QD'].max() if 'QD' in df.columns else 0,
                                'min_reactive_mvar': df['QD'].min() if 'QD' in df.columns else 0
                            },
                            'message': f'Load analysis from {table} ({len(df)} load buses found)'
                        }
                        
                        conn.close()
                        return load_summary
                        
                except Exception:
                    continue
            
            conn.close()
            return {'error': 'No load data found in any database table'}
            
        except Exception as e:
            print(f"Error in load fallback analysis: {e}")
            return {'error': f'Load fallback failed: {str(e)}'}

    def system_losses_analysis(self, base_case_id=None):
        """
        Analyze system losses and efficiency
        If base_case_id is None, automatically selects the best available case
        """
        try:
            # Auto-select base case if not specified
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return self._get_losses_analysis_from_any_source()
            
            buses, branches = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                return self._get_losses_analysis_from_any_source()
            
            total_generation = buses['PG'].sum()
            total_load = buses['PD'].sum()
            total_reactive_gen = buses['QG'].sum()
            total_reactive_load = buses['QD'].sum()
            
            # Calculate losses
            active_losses = total_generation - total_load
            reactive_losses = total_reactive_gen - total_reactive_load
            
            losses_analysis = {
                'base_case_id': base_case_id,
                'power_balance': {
                    'total_generation_mw': total_generation,
                    'total_load_mw': total_load,
                    'active_losses_mw': active_losses,
                    'loss_percentage': (active_losses / total_generation) * 100 if total_generation > 0 else 0
                },
                'reactive_balance': {
                    'total_reactive_generation_mvar': total_reactive_gen,
                    'total_reactive_load_mvar': total_reactive_load,
                    'reactive_losses_mvar': reactive_losses,
                    'reactive_loss_percentage': (reactive_losses / total_reactive_gen) * 100 if total_reactive_gen > 0 else 0
                },
                'efficiency_metrics': {
                    'system_efficiency': (total_load / total_generation) * 100 if total_generation > 0 else 0,
                    'generation_load_ratio': total_generation / total_load if total_load > 0 else 0,
                    'specific_losses': active_losses / total_load * 100 if total_load > 0 else 0
                }
            }
            
            return losses_analysis
            
        except Exception as e:
            print(f"Error in system losses analysis: {e}")
            return {'error': f'System losses analysis failed: {str(e)}'}
    
    def _get_losses_analysis_from_any_source(self):
        """Fallback method to get losses analysis from any available data source"""
        try:
            conn = self.get_connection()
            
            # Try different tables for power balance data
            tables_to_try = ['BaseBusData', 'SLRBusData', 'DLRBusData']
            
            for table in tables_to_try:
                try:
                    query = f"SELECT PG, PD, QG, QD FROM {table}"
                    df = pd.read_sql_query(query, conn)
                    
                    if not df.empty:
                        print(f"📊 Using losses data from {table}")
                        
                        total_generation = df['PG'].sum()
                        total_load = df['PD'].sum()
                        total_reactive_gen = df['QG'].sum() if 'QG' in df.columns else 0
                        total_reactive_load = df['QD'].sum() if 'QD' in df.columns else 0
                        
                        active_losses = total_generation - total_load
                        reactive_losses = total_reactive_gen - total_reactive_load
                        
                        losses_summary = {
                            'data_source': table,
                            'power_balance': {
                                'total_generation_mw': total_generation,
                                'total_load_mw': total_load,
                                'active_losses_mw': active_losses,
                                'loss_percentage': (active_losses / total_generation) * 100 if total_generation > 0 else 0
                            },
                            'efficiency_metrics': {
                                'system_efficiency': (total_load / total_generation) * 100 if total_generation > 0 else 0,
                                'generation_load_ratio': total_generation / total_load if total_load > 0 else 0
                            },
                            'message': f'Losses analysis from {table} (Generation: {total_generation:.1f} MW, Load: {total_load:.1f} MW)'
                        }
                        
                        conn.close()
                        return losses_summary
                        
                except Exception:
                    continue
            
            conn.close()
            return {'error': 'No power balance data found in any database table'}
            
        except Exception as e:
            print(f"Error in losses fallback analysis: {e}")
            return {'error': f'Losses fallback failed: {str(e)}'}

    def get_system_health_check(self, base_case_id=None):
        """
        Quick system health check combining key basic analyses
        If base_case_id is None, automatically selects the best available case
        """
        try:
            # Auto-select base case if not specified
            if base_case_id is None:
                base_case_id = self._get_best_available_base_case()
                if base_case_id is None:
                    return {'error': 'No base case data available for health check'}
            
            print(f"🏥 Performing System Health Check for Base Case {base_case_id}...")
            
            # Get key analyses
            summary = self.basic_system_summary(base_case_id)
            voltage_analysis = self.voltage_violation_analysis(base_case_id)
            flow_analysis = self.power_flow_analysis(base_case_id)
            losses = self.system_losses_analysis(base_case_id)
            
            # Calculate health scores
            voltage_score = 100
            if voltage_analysis and 'low_voltage_violations' in voltage_analysis:
                low_v_pct = voltage_analysis['low_voltage_violations'].get('percentage', 0)
                high_v_pct = voltage_analysis['high_voltage_violations'].get('percentage', 0)
                voltage_score = max(0, 100 - (low_v_pct + high_v_pct) * 2)
            
            loading_score = 100
            if flow_analysis and 'overloaded_branches' in flow_analysis:
                overload_pct = flow_analysis['overloaded_branches'].get('percentage', 0)
                heavy_load_pct = flow_analysis['heavily_loaded_branches'].get('percentage', 0)
                loading_score = max(0, 100 - overload_pct * 5 - heavy_load_pct * 2)
            
            efficiency_score = 100
            if losses and 'efficiency_metrics' in losses:
                system_eff = losses['efficiency_metrics'].get('system_efficiency', 100)
                if system_eff < 95:
                    efficiency_score = system_eff
            
            overall_health = (voltage_score + loading_score + efficiency_score) / 3
            
            health_check = {
                'base_case_id': base_case_id,
                'timestamp': pd.Timestamp.now().isoformat(),
                'overall_health_score': overall_health,
                'health_rating': 'Excellent' if overall_health >= 95 else 'Good' if overall_health >= 85 else 'Fair' if overall_health >= 70 else 'Poor',
                'component_scores': {
                    'voltage_health': voltage_score,
                    'loading_health': loading_score,
                    'efficiency_health': efficiency_score
                },
                'key_metrics': {
                    'total_buses': summary.get('total_buses', 0),
                    'total_branches': summary.get('total_branches', 0),
                    'voltage_violations': voltage_analysis.get('low_voltage_violations', {}).get('count', 0) + voltage_analysis.get('high_voltage_violations', {}).get('count', 0),
                    'overloaded_branches': flow_analysis.get('overloaded_branches', {}).get('count', 0),
                    'system_losses_pct': losses.get('power_balance', {}).get('loss_percentage', 0)
                },
                'recommendations': []
            }
            
            # Generate recommendations
            if voltage_score < 95:
                health_check['recommendations'].append("Address voltage violations - check reactive power support")
            if loading_score < 95:
                health_check['recommendations'].append("Review branch loading - consider system reinforcement")
            if efficiency_score < 95:
                health_check['recommendations'].append("Investigate system losses - optimize generation dispatch")
            if overall_health >= 95:
                health_check['recommendations'].append("System operating within normal parameters")
            
            print(f"✅ Health Check Complete - Overall Rating: {health_check['health_rating']} ({overall_health:.1f}/100)")
            
            return health_check
            
        except Exception as e:
            print(f"Error in system health check: {e}")
            return {"error": f"Health check failed: {str(e)}"}

    def basic_analysis_suite(self, base_case_id=None):
        """
        Run all basic analyses in one comprehensive function
        If base_case_id is None, automatically selects the best available case
        """
        # Auto-select base case if not specified
        if base_case_id is None:
            base_case_id = self._get_best_available_base_case()
            if base_case_id is None:
                return {'error': 'No base case data available for analysis suite'}
        
        print(f"🔍 Running Basic Analysis Suite for Base Case {base_case_id}...")
        
        analyses = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'base_case_id': base_case_id,
            'analyses': {}
        }
        
        basic_analyses = [
            ('system_summary', lambda: self.basic_system_summary(base_case_id)),
            ('voltage_violations', lambda: self.voltage_violation_analysis(base_case_id)),
            ('power_flow', lambda: self.power_flow_analysis(base_case_id)),
            ('contingency_impact', lambda: self.contingency_impact_analysis(base_case_id)),
            ('generation_dispatch', lambda: self.generation_dispatch_analysis(base_case_id)),
            ('load_distribution', lambda: self.load_distribution_analysis(base_case_id)),
            ('system_losses', lambda: self.system_losses_analysis(base_case_id))
        ]
        
        for analysis_name, analysis_func in basic_analyses:
            try:
                print(f"  📊 Running {analysis_name}...")
                analyses['analyses'][analysis_name] = analysis_func()
                print(f"  ✅ {analysis_name} completed")
            except Exception as e:
                print(f"  ❌ Error in {analysis_name}: {e}")
                analyses['analyses'][analysis_name] = {}
        
        print("🎉 Basic Analysis Suite completed!")
        return analyses
    
    def comprehensive_analysis_suite(self, base_case_id=None):
        """
        Run ALL comprehensive power system analyses including bus-level, branch-level, 
        system-level, comparative, and statistical analyses
        """
        # Auto-select base case if not specified
        if base_case_id is None:
            base_case_id = self._get_best_available_base_case()
            if base_case_id is None:
                return {'error': 'No base case data available for comprehensive analysis'}
        
        print(f"🔍 Running COMPREHENSIVE Analysis Suite for Base Case {base_case_id}...")
        
        analyses = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'base_case_id': base_case_id,
            'bus_level_analyses': {},
            'branch_level_analyses': {},
            'system_level_analyses': {},
            'comparative_analyses': {},
            'statistical_analyses': {}
        }
        
        # 🔹 BUS-LEVEL ANALYSES
        bus_analyses = [
            ('voltage_profile_analysis', lambda: self.voltage_profile_analysis(base_case_id)),
            ('load_analysis', lambda: self.load_analysis(base_case_id)),
            ('generation_analysis', lambda: self.generation_analysis(base_case_id)),
            ('voltage_violation_count', lambda: self.enhanced_voltage_violation_count(base_case_id))
        ]
        
        print("🔹 Bus-Level Analyses:")
        for analysis_name, analysis_func in bus_analyses:
            try:
                print(f"  📊 Running {analysis_name}...")
                analyses['bus_level_analyses'][analysis_name] = analysis_func()
                print(f"  ✅ {analysis_name} completed")
            except Exception as e:
                print(f"  ❌ Error in {analysis_name}: {e}")
                analyses['bus_level_analyses'][analysis_name] = {'error': str(e)}
        
        # 🔹 BRANCH-LEVEL ANALYSES  
        branch_analyses = [
            ('power_flow_analysis', lambda: self.power_flow_analysis(base_case_id)),
            ('line_loading_analysis', lambda: self.line_loading_analysis(base_case_id)),
            ('loss_analysis', lambda: self.loss_analysis(base_case_id)),
            ('branch_violation_detection', lambda: self.branch_violation_detection(base_case_id))
        ]
        
        print("🔹 Branch-Level Analyses:")
        for analysis_name, analysis_func in branch_analyses:
            try:
                print(f"  📊 Running {analysis_name}...")
                analyses['branch_level_analyses'][analysis_name] = analysis_func()
                print(f"  ✅ {analysis_name} completed")
            except Exception as e:
                print(f"  ❌ Error in {analysis_name}: {e}")
                analyses['branch_level_analyses'][analysis_name] = {'error': str(e)}
        
        # 🔹 SYSTEM-LEVEL ANALYSES
        system_analyses = [
            ('power_balance_analysis', lambda: self.power_balance_analysis(base_case_id)),
            ('system_losses_analysis', lambda: self.system_losses_analysis(base_case_id)),
            ('system_reliability_indices', lambda: self.system_reliability_indices(base_case_id)),
            ('n_minus_1_analysis', lambda: self.n_minus_1_analysis(base_case_id)),
            ('contingency_impact_analysis', lambda: self.contingency_impact_analysis(base_case_id))
        ]
        
        print("🔹 System-Level Analyses:")
        for analysis_name, analysis_func in system_analyses:
            try:
                print(f"  📊 Running {analysis_name}...")
                analyses['system_level_analyses'][analysis_name] = analysis_func()
                print(f"  ✅ {analysis_name} completed")
            except Exception as e:
                print(f"  ❌ Error in {analysis_name}: {e}")
                analyses['system_level_analyses'][analysis_name] = {'error': str(e)}
        
        # 🔹 COMPARATIVE ANALYSES
        comparative_analyses = [
            ('dlr_benefits_analysis', lambda: self.dlr_benefits_analysis(base_case_id)),
            ('stress_points_analysis', lambda: self.stress_points_analysis(base_case_id))
        ]
        
        print("🔹 Comparative Analyses:")
        for analysis_name, analysis_func in comparative_analyses:
            try:
                print(f"  📊 Running {analysis_name}...")
                analyses['comparative_analyses'][analysis_name] = analysis_func()
                print(f"  ✅ {analysis_name} completed")
            except Exception as e:
                print(f"  ❌ Error in {analysis_name}: {e}")
                analyses['comparative_analyses'][analysis_name] = {'error': str(e)}
        
        # 🔹 STATISTICAL ANALYSES
        statistical_analyses = [
            ('correlation_analysis', lambda: self.correlation_analysis(base_case_id)),
            ('distribution_analysis', lambda: self.distribution_analysis(base_case_id)),
            ('outlier_detection', lambda: self.outlier_detection(base_case_id))
        ]
        
        print("🔹 Statistical Analyses:")
        for analysis_name, analysis_func in statistical_analyses:
            try:
                print(f"  📊 Running {analysis_name}...")
                analyses['statistical_analyses'][analysis_name] = analysis_func()
                print(f"  ✅ {analysis_name} completed")
            except Exception as e:
                print(f"  ❌ Error in {analysis_name}: {e}")
                analyses['statistical_analyses'][analysis_name] = {'error': str(e)}
        
        # Generate comprehensive summary
        analyses['comprehensive_summary'] = self._generate_comprehensive_summary(analyses)
        
        print("🎉 COMPREHENSIVE Analysis Suite completed!")
        return analyses
    
    def _generate_comprehensive_summary(self, analyses):
        """Generate a high-level summary of all analyses"""
        try:
            summary = {
                'total_analyses_run': 0,
                'successful_analyses': 0,
                'failed_analyses': 0,
                'key_findings': [],
                'critical_issues': [],
                'system_health_overview': {}
            }
            
            # Count analyses
            for category in ['bus_level_analyses', 'branch_level_analyses', 'system_level_analyses', 'comparative_analyses', 'statistical_analyses']:
                if category in analyses:
                    for analysis_name, result in analyses[category].items():
                        summary['total_analyses_run'] += 1
                        if 'error' in result:
                            summary['failed_analyses'] += 1
                        else:
                            summary['successful_analyses'] += 1
            
            # Extract key findings
            try:
                # Voltage issues
                voltage_analysis = analyses.get('bus_level_analyses', {}).get('voltage_profile_analysis', {})
                if 'under_voltage_violations' in voltage_analysis:
                    violation_count = voltage_analysis['under_voltage_violations']['count'] + voltage_analysis['over_voltage_violations']['count']
                    if violation_count > 0:
                        summary['critical_issues'].append(f"{violation_count} voltage violations detected")
                
                # Loading issues
                loading_analysis = analyses.get('branch_level_analyses', {}).get('line_loading_analysis', {})
                if 'overloaded_branches' in loading_analysis:
                    overload_count = loading_analysis['overloaded_branches']['count']
                    if overload_count > 0:
                        summary['critical_issues'].append(f"{overload_count} overloaded branches detected")
                
                # System health
                reliability_analysis = analyses.get('system_level_analyses', {}).get('system_reliability_indices', {})
                if 'reliability_indices' in reliability_analysis:
                    health_score = reliability_analysis['reliability_indices']['system_health_score']
                    summary['system_health_overview']['health_score'] = health_score
                    summary['system_health_overview']['assessment'] = reliability_analysis['reliability_assessment']
                
            except Exception as e:
                summary['key_findings'].append(f"Summary generation error: {str(e)}")
            
            return summary
            
        except Exception as e:
            return {'error': f'Could not generate comprehensive summary: {str(e)}'}
    
    def get_all_base_case_ids(self):
        """Get all available base case IDs from the database"""
        if self._all_base_case_ids is None:
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT base_case_id FROM BaseBusData ORDER BY base_case_id")
                self._all_base_case_ids = [row[0] for row in cursor.fetchall()]
                conn.close()
                print(f"✅ Found {len(self._all_base_case_ids)} base cases in database")
            except Exception as e:
                print(f"❌ Error getting base case IDs: {e}")
                self._all_base_case_ids = []
        return self._all_base_case_ids
    
    def load_base_case_data(self, base_case_id=42):
        """Load base case bus and branch data with flexible column handling"""
        try:
            conn = self.get_connection()
            
            # Check available columns first
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(BaseBusData)")
            bus_columns = [col[1] for col in cursor.fetchall()]
            
            # Build flexible bus query based on available columns
            required_bus_cols = ['BUS_NUMBER', 'VM', 'PG', 'PD']
            optional_bus_cols = ['VA', 'QG', 'QD', 'BASE_KV']
            
            select_bus_cols = []
            for col in required_bus_cols:
                if col in bus_columns:
                    select_bus_cols.append(col)
            
            for col in optional_bus_cols:
                if col in bus_columns:
                    select_bus_cols.append(col)
                else:
                    select_bus_cols.append(f"0 as {col}")  # Default value for missing columns
            
            bus_query = f"""
            SELECT {', '.join(select_bus_cols)}
            FROM BaseBusData 
            WHERE base_case_id = {base_case_id}
            """
            buses_df = pd.read_sql_query(bus_query, conn)
            
            # Check branch table columns
            cursor.execute("PRAGMA table_info(BaseBranchData)")
            branch_columns = [col[1] for col in cursor.fetchall()]
            
            # Build flexible branch query
            required_branch_cols = ['FROM_BUS', 'TO_BUS']
            optional_branch_cols = ['PF', 'QF', 'RATE', 'VIO']
            
            select_branch_cols = []
            for col in required_branch_cols:
                if col in branch_columns:
                    select_branch_cols.append(col)
            
            for col in optional_branch_cols:
                if col in branch_columns:
                    select_branch_cols.append(col)
                else:
                    select_branch_cols.append(f"0 as {col}")  # Default value
            
            branch_query = f"""
            SELECT {', '.join(select_branch_cols)}
            FROM BaseBranchData 
            WHERE base_case_id = {base_case_id}
            """
            branches_df = pd.read_sql_query(branch_query, conn)
            
            conn.close()
            return buses_df, branches_df
            
        except Exception as e:
            print(f"Error loading base case data: {e}")
            return pd.DataFrame(), pd.DataFrame()
            return pd.DataFrame(), pd.DataFrame()
    
    def load_contingency_data(self, contingency_case_id=1, base_case_id=42):
        """Load contingency case data"""
        try:
            conn = self.get_connection()
            
            # Load contingency bus data
            bus_query = f"""
            SELECT BUS_NUMBER, VM, VA, PG, QG, PD, QD
            FROM ContingencyBusData 
            WHERE contingency_case_id = {contingency_case_id} AND base_case_id = {base_case_id}
            """
            buses_df = pd.read_sql_query(bus_query, conn)
            
            # Load contingency branch data  
            branch_query = f"""
            SELECT FROM_BUS, TO_BUS, PF, QF, RATE, VIO
            FROM ContingencyBranchData 
            WHERE contingency_case_id = {contingency_case_id} AND base_case_id = {base_case_id}
            """
            branches_df = pd.read_sql_query(branch_query, conn)
            
            conn.close()
            return buses_df, branches_df
            
        except Exception as e:
            print(f"Error loading contingency data: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def perform_correlation_analysis(self, base_case_ids=None):
        """Wrapper for correlation analysis with enhanced results formatting"""
        results = self.correlation_analysis(base_case_ids)
        
        if results:
            # Add summary metrics for chat interface
            correlation_matrix = results.get('correlation_matrix', {})
            strong_correlations = results.get('strong_correlations', [])
            
            summary = {
                'analysis_type': 'correlation',
                'num_variables': len(correlation_matrix) if correlation_matrix else 0,
                'strong_correlations_found': len(strong_correlations),
                'max_correlation': max([abs(c['correlation']) for c in strong_correlations]) if strong_correlations else 0,
                'min_correlation': min([abs(c['correlation']) for c in strong_correlations]) if strong_correlations else 0,
                'key_findings': []
            }
            
            # Generate key findings
            if strong_correlations:
                summary['key_findings'].append(f"Found {len(strong_correlations)} strong correlations (>0.7)")
                strongest = max(strong_correlations, key=lambda x: abs(x['correlation']))
                summary['key_findings'].append(f"Strongest correlation: {strongest['var1']} vs {strongest['var2']} ({strongest['correlation']:.3f})")
            
            results['summary'] = summary
            
        return results
    
    def perform_monte_carlo_analysis(self, base_case_id=42, n_simulations=1000):
        """Wrapper for Monte Carlo analysis with enhanced results formatting"""
        results = self.monte_carlo_risk_assessment(base_case_id, n_simulations)
        
        if results:
            risk_stats = results.get('risk_statistics', {})
            
            summary = {
                'analysis_type': 'monte_carlo',
                'num_simulations': n_simulations,
                'risk_level': 'Low' if risk_stats.get('high_risk_probability', 0) < 0.1 else 'Medium' if risk_stats.get('high_risk_probability', 0) < 0.3 else 'High',
                'confidence_interval': '95%',
                'insights': []
            }
            
            # Generate insights
            if 'high_risk_probability' in risk_stats:
                prob = risk_stats['high_risk_probability']
                summary['insights'].append(f"High risk probability: {prob:.1%}")
                
            if 'avg_voltage_violations' in risk_stats:
                violations = risk_stats['avg_voltage_violations']
                summary['insights'].append(f"Average voltage violations per simulation: {violations:.1f}")
                
            if 'load_volatility' in risk_stats:
                volatility = risk_stats['load_volatility']
                summary['insights'].append(f"Load volatility coefficient: {volatility:.3f}")
            
            results['summary'] = summary
            
        return results
    
    def perform_sensitivity_analysis(self, base_case_id=42, perturbation_percent=5):
        """Wrapper for sensitivity analysis with enhanced results formatting"""
        results = self.sensitivity_analysis(base_case_id, perturbation_percent)
        
        if results:
            sensitivity_results = results.get('sensitivity_results', {})
            
            # Find most sensitive parameter
            max_sensitivity = 0
            most_sensitive = None
            
            for param, sensitivities in sensitivity_results.items():
                for metric, sensitivity in sensitivities.items():
                    if abs(sensitivity) > abs(max_sensitivity):
                        max_sensitivity = sensitivity
                        most_sensitive = f"{param} -> {metric}"
            
            summary = {
                'analysis_type': 'sensitivity',
                'num_parameters': len(sensitivity_results),
                'most_sensitive': most_sensitive,
                'sensitivity_range': f"±{perturbation_percent}%",
                'insights': []
            }
            
            # Generate insights
            if most_sensitive:
                summary['insights'].append(f"Most sensitive parameter: {most_sensitive}")
                summary['insights'].append(f"Maximum sensitivity coefficient: {max_sensitivity:.3f}")
            
            for param in sensitivity_results:
                param_name = 'Load' if param == 'PD' else 'Generation' if param == 'PG' else param
                summary['insights'].append(f"{param_name} parameter analyzed with {perturbation_percent}% perturbation")
            
            results['summary'] = summary
            
        return results
    
    def perform_clustering_analysis(self, base_case_ids=None, n_clusters=5):
        """Wrapper for clustering analysis with enhanced results formatting"""
        results = self.clustering_analysis(base_case_ids, n_clusters)
        
        if results:
            summary = {
                'analysis_type': 'clustering',
                'optimal_clusters': results.get('optimal_clusters', n_clusters),
                'silhouette_score': results.get('silhouette_score', 0),
                'algorithm': 'K-means',
                'characteristics': []
            }
            
            # Generate cluster characteristics
            silhouette = results.get('silhouette_score', 0)
            if silhouette > 0.5:
                summary['characteristics'].append(f"Excellent cluster separation (silhouette score: {silhouette:.3f})")
            elif silhouette > 0.3:
                summary['characteristics'].append(f"Good cluster separation (silhouette score: {silhouette:.3f})")
            else:
                summary['characteristics'].append(f"Moderate cluster separation (silhouette score: {silhouette:.3f})")
            
            optimal_k = results.get('optimal_clusters', n_clusters)
            if optimal_k != n_clusters:
                summary['characteristics'].append(f"Recommended {optimal_k} clusters instead of {n_clusters}")
            
            cluster_results = results.get('cluster_results', [])
            if cluster_results:
                summary['characteristics'].append(f"Analyzed {len(cluster_results)} operating conditions")
            
            results['summary'] = summary
            
        return results
    
    def perform_reliability_analysis(self, base_case_ids=None):
        """Wrapper for reliability analysis with enhanced results formatting"""
        results = self.reliability_statistics(base_case_ids)
        
        if results:
            overall_metrics = results.get('overall_metrics', {})
            
            summary = {
                'analysis_type': 'reliability',
                'availability': overall_metrics.get('avg_reliability_index', 0),
                'mtbf': 'N/A',  # Would need historical data
                'mttr': 'N/A',  # Would need historical data
                'insights': []
            }
            
            # Generate insights
            if 'avg_reliability_index' in overall_metrics:
                reliability = overall_metrics['avg_reliability_index']
                summary['insights'].append(f"Average system reliability index: {reliability:.3f}")
                
                if reliability > 0.95:
                    summary['insights'].append("Excellent system reliability (>95%)")
                elif reliability > 0.90:
                    summary['insights'].append("Good system reliability (90-95%)")
                else:
                    summary['insights'].append("System reliability needs improvement (<90%)")
            
            if 'system_violation_rate' in overall_metrics:
                violation_rate = overall_metrics['system_violation_rate']
                summary['insights'].append(f"Average violation rate: {violation_rate:.1%}")
            
            if 'total_base_cases' in overall_metrics:
                cases = overall_metrics['total_base_cases']
                summary['insights'].append(f"Analyzed {cases} base case scenarios")
            
            results['summary'] = summary
            
        return results
    
    def perform_economic_analysis(self, base_case_ids=None):
        """Wrapper for economic analysis with enhanced results formatting"""
        if base_case_ids is None:
            base_case_ids = [42, 43, 44, 45, 46]
            
        results = self.economic_analysis(base_case_ids)
        
        if results:
            avg_metrics = results.get('average_metrics', {})
            efficiency_range = results.get('efficiency_range', {})
            
            summary = {
                'analysis_type': 'economic',
                'avg_cost': avg_metrics.get('total_cost_usd', 0),
                'efficiency': efficiency_range.get('avg', 0),
                'cost_range': f"${avg_metrics.get('total_cost_usd', 0) - results.get('cost_variance', 0):.0f} - ${avg_metrics.get('total_cost_usd', 0) + results.get('cost_variance', 0):.0f}",
                'insights': []
            }
            
            # Generate insights
            if 'total_cost_usd' in avg_metrics:
                cost = avg_metrics['total_cost_usd']
                summary['insights'].append(f"Average operating cost: ${cost:,.0f}")
            
            if efficiency_range:
                eff_avg = efficiency_range.get('avg', 0)
                eff_range = efficiency_range.get('max', 0) - efficiency_range.get('min', 0)
                summary['insights'].append(f"Generation efficiency: {eff_avg:.1%} (±{eff_range:.1%})")
            
            best_case = results.get('best_case_scenario', {})
            if best_case:
                summary['insights'].append(f"Most economical case: {best_case.get('case_id', 'N/A')}")
            
            results['summary'] = summary
            
        return results
    
    def perform_power_quality_analysis(self, base_case_ids=None):
        """Wrapper for power quality analysis with enhanced results formatting"""
        if base_case_ids is None:
            base_case_ids = [42, 43, 44, 45, 46]
            
        results = self.power_quality_analysis(base_case_ids)
        
        if results:
            overall_assessment = results.get('overall_assessment', {})
            violation_summary = results.get('violation_summary', {})
            
            summary = {
                'analysis_type': 'power_quality',
                'quality_index': overall_assessment.get('system_voltage_quality', 0),
                'total_violations': violation_summary.get('total_violations', 0),
                'voltage_stability': overall_assessment.get('avg_voltage_stability', 0),
                'insights': []
            }
            
            # Generate insights
            quality_index = overall_assessment.get('system_voltage_quality', 0)
            if quality_index > 0.95:
                summary['insights'].append(f"Excellent power quality (index: {quality_index:.3f})")
            elif quality_index > 0.90:
                summary['insights'].append(f"Good power quality (index: {quality_index:.3f})")
            else:
                summary['insights'].append(f"Power quality needs improvement (index: {quality_index:.3f})")
            
            total_violations = violation_summary.get('total_violations', 0)
            if total_violations > 0:
                summary['insights'].append(f"Total voltage violations detected: {total_violations}")
                low_v = violation_summary.get('low_voltage', 0)
                high_v = violation_summary.get('high_voltage', 0)
                summary['insights'].append(f"Low voltage: {low_v}, High voltage: {high_v}")
            else:
                summary['insights'].append("No voltage violations detected")
            
            results['summary'] = summary
            
        return results
        """
        Analyze correlations between electrical parameters across all base cases
        """
        try:
            # Use all base cases if none specified
            if base_case_ids is None:
                base_case_ids = self.get_all_base_case_ids()
            
            print(f"🔄 Starting correlation analysis for {len(base_case_ids)} base cases...")
            
            all_data = []
            processed = 0
            
            # Process in batches for memory efficiency
            for i in range(0, len(base_case_ids), batch_size):
                batch = base_case_ids[i:i+batch_size]
                print(f"📊 Processing batch {i//batch_size + 1}/{(len(base_case_ids)-1)//batch_size + 1} (cases {batch[0]}-{batch[-1]})")
                
                for case_id in batch:
                    buses, branches = self.load_base_case_data(case_id)
                    
                    if not buses.empty:
                        # Bus-level correlations
                        bus_analysis = {
                            'case_id': case_id,
                            'avg_voltage': buses['VM'].mean(),
                            'voltage_std': buses['VM'].std(),
                            'total_generation': buses['PG'].sum(),
                            'total_load': buses['PD'].sum(),
                            'reactive_generation': buses['QG'].sum(),
                            'reactive_load': buses['QD'].sum(),
                            'gen_load_ratio': buses['PG'].sum() / buses['PD'].sum() if buses['PD'].sum() > 0 else 0,
                            'voltage_range': buses['VM'].max() - buses['VM'].min(),
                            'load_diversity': buses['PD'].std() / buses['PD'].mean() if buses['PD'].mean() > 0 else 0
                        }
                        all_data.append(bus_analysis)
                        processed += 1
                        
                        # Progress update every 50 cases
                        if processed % 50 == 0:
                            print(f"  ✅ Processed {processed}/{len(base_case_ids)} cases...")
            
            if not all_data:
                return {}
            
            print(f"🎯 Successfully processed {processed} base cases")
            analysis_df = pd.DataFrame(all_data)
            
            # Calculate correlation matrix
            correlation_matrix = analysis_df.select_dtypes(include=[np.number]).corr()
            
            # Identify strong correlations
            strong_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_val = correlation_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:  # Strong correlation threshold
                        strong_correlations.append({
                            'var1': correlation_matrix.columns[i],
                            'var2': correlation_matrix.columns[j],
                            'correlation': corr_val
                        })
            
            # PCA Analysis
            numeric_data = analysis_df.select_dtypes(include=[np.number])
            if len(numeric_data.columns) > 1:
                scaled_data = self.scaler.fit_transform(numeric_data)
                pca = PCA(n_components=min(3, len(numeric_data.columns)))
                pca_result = pca.fit_transform(scaled_data)
                
                pca_analysis = {
                    'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
                    'components': pca.components_.tolist(),
                    'feature_names': numeric_data.columns.tolist()
                }
            else:
                pca_analysis = {}
            
            return {
                'correlation_matrix': correlation_matrix.to_dict(),
                'strong_correlations': strong_correlations,
                'pca_analysis': pca_analysis,
                'summary_stats': analysis_df.describe().to_dict()
            }
            
        except Exception as e:
            print(f"Error in correlation analysis: {e}")
            return {}
    
    def monte_carlo_risk_assessment(self, base_case_id=42, n_simulations=1000, analyze_all_cases=False):
        """
        Monte Carlo simulation for risk assessment
        Can analyze single base case or multiple cases if analyze_all_cases=True
        """
        try:
            if analyze_all_cases:
                print(f"🔄 Starting Monte Carlo analysis for all base cases...")
                all_base_cases = self.get_all_base_case_ids()
                
                # For all cases analysis, use fewer simulations per case to manage time
                simulations_per_case = max(100, n_simulations // len(all_base_cases))
                all_results = []
                
                for i, case_id in enumerate(all_base_cases[:50]):  # Limit to first 50 cases for demo
                    if i % 10 == 0:
                        print(f"  📊 Monte Carlo progress: {i}/{min(50, len(all_base_cases))} cases...")
                    
                    case_result = self._monte_carlo_single_case(case_id, simulations_per_case)
                    if case_result:
                        case_result['base_case_id'] = case_id
                        all_results.append(case_result)
                
                return {
                    'analysis_type': 'multi_case',
                    'total_cases_analyzed': len(all_results),
                    'simulations_per_case': simulations_per_case,
                    'case_results': all_results,
                    'summary_stats': self._summarize_monte_carlo_results(all_results)
                }
            else:
                return self._monte_carlo_single_case(base_case_id, n_simulations)
                
        except Exception as e:
            print(f"Error in Monte Carlo analysis: {e}")
            return {}
    
    def _monte_carlo_single_case(self, base_case_id, n_simulations):
        """Helper method for single case Monte Carlo analysis"""
        try:
            buses, branches = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                return {}
            
            # Base statistics
            base_loads = buses['PD'].values
            base_generation = buses['PG'].values
            base_voltages = buses['VM'].values
            
            simulation_results = []
            
            for _ in range(n_simulations):
                # Random load variations (±20%)
                load_multipliers = np.random.normal(1.0, 0.1, len(base_loads))
                simulated_loads = base_loads * load_multipliers
                
                # Random generation variations (±15%)
                gen_multipliers = np.random.normal(1.0, 0.075, len(base_generation))
                simulated_generation = base_generation * gen_multipliers
                
                # Voltage impact estimation (simplified)
                load_impact = (simulated_loads - base_loads) / base_loads
                voltage_change = -0.02 * load_impact  # Simplified voltage drop
                simulated_voltages = base_voltages + voltage_change
                
                # Risk metrics
                voltage_violations = np.sum((simulated_voltages < 0.95) | (simulated_voltages > 1.05))
                overload_risk = np.sum(simulated_loads > 1.2 * base_loads)
                total_load = np.sum(simulated_loads)
                total_generation = np.sum(simulated_generation)
                generation_deficit = max(0, total_load - total_generation)
                
                simulation_results.append({
                    'voltage_violations': voltage_violations,
                    'overload_risk': overload_risk,
                    'generation_deficit': generation_deficit,
                    'min_voltage': np.min(simulated_voltages),
                    'max_voltage': np.max(simulated_voltages),
                    'total_load': total_load,
                    'total_generation': total_generation
                })
            
            results_df = pd.DataFrame(simulation_results)
            
            # Risk statistics
            risk_statistics = {
                'high_risk_probability': len(results_df[results_df['voltage_violations'] > 0]) / n_simulations,
                'avg_voltage_violations': results_df['voltage_violations'].mean(),
                'avg_overload_risk': results_df['overload_risk'].mean(),
                'generation_deficit_probability': len(results_df[results_df['generation_deficit'] > 0]) / n_simulations,
                'load_volatility': results_df['total_load'].std() / results_df['total_load'].mean(),
                'generation_volatility': results_df['total_generation'].std() / results_df['total_generation'].mean()
            }
            
            return {
                'simulation_results': results_df.to_dict('records'),
                'risk_statistics': risk_statistics,
                'summary_stats': results_df.describe().to_dict(),
                'percentiles': {
                    '5th': results_df.quantile(0.05).to_dict(),
                    '95th': results_df.quantile(0.95).to_dict()
                }
            }
            
        except Exception as e:
            print(f"Error in Monte Carlo analysis: {e}")
            return {}
    
    def _summarize_monte_carlo_results(self, all_results):
        """Helper method to summarize Monte Carlo results across multiple cases"""
        if not all_results:
            return {}
        
        # Extract key metrics from all cases
        risk_probs = [r['risk_statistics']['high_risk_probability'] for r in all_results]
        voltage_violations = [r['risk_statistics']['avg_voltage_violations'] for r in all_results]
        load_volatilities = [r['risk_statistics']['load_volatility'] for r in all_results]
        
        return {
            'overall_risk_probability': np.mean(risk_probs),
            'max_risk_case': all_results[np.argmax(risk_probs)]['base_case_id'],
            'avg_voltage_violations': np.mean(voltage_violations),
            'system_load_volatility': np.mean(load_volatilities),
            'risk_distribution': {
                'low_risk_cases': sum(1 for p in risk_probs if p < 0.1),
                'medium_risk_cases': sum(1 for p in risk_probs if 0.1 <= p < 0.3),
                'high_risk_cases': sum(1 for p in risk_probs if p >= 0.3)
            }
        }

    def sensitivity_analysis(self, base_case_id=42, perturbation_percent=5):
        """
        Sensitivity analysis of system parameters
        """
        try:
            buses, branches = self.load_base_case_data(base_case_id)
            
            if buses.empty:
                return {}
            
            base_metrics = {
                'total_load': buses['PD'].sum(),
                'total_generation': buses['PG'].sum(),
                'avg_voltage': buses['VM'].mean(),
                'voltage_std': buses['VM'].std(),
                'max_generation': buses['PG'].max(),
                'max_load': buses['PD'].max()
            }
            
            sensitivity_results = {}
            perturbation = perturbation_percent / 100.0
            
            # Load sensitivity
            for param in ['PD', 'PG']:
                if param in buses.columns:
                    original_values = buses[param].copy()
                    
                    # Increase parameter
                    buses_plus = buses.copy()
                    buses_plus[param] = original_values * (1 + perturbation)
                    
                    # Decrease parameter
                    buses_minus = buses.copy()
                    buses_minus[param] = original_values * (1 - perturbation)
                    
                    # Calculate sensitivities
                    metrics_plus = {
                        'total_load': buses_plus['PD'].sum(),
                        'total_generation': buses_plus['PG'].sum(),
                        'avg_voltage': buses_plus['VM'].mean(),
                        'voltage_std': buses_plus['VM'].std()
                    }
                    
                    metrics_minus = {
                        'total_load': buses_minus['PD'].sum(),
                        'total_generation': buses_minus['PG'].sum(),
                        'avg_voltage': buses_minus['VM'].mean(),
                        'voltage_std': buses_minus['VM'].std()
                    }
                    
                    # Calculate sensitivity coefficients
                    param_sensitivity = {}
                    for metric in metrics_plus:
                        if base_metrics[metric] != 0:
                            sensitivity = ((metrics_plus[metric] - metrics_minus[metric]) / 
                                         (2 * perturbation * base_metrics[metric]))
                            param_sensitivity[metric] = sensitivity
                    
                    sensitivity_results[param] = param_sensitivity
            
            return {
                'sensitivity_results': sensitivity_results,
                'base_metrics': base_metrics,
                'perturbation_percent': perturbation_percent
            }
            
        except Exception as e:
            print(f"Error in sensitivity analysis: {e}")
            return {}
    
    def clustering_analysis(self, base_case_ids=None, n_clusters=5, batch_size=100):
        """
        Cluster operating conditions based on electrical parameters across all base cases
        """
        try:
            # Use all base cases if none specified
            if base_case_ids is None:
                base_case_ids = self.get_all_base_case_ids()
            
            print(f"🔄 Starting clustering analysis for {len(base_case_ids)} base cases...")
            
            all_features = []
            case_labels = []
            processed = 0
            
            # Process in batches for memory efficiency
            for i in range(0, len(base_case_ids), batch_size):
                batch = base_case_ids[i:i+batch_size]
                print(f"📊 Processing clustering batch {i//batch_size + 1}/{(len(base_case_ids)-1)//batch_size + 1}")
                
                for case_id in batch:
                    buses, branches = self.load_base_case_data(case_id)
                    
                    if not buses.empty:
                        # Extract comprehensive features for clustering
                        features = {
                            'avg_voltage': buses['VM'].mean(),
                            'voltage_std': buses['VM'].std(),
                            'total_load': buses['PD'].sum(),
                            'total_generation': buses['PG'].sum(),
                            'reactive_load': buses['QD'].sum(),
                            'reactive_generation': buses['QG'].sum(),
                            'load_balance': buses['PG'].sum() - buses['PD'].sum(),
                            'max_voltage': buses['VM'].max(),
                            'min_voltage': buses['VM'].min(),
                            'voltage_range': buses['VM'].max() - buses['VM'].min(),
                            'load_diversity': buses['PD'].std() / buses['PD'].mean() if buses['PD'].mean() > 0 else 0,
                            'gen_diversity': buses['PG'].std() / buses['PG'].mean() if buses['PG'].mean() > 0 else 0
                        }
                        
                        all_features.append(list(features.values()))
                        case_labels.append(case_id)
                        processed += 1
                        
                        # Progress update every 100 cases
                        if processed % 100 == 0:
                            print(f"  ✅ Processed {processed}/{len(base_case_ids)} cases for clustering...")
            
            if len(all_features) < n_clusters:
                print(f"❌ Not enough data for {n_clusters} clusters. Found {len(all_features)} cases.")
                return {}
            
            print(f"🎯 Successfully processed {processed} cases for clustering")
            
            features_df = pd.DataFrame(all_features, columns=[
                'avg_voltage', 'voltage_std', 'total_load', 'total_generation',
                'reactive_load', 'reactive_generation', 'load_balance',
                'max_voltage', 'min_voltage', 'voltage_range', 'load_diversity', 'gen_diversity'
            ])
            
            # Standardize features
            features_scaled = self.scaler.fit_transform(features_df)
            
            # K-means clustering
            print(f"🧮 Performing K-means clustering with {n_clusters} clusters...")
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            # Calculate silhouette score
            silhouette_avg = silhouette_score(features_scaled, cluster_labels)
            
            # Find optimal number of clusters (test up to 10 or data size limit)
            print("🔍 Finding optimal number of clusters...")
            silhouette_scores = []
            max_clusters = min(10, len(all_features) // 2)
            for k in range(2, max_clusters + 1):
                kmeans_test = KMeans(n_clusters=k, random_state=42, n_init=5)
                labels_test = kmeans_test.fit_predict(features_scaled)
                score = silhouette_score(features_scaled, labels_test)
                silhouette_scores.append({'k': k, 'score': score})
            
            optimal_k = max(silhouette_scores, key=lambda x: x['score'])['k'] if silhouette_scores else n_clusters
            
            # PCA for visualization
            pca = PCA(n_components=2)
            features_2d = pca.fit_transform(features_scaled)
            
            cluster_results = []
            for i, case_id in enumerate(case_labels):
                cluster_results.append({
                    'case_id': case_id,
                    'cluster': int(cluster_labels[i]),
                    'pca_x': features_2d[i, 0],
                    'pca_y': features_2d[i, 1],
                    **dict(zip(features_df.columns, all_features[i]))
                })
            
            return {
                'cluster_results': cluster_results,
                'silhouette_score': silhouette_avg,
                'optimal_clusters': optimal_k,
                'cluster_centers': kmeans.cluster_centers_.tolist(),
                'feature_names': features_df.columns.tolist(),
                'pca_explained_variance': pca.explained_variance_ratio_.tolist()
            }
            
        except Exception as e:
            print(f"Error in clustering analysis: {e}")
            return {}
    
    def reliability_statistics(self, base_case_ids=None, batch_size=50):
        """
        Calculate reliability statistics based on contingency analysis for all base cases
        """
        try:
            # Use all base cases if none specified
            if base_case_ids is None:
                base_case_ids = self.get_all_base_case_ids()
            
            print(f"🔄 Starting reliability analysis for {len(base_case_ids)} base cases...")
            
            reliability_data = []
            processed = 0
            total_contingencies = 0
            
            # Process in batches for memory efficiency
            for i in range(0, len(base_case_ids), batch_size):
                batch = base_case_ids[i:i+batch_size]
                print(f"📊 Processing reliability batch {i//batch_size + 1}/{(len(base_case_ids)-1)//batch_size + 1}")
                
                for base_case_id in batch:
                    base_buses, base_branches = self.load_base_case_data(base_case_id)
                    
                    if not base_branches.empty:
                        case_violations = []
                        case_contingencies = 0
                        
                        # Check multiple contingency scenarios for each base case
                        for contingency_id in range(1, 11):  # Check up to 10 contingencies per base case
                            buses, branches = self.load_contingency_data(contingency_id, base_case_id)
                            
                            if not branches.empty:
                                case_contingencies += 1
                                total_contingencies += 1
                                
                                # Calculate violations
                                violations = 0
                                if 'VIO' in branches.columns:
                                    violations = branches['VIO'].sum()
                                elif 'PF' in branches.columns and 'RATE' in branches.columns:
                                    # Calculate thermal violations
                                    apparent_flow = np.sqrt(branches['PF']**2 + branches['QF']**2)
                                    violations = (apparent_flow > branches['RATE']).sum()
                                
                                case_violations.append(violations)
                        
                        # Calculate reliability metrics for this base case
                        if case_violations:
                            reliability_metrics = {
                                'base_case_id': base_case_id,
                                'total_contingencies': case_contingencies,
                                'avg_violations': np.mean(case_violations),
                                'max_violations': np.max(case_violations),
                                'violation_rate': sum(1 for v in case_violations if v > 0) / len(case_violations),
                                'reliability_index': 1 - (sum(case_violations) / (len(case_violations) * len(base_branches))),
                                'violation_severity': np.std(case_violations),
                                'total_violations': sum(case_violations)
                            }
                            reliability_data.append(reliability_metrics)
                        
                        processed += 1
                        
                        # Progress update every 25 cases
                        if processed % 25 == 0:
                            print(f"  ✅ Processed {processed}/{len(base_case_ids)} base cases...")
            
            if not reliability_data:
                return {}
            
            print(f"🎯 Successfully analyzed {processed} base cases with {total_contingencies} total contingency scenarios")
            
            reliability_df = pd.DataFrame(reliability_data)
            
            # Calculate overall system reliability metrics
            overall_metrics = {
                'total_base_cases': len(reliability_data),
                'avg_reliability_index': reliability_df['reliability_index'].mean(),
                'system_violation_rate': reliability_df['violation_rate'].mean(),
                'worst_case_violations': reliability_df['max_violations'].max(),
                'best_reliability_index': reliability_df['reliability_index'].max(),
                'worst_reliability_index': reliability_df['reliability_index'].min(),
                'total_contingencies_analyzed': total_contingencies
            }
            
            if not reliability_data:
                return {}
            
            reliability_df = pd.DataFrame(reliability_data)
            
            # Calculate reliability metrics
            metrics = {
                'avg_violation_rate': reliability_df['violation_rate'].mean(),
                'max_violation_rate': reliability_df['violation_rate'].max(),
                'total_contingencies_analyzed': len(reliability_df),
                'contingencies_with_violations': len(reliability_df[reliability_df['violations'] > 0]),
                'system_reliability': 1 - (reliability_df['violations'].sum() / reliability_df['total_branches'].sum()),
                'worst_case_scenario': reliability_df.loc[reliability_df['violations'].idxmax()].to_dict() if len(reliability_df) > 0 else {}
            }
            
            return {
                'reliability_metrics': metrics,
                'contingency_analysis': reliability_df.to_dict('records'),
                'summary_by_case': reliability_df.groupby('base_case_id').agg({
                    'violations': 'sum',
                    'violation_rate': 'mean',
                    'total_branches': 'mean'
                }).to_dict()
            }
            
        except Exception as e:
            print(f"Error in reliability analysis: {e}")
            return {}
    
    def economic_analysis(self, base_case_ids=[42, 43, 44, 45, 46]):
        """
        Economic analysis based on generation patterns
        """
        try:
            economic_data = []
            
            for case_id in base_case_ids:
                buses, branches = self.load_base_case_data(case_id)
                
                if not buses.empty:
                    # Simple economic metrics
                    total_generation = buses['PG'].sum()
                    total_load = buses['PD'].sum()
                    
                    # Estimate costs (simplified)
                    generation_cost = total_generation * 50  # $/MWh
                    transmission_losses = max(0, total_generation - total_load)
                    loss_cost = transmission_losses * 50
                    
                    # Generation distribution
                    max_gen_bus = buses.loc[buses['PG'].idxmax()] if buses['PG'].max() > 0 else None
                    num_generating_buses = (buses['PG'] > 0).sum()
                    
                    economic_data.append({
                        'case_id': case_id,
                        'total_generation_mw': total_generation,
                        'total_load_mw': total_load,
                        'transmission_losses_mw': transmission_losses,
                        'generation_cost_usd': generation_cost,
                        'loss_cost_usd': loss_cost,
                        'total_cost_usd': generation_cost + loss_cost,
                        'num_generating_buses': num_generating_buses,
                        'max_generation_mw': buses['PG'].max(),
                        'avg_generation_mw': buses[buses['PG'] > 0]['PG'].mean() if num_generating_buses > 0 else 0,
                        'generation_efficiency': total_load / total_generation if total_generation > 0 else 0
                    })
            
            if not economic_data:
                return {}
            
            economic_df = pd.DataFrame(economic_data)
            
            # Economic insights
            best_case = economic_df.loc[economic_df['total_cost_usd'].idxmin()]
            worst_case = economic_df.loc[economic_df['total_cost_usd'].idxmax()]
            
            return {
                'economic_analysis': economic_df.to_dict('records'),
                'best_case_scenario': best_case.to_dict(),
                'worst_case_scenario': worst_case.to_dict(),
                'average_metrics': economic_df.mean().to_dict(),
                'cost_variance': economic_df['total_cost_usd'].std(),
                'efficiency_range': {
                    'min': economic_df['generation_efficiency'].min(),
                    'max': economic_df['generation_efficiency'].max(),
                    'avg': economic_df['generation_efficiency'].mean()
                }
            }
            
        except Exception as e:
            print(f"Error in economic analysis: {e}")
            return {}
    
    def power_quality_analysis(self, base_case_ids=[42, 43, 44, 45, 46]):
        """
        Power quality analysis based on voltage and power flow data
        """
        try:
            quality_data = []
            
            for case_id in base_case_ids:
                buses, branches = self.load_base_case_data(case_id)
                
                if not buses.empty:
                    # Voltage quality metrics
                    voltages = buses['VM']
                    voltage_deviations = abs(voltages - 1.0)  # Deviation from nominal
                    
                    # Power quality indicators
                    quality_metrics = {
                        'case_id': case_id,
                        'avg_voltage_pu': voltages.mean(),
                        'voltage_std': voltages.std(),
                        'min_voltage_pu': voltages.min(),
                        'max_voltage_pu': voltages.max(),
                        'voltage_deviation_avg': voltage_deviations.mean(),
                        'voltage_deviation_max': voltage_deviations.max(),
                        'low_voltage_buses': (voltages < 0.95).sum(),
                        'high_voltage_buses': (voltages > 1.05).sum(),
                        'voltage_violations': ((voltages < 0.95) | (voltages > 1.05)).sum(),
                        'voltage_quality_index': 1 - voltage_deviations.mean(),  # Higher is better
                        'total_buses': len(buses)
                    }
                    
                    # Power factor analysis if reactive power data available
                    if 'PG' in buses.columns and 'QG' in buses.columns:
                        active_power = buses['PG']
                        reactive_power = buses['QG']
                        
                        # Calculate power factor where applicable
                        apparent_power = np.sqrt(active_power**2 + reactive_power**2)
                        power_factor = np.where(apparent_power > 0, 
                                              active_power / apparent_power, 
                                              1.0)
                        
                        quality_metrics.update({
                            'avg_power_factor': power_factor.mean(),
                            'min_power_factor': power_factor.min(),
                            'poor_pf_buses': (power_factor < 0.9).sum()
                        })
                    
                    quality_data.append(quality_metrics)
            
            if not quality_data:
                return {}
            
            quality_df = pd.DataFrame(quality_data)
            
            # Overall power quality assessment
            overall_quality = {
                'system_voltage_quality': quality_df['voltage_quality_index'].mean(),
                'worst_voltage_case': quality_df.loc[quality_df['voltage_quality_index'].idxmin()]['case_id'],
                'best_voltage_case': quality_df.loc[quality_df['voltage_quality_index'].idxmax()]['case_id'],
                'total_voltage_violations': quality_df['voltage_violations'].sum(),
                'avg_voltage_stability': quality_df['voltage_std'].mean()
            }
            
            return {
                'power_quality_analysis': quality_df.to_dict('records'),
                'overall_assessment': overall_quality,
                'quality_trends': quality_df.describe().to_dict(),
                'violation_summary': {
                    'low_voltage': quality_df['low_voltage_buses'].sum(),
                    'high_voltage': quality_df['high_voltage_buses'].sum(),
                    'total_violations': quality_df['voltage_violations'].sum()
                }
            }
            
        except Exception as e:
            print(f"Error in power quality analysis: {e}")
            return {}
    
    def comprehensive_analysis(self):
        """
        Run all analyses and return comprehensive results
        """
        print("🔍 Starting Comprehensive Power System Statistical Analysis...")
        
        results = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'analyses': {}
        }
        
        analyses = [
            ('correlation_analysis', self.correlation_analysis),
            ('monte_carlo_risk', lambda: self.monte_carlo_risk_assessment(n_simulations=500)),
            ('sensitivity_analysis', self.sensitivity_analysis),
            ('clustering_analysis', self.clustering_analysis),
            ('reliability_statistics', self.reliability_statistics),
            ('economic_analysis', self.economic_analysis),
            ('power_quality_analysis', self.power_quality_analysis)
        ]
        
        for analysis_name, analysis_func in analyses:
            try:
                print(f"  📊 Running {analysis_name}...")
                results['analyses'][analysis_name] = analysis_func()
                print(f"  ✅ {analysis_name} completed")
            except Exception as e:
                print(f"  ❌ Error in {analysis_name}: {e}")
                results['analyses'][analysis_name] = {}
        
        print("🎉 Comprehensive analysis completed!")
        return results
    
    def perform_basic_analysis(self, analysis_type="all", base_case_id=42):
        """
        Perform basic power system analyses
        
        analysis_type options:
        - "all": Run complete basic analysis suite
        - "voltage": Voltage violation analysis
        - "power_flow": Power flow and loading analysis  
        - "contingency": Contingency impact analysis
        - "generation": Generation dispatch analysis
        - "load": Load distribution analysis
        - "losses": System losses analysis
        - "summary": Basic system summary
        """
        
        if analysis_type == "all":
            return self.basic_analysis_suite(base_case_id)
        elif analysis_type == "voltage":
            return self.voltage_violation_analysis(base_case_id)
        elif analysis_type == "power_flow":
            return self.power_flow_analysis(base_case_id)
        elif analysis_type == "contingency":
            return self.contingency_impact_analysis(base_case_id)
        elif analysis_type == "generation":
            return self.generation_dispatch_analysis(base_case_id)
        elif analysis_type == "load":
            return self.load_distribution_analysis(base_case_id)
        elif analysis_type == "losses":
            return self.system_losses_analysis(base_case_id)
        elif analysis_type == "summary":
            return self.basic_system_summary(base_case_id)
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}
    
    def quick_analysis(self, query_type="overview", base_case_id=42):
        """
        Quick analysis for common queries
        
        query_type options:
        - "overview": System overview
        - "violations": All violations (voltage + loading)  
        - "critical": Critical issues only
        - "performance": Performance metrics
        - "health": System health check
        """
        
        try:
            if query_type == "overview":
                summary = self.basic_system_summary(base_case_id)
                voltage = self.voltage_violation_analysis(base_case_id)
                flow = self.power_flow_analysis(base_case_id)
                
                return {
                    'analysis_type': 'overview',
                    'base_case_id': base_case_id,
                    'system_size': {
                        'buses': summary.get('total_buses', 0),
                        'branches': summary.get('total_branches', 0)
                    },
                    'power_balance': {
                        'total_load_mw': summary.get('total_load_mw', 0),
                        'total_generation_mw': summary.get('total_generation_mw', 0),
                        'balance_mw': summary.get('load_generation_balance_mw', 0)
                    },
                    'issues_found': {
                        'voltage_violations': voltage.get('low_voltage_violations', {}).get('count', 0) + voltage.get('high_voltage_violations', {}).get('count', 0),
                        'overloaded_branches': flow.get('overloaded_branches', {}).get('count', 0)
                    }
                }
                
            elif query_type == "violations":
                voltage = self.voltage_violation_analysis(base_case_id)
                flow = self.power_flow_analysis(base_case_id)
                
                violations = {
                    'analysis_type': 'violations',
                    'base_case_id': base_case_id,
                    'voltage_violations': {
                        'low_voltage': voltage.get('low_voltage_violations', {}),
                        'high_voltage': voltage.get('high_voltage_violations', {})
                    },
                    'loading_violations': {
                        'overloaded_branches': flow.get('overloaded_branches', {}),
                        'heavily_loaded_branches': flow.get('heavily_loaded_branches', {})
                    }
                }
                
                return violations
                
            elif query_type == "critical":
                voltage = self.voltage_violation_analysis(base_case_id)
                flow = self.power_flow_analysis(base_case_id)
                contingency = self.contingency_impact_analysis(base_case_id)
                
                critical_issues = []
                
                # Critical voltage violations
                if voltage.get('low_voltage_violations', {}).get('count', 0) > 0:
                    worst_v = voltage['low_voltage_violations'].get('worst_voltage', 'N/A')
                    critical_issues.append(f"Critical low voltage: {worst_v:.3f} p.u.")
                
                # Critical overloads
                if flow.get('overloaded_branches', {}).get('count', 0) > 0:
                    max_loading = flow['overloaded_branches'].get('max_loading', 0)
                    critical_issues.append(f"Critical overload: {max_loading:.1f}%")
                
                # Critical contingencies
                if contingency.get('total_violations', 0) > 10:
                    critical_issues.append(f"High contingency impact: {contingency.get('total_violations', 0)} violations")
                
                return {
                    'analysis_type': 'critical',
                    'base_case_id': base_case_id,
                    'critical_issues': critical_issues,
                    'severity': 'High' if len(critical_issues) >= 2 else 'Medium' if len(critical_issues) == 1 else 'Low'
                }
                
            elif query_type == "performance":
                losses = self.system_losses_analysis(base_case_id)
                gen = self.generation_dispatch_analysis(base_case_id)
                load = self.load_distribution_analysis(base_case_id)
                
                return {
                    'analysis_type': 'performance',
                    'base_case_id': base_case_id,
                    'efficiency_metrics': losses.get('efficiency_metrics', {}),
                    'generation_performance': gen.get('dispatch_metrics', {}),
                    'load_characteristics': load.get('load_metrics', {}),
                    'system_losses': losses.get('power_balance', {}).get('loss_percentage', 0)
                }
                
            elif query_type == "health":
                return self.get_system_health_check(base_case_id)
                
            else:
                return {"error": f"Unknown query type: {query_type}"}
                
        except Exception as e:
            return {"error": f"Quick analysis failed: {str(e)}"}

if __name__ == "__main__":
    # Example usage
    import os
    
    # Try to find the database
    possible_paths = [
        "ndata.db",
        "C:/Users/nira771/SULI_FALL/ndata.db",
        "../ndata.db"
    ]
    
    database_path = None
    for path in possible_paths:
        if os.path.exists(path):
            database_path = path
            break
    
    if database_path:
        analyzer = PowerSystemStatisticalAnalyzer(database_path)
        
        # Run individual analysis example
        print("🔍 Testing Correlation Analysis...")
        correlation_results = analyzer.correlation_analysis()
        if correlation_results:
            print("✅ Correlation analysis successful!")
            print(f"   Found {len(correlation_results.get('strong_correlations', []))} strong correlations")
        
        # Uncomment to run comprehensive analysis
        # comprehensive_results = analyzer.comprehensive_analysis()
        
    else:
        print("❌ Database not found. Please check the database path.")