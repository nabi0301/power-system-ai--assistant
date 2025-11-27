"""
Document Ingestion and Chunking for Power System RAG
==================================================

This module implements sophisticated document ingestion and chunking specifically
optimized for power system tabular data with proper metadata preservation.

Key Features:
- Optimal chunk sizes (400-1000 tokens for text, 200-400 for tables)
- 10-30% overlap preservation
- Rich metadata (case ID, bus/branch IDs, timestamps, row indices)
- Tabular data preprocessing (textual + raw representations)
- Intelligent chunking that preserves power system context

Author: Power System Analysis Team
Date: September 2025
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
import re
from datetime import datetime
import hashlib
from dataclasses import dataclass, asdict

# Import from our core RAG module
from power_system_rag_core import ChunkMetadata

logger = logging.getLogger(__name__)

class PowerSystemDocumentIngestor:
    """
    Advanced document ingestion system for power system data.
    
    Handles chunking, metadata extraction, and preprocessing of tabular
    power system data for optimal RAG performance.
    """
    
    def __init__(
        self,
        db_path: str,
        chunk_size_text: int = 600,
        chunk_size_table: int = 300,
        overlap_percentage: float = 0.2,
        max_tokens_per_chunk: int = 1000
    ):
        """
        Initialize the document ingestor.
        
        Args:
            db_path: Path to SQLite database
            chunk_size_text: Target size for text chunks
            chunk_size_table: Target size for tabular data chunks  
            overlap_percentage: Overlap between chunks (0.1-0.3 recommended)
            max_tokens_per_chunk: Maximum tokens per chunk
        """
        self.db_path = db_path
        self.chunk_size_text = chunk_size_text
        self.chunk_size_table = chunk_size_table
        self.overlap_percentage = overlap_percentage
        self.max_tokens_per_chunk = max_tokens_per_chunk
        
        # Power system specific patterns
        self.bus_pattern = re.compile(r'bus[_\s]*(\d+)', re.IGNORECASE)
        self.branch_pattern = re.compile(r'branch[_\s]*(\d+)', re.IGNORECASE)
        self.voltage_pattern = re.compile(r'(\d+\.?\d*)\s*(kv|v|volt)', re.IGNORECASE)
        self.power_pattern = re.compile(r'(\d+\.?\d*)\s*(mw|mvar|kw)', re.IGNORECASE)
        
        logger.info(f"Document ingestor initialized for {db_path}")
    
    def ingest_database(self) -> List[Dict[str, Any]]:
        """
        Ingest entire database and create optimized chunks.
        
        Returns:
            List of document chunks with metadata
        """
        logger.info("Starting database ingestion...")
        
        chunks = []
        
        try:
            # Get all tables in the database
            tables = self._get_database_tables()
            logger.info(f"Found {len(tables)} tables to process")
            
            # Process each table
            for table_name in tables:
                logger.info(f"Processing table: {table_name}")
                
                table_chunks = self._process_table(table_name)
                chunks.extend(table_chunks)
                
                logger.info(f"Created {len(table_chunks)} chunks from {table_name}")
            
            logger.info(f"Total chunks created: {len(chunks)}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error during database ingestion: {e}")
            return []
    
    def _get_database_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return tables
            
        except Exception as e:
            logger.error(f"Error getting database tables: {e}")
            return []
    
    def _process_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Process a single table and create optimized chunks.
        
        Args:
            table_name: Name of the database table
            
        Returns:
            List of chunks for this table
        """
        try:
            # Load table data
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()
            
            if df.empty:
                logger.warning(f"Table {table_name} is empty")
                return []
            
            # Determine table type and processing strategy
            table_type = self._classify_table_type(table_name, df)
            logger.info(f"Table {table_name} classified as: {table_type}")
            
            # Process based on table type
            if table_type == "bus_data":
                return self._process_bus_data_table(table_name, df)
            elif table_type == "branch_data":
                return self._process_branch_data_table(table_name, df)
            elif table_type == "contingency":
                return self._process_contingency_table(table_name, df)
            else:
                return self._process_generic_table(table_name, df)
                
        except Exception as e:
            logger.error(f"Error processing table {table_name}: {e}")
            return []
    
    def _classify_table_type(self, table_name: str, df: pd.DataFrame) -> str:
        """Classify the type of power system table"""
        name_lower = table_name.lower()
        columns_lower = [col.lower() for col in df.columns]
        
        # Bus data tables
        if any(keyword in name_lower for keyword in ['bus', 'node']) or \
           any(col in columns_lower for col in ['vm', 'va', 'pd', 'qd', 'pg', 'qg', 'bus_number']):
            return "bus_data"
        
        # Branch/Line data tables
        elif any(keyword in name_lower for keyword in ['branch', 'line', 'transmission']) or \
             any(col in columns_lower for col in ['from_bus', 'to_bus', 'pf', 'qf', 'pt', 'qt']):
            return "branch_data"
        
        # Contingency tables
        elif any(keyword in name_lower for keyword in ['contingency', 'outage', 'scenario']):
            return "contingency"
        
        else:
            return "generic"
    
    def _process_bus_data_table(self, table_name: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process bus data tables with power system specific chunking"""
        chunks = []
        
        # Determine case type and ID
        case_type, case_id = self._extract_case_info(table_name, df)
        
        # Group by logical units (e.g., voltage levels, geographic regions)
        chunk_size = self.chunk_size_table
        
        for start_idx in range(0, len(df), chunk_size):
            end_idx = min(start_idx + chunk_size, len(df))
            chunk_df = df.iloc[start_idx:end_idx]
            
            # Create textual representation
            text_content = self._bus_data_to_text(chunk_df, table_name)
            
            # Create tabular representation
            table_content = self._dataframe_to_structured_text(chunk_df)
            
            # Extract metadata
            bus_ids = self._extract_bus_ids(chunk_df)
            
            # Create chunk metadata
            metadata = ChunkMetadata(
                chunk_id=f"{table_name}_{start_idx}_{end_idx}",
                source_file=table_name,
                case_id=case_id,
                case_type=case_type,
                bus_ids=bus_ids,
                branch_ids=[],
                timestamp=datetime.now().isoformat(),
                row_index=start_idx,
                chunk_size=len(text_content),
                original_table=table_name,
                confidence_score=1.0
            )
            
            # Create chunk document
            full_content = f"{text_content}\n\nTabular Data:\n{table_content}"
            
            chunks.append({
                'content': full_content,
                'metadata': asdict(metadata),
                'embedding_content': text_content  # What gets embedded
            })
        
        return chunks
    
    def _process_branch_data_table(self, table_name: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process branch/transmission line data tables"""
        chunks = []
        
        case_type, case_id = self._extract_case_info(table_name, df)
        chunk_size = self.chunk_size_table
        
        for start_idx in range(0, len(df), chunk_size):
            end_idx = min(start_idx + chunk_size, len(df))
            chunk_df = df.iloc[start_idx:end_idx]
            
            # Create textual representation
            text_content = self._branch_data_to_text(chunk_df, table_name)
            table_content = self._dataframe_to_structured_text(chunk_df)
            
            # Extract IDs
            bus_ids = self._extract_bus_ids_from_branches(chunk_df)
            branch_ids = self._extract_branch_ids(chunk_df)
            
            metadata = ChunkMetadata(
                chunk_id=f"{table_name}_{start_idx}_{end_idx}",
                source_file=table_name,
                case_id=case_id,
                case_type=case_type,
                bus_ids=bus_ids,
                branch_ids=branch_ids,
                timestamp=datetime.now().isoformat(),
                row_index=start_idx,
                chunk_size=len(text_content),
                original_table=table_name,
                confidence_score=1.0
            )
            
            full_content = f"{text_content}\n\nTabular Data:\n{table_content}"
            
            chunks.append({
                'content': full_content,
                'metadata': asdict(metadata),
                'embedding_content': text_content
            })
        
        return chunks
    
    def _process_contingency_table(self, table_name: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process contingency analysis tables"""
        chunks = []
        
        # Group by contingency case
        if 'contingency_case_id' in df.columns:
            for case_id in df['contingency_case_id'].unique():
                case_df = df[df['contingency_case_id'] == case_id]
                
                text_content = self._contingency_data_to_text(case_df, table_name, case_id)
                table_content = self._dataframe_to_structured_text(case_df)
                
                bus_ids = self._extract_bus_ids(case_df)
                branch_ids = self._extract_branch_ids(case_df)
                
                metadata = ChunkMetadata(
                    chunk_id=f"{table_name}_contingency_{case_id}",
                    source_file=table_name,
                    case_id=str(case_id),
                    case_type="contingency",
                    bus_ids=bus_ids,
                    branch_ids=branch_ids,
                    timestamp=datetime.now().isoformat(),
                    row_index=0,
                    chunk_size=len(text_content),
                    original_table=table_name,
                    confidence_score=1.0
                )
                
                full_content = f"{text_content}\n\nTabular Data:\n{table_content}"
                
                chunks.append({
                    'content': full_content,
                    'metadata': asdict(metadata),
                    'embedding_content': text_content
                })
        else:
            # Process as generic table
            return self._process_generic_table(table_name, df)
        
        return chunks
    
    def _process_generic_table(self, table_name: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process generic tables with basic chunking"""
        chunks = []
        
        chunk_size = self.chunk_size_text
        overlap_size = int(chunk_size * self.overlap_percentage)
        
        for start_idx in range(0, len(df), chunk_size - overlap_size):
            end_idx = min(start_idx + chunk_size, len(df))
            chunk_df = df.iloc[start_idx:end_idx]
            
            text_content = self._generic_data_to_text(chunk_df, table_name)
            table_content = self._dataframe_to_structured_text(chunk_df)
            
            metadata = ChunkMetadata(
                chunk_id=f"{table_name}_{start_idx}_{end_idx}",
                source_file=table_name,
                case_id="unknown",
                case_type="generic",
                bus_ids=[],
                branch_ids=[],
                timestamp=datetime.now().isoformat(),
                row_index=start_idx,
                chunk_size=len(text_content),
                original_table=table_name,
                confidence_score=0.8
            )
            
            full_content = f"{text_content}\n\nTabular Data:\n{table_content}"
            
            chunks.append({
                'content': full_content,
                'metadata': asdict(metadata),
                'embedding_content': text_content
            })
        
        return chunks
    
    def _extract_case_info(self, table_name: str, df: pd.DataFrame) -> Tuple[str, str]:
        """Extract case type and ID from table"""
        name_lower = table_name.lower()
        
        # Determine case type
        if 'base' in name_lower:
            case_type = "base"
        elif 'slr' in name_lower:
            case_type = "slr"
        elif 'dlr' in name_lower:
            case_type = "dlr"
        elif 'contingency' in name_lower:
            case_type = "contingency"
        else:
            case_type = "unknown"
        
        # Extract case ID
        case_id = "0"  # Default
        
        # Look for case ID in columns
        if 'case_id' in df.columns:
            case_id = str(df['case_id'].iloc[0])
        elif 'base_case_id' in df.columns:
            case_id = str(df['base_case_id'].iloc[0])
        elif any('id' in col.lower() for col in df.columns):
            id_col = next(col for col in df.columns if 'id' in col.lower())
            case_id = str(df[id_col].iloc[0])
        
        return case_type, case_id
    
    def _bus_data_to_text(self, df: pd.DataFrame, table_name: str) -> str:
        """Convert bus data to descriptive text"""
        descriptions = [f"Power system bus data from {table_name}:"]
        
        for _, row in df.iterrows():
            bus_desc = []
            
            # Bus identification
            if 'BUS_NUMBER' in row:
                bus_desc.append(f"Bus {row['BUS_NUMBER']}")
            elif 'bus_number' in row:
                bus_desc.append(f"Bus {row['bus_number']}")
            
            # Voltage information
            if 'VM' in row:
                bus_desc.append(f"voltage magnitude {row['VM']:.3f} per unit")
            if 'VA' in row:
                bus_desc.append(f"voltage angle {row['VA']:.3f} degrees")
            if 'BASE_KV' in row:
                bus_desc.append(f"base voltage {row['BASE_KV']:.1f} kV")
            
            # Load information
            if 'PD' in row and row['PD'] > 0:
                bus_desc.append(f"active load {row['PD']:.1f} MW")
            if 'QD' in row and row['QD'] != 0:
                bus_desc.append(f"reactive load {row['QD']:.1f} MVAr")
            
            # Generation information
            if 'PG' in row and row['PG'] > 0:
                bus_desc.append(f"active generation {row['PG']:.1f} MW")
            if 'QG' in row and row['QG'] != 0:
                bus_desc.append(f"reactive generation {row['QG']:.1f} MVAr")
            
            if bus_desc:
                descriptions.append(" with ".join(bus_desc) + ".")
        
        return " ".join(descriptions)
    
    def _branch_data_to_text(self, df: pd.DataFrame, table_name: str) -> str:
        """Convert branch data to descriptive text"""
        descriptions = [f"Power system branch data from {table_name}:"]
        
        for _, row in df.iterrows():
            branch_desc = []
            
            # Branch identification
            if 'FROM_BUS' in row and 'TO_BUS' in row:
                branch_desc.append(f"Branch from bus {row['FROM_BUS']} to bus {row['TO_BUS']}")
            
            # Power flow information
            if 'PF' in row:
                branch_desc.append(f"real power flow {row['PF']:.1f} MW")
            if 'QF' in row:
                branch_desc.append(f"reactive power flow {row['QF']:.1f} MVAr")
            
            # Ratings and limits
            if 'RATE_A' in row and row['RATE_A'] > 0:
                branch_desc.append(f"thermal rating {row['RATE_A']:.1f} MVA")
            
            # Loading
            if 'PF' in row and 'RATE_A' in row and row['RATE_A'] > 0:
                loading = abs(row['PF']) / row['RATE_A'] * 100
                branch_desc.append(f"loading {loading:.1f}%")
            
            if branch_desc:
                descriptions.append(" with ".join(branch_desc) + ".")
        
        return " ".join(descriptions)
    
    def _contingency_data_to_text(self, df: pd.DataFrame, table_name: str, case_id: str) -> str:
        """Convert contingency data to descriptive text"""
        description = f"Contingency analysis results for case {case_id} from {table_name}: "
        
        # Count violations and issues
        voltage_violations = 0
        thermal_violations = 0
        
        if 'VM' in df.columns:
            voltage_violations = len(df[(df['VM'] < 0.95) | (df['VM'] > 1.05)])
        
        # Add summary statistics
        summary = [f"{len(df)} system elements analyzed"]
        
        if voltage_violations > 0:
            summary.append(f"{voltage_violations} voltage violations detected")
        
        return description + ", ".join(summary) + "."
    
    def _generic_data_to_text(self, df: pd.DataFrame, table_name: str) -> str:
        """Convert generic data to text"""
        return f"Data from table {table_name} with {len(df)} records and columns: {', '.join(df.columns)}."
    
    def _dataframe_to_structured_text(self, df: pd.DataFrame) -> str:
        """Convert dataframe to structured text format"""
        lines = []
        
        # Add column headers
        lines.append("| " + " | ".join(str(col) for col in df.columns) + " |")
        lines.append("|" + "|".join("---" for _ in df.columns) + "|")
        
        # Add data rows (limit to prevent huge chunks)
        for i, (_, row) in enumerate(df.iterrows()):
            if i >= 20:  # Limit rows per chunk
                lines.append(f"... and {len(df) - 20} more rows")
                break
            
            row_values = []
            for val in row:
                if pd.isna(val):
                    row_values.append("--")
                elif isinstance(val, float):
                    row_values.append(f"{val:.3f}")
                else:
                    row_values.append(str(val))
            
            lines.append("| " + " | ".join(row_values) + " |")
        
        return "\n".join(lines)
    
    def _extract_bus_ids(self, df: pd.DataFrame) -> List[str]:
        """Extract bus IDs from dataframe"""
        bus_ids = []
        
        for col in ['BUS_NUMBER', 'bus_number', 'BUS_ID', 'bus_id']:
            if col in df.columns:
                bus_ids.extend([str(x) for x in df[col].dropna().unique()])
                break
        
        return bus_ids
    
    def _extract_bus_ids_from_branches(self, df: pd.DataFrame) -> List[str]:
        """Extract bus IDs from branch data (from_bus, to_bus)"""
        bus_ids = []
        
        for col in ['FROM_BUS', 'TO_BUS', 'from_bus', 'to_bus']:
            if col in df.columns:
                bus_ids.extend([str(x) for x in df[col].dropna().unique()])
        
        return list(set(bus_ids))  # Remove duplicates
    
    def _extract_branch_ids(self, df: pd.DataFrame) -> List[str]:
        """Extract branch IDs from dataframe"""
        branch_ids = []
        
        # Look for explicit branch ID columns
        for col in ['BRANCH_ID', 'branch_id', 'LINE_ID', 'line_id']:
            if col in df.columns:
                branch_ids.extend([str(x) for x in df[col].dropna().unique()])
                return branch_ids
        
        # Create branch IDs from from_bus-to_bus pairs
        if 'FROM_BUS' in df.columns and 'TO_BUS' in df.columns:
            for _, row in df.iterrows():
                branch_ids.append(f"{row['FROM_BUS']}-{row['TO_BUS']}")
        elif 'from_bus' in df.columns and 'to_bus' in df.columns:
            for _, row in df.iterrows():
                branch_ids.append(f"{row['from_bus']}-{row['to_bus']}")
        
        return branch_ids


# Export the main class
__all__ = ['PowerSystemDocumentIngestor']