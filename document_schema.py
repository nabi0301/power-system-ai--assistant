"""
PostgreSQL Database Schema Documentation Generator
Generates comprehensive documentation for the '118' PostgreSQL database
"""

import psycopg2
from datetime import datetime

# Database configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': '118',
    'user': 'postgres',
    'password': 'pnnl'
}

OUTPUT_FILE = 'C:\\Users\\nira771\\PostgreSQL_118_Database_Documentation.md'

def get_all_tables(conn):
    """Get all tables in the public schema"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_table_columns(conn, table_name):
    """Get column information for a table"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    columns = cursor.fetchall()
    cursor.close()
    return columns

def get_primary_keys(conn, table_name):
    """Get primary key columns for a table"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = quote_ident(%s)::regclass
            AND i.indisprimary;
        """, (table_name,))
        pks = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return pks
    except Exception as e:
        cursor.close()
        return []

def get_foreign_keys(conn, table_name):
    """Get foreign key constraints for a table"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = %s
        AND tc.table_schema = 'public';
    """, (table_name,))
    fks = cursor.fetchall()
    cursor.close()
    return fks

def get_indexes(conn, table_name):
    """Get indexes for a table"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE tablename = %s
        AND schemaname = 'public';
    """, (table_name,))
    indexes = cursor.fetchall()
    cursor.close()
    return indexes

def get_row_count(conn, table_name):
    """Get approximate row count for a table"""
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except Exception as e:
        cursor.close()
        return "Error"

def get_table_size(conn, table_name):
    """Get table size in human-readable format"""
    cursor = conn.cursor()
    try:
        # Properly quote table name to handle case sensitivity
        cursor.execute("""
            SELECT pg_size_pretty(pg_total_relation_size(quote_ident(%s)::regclass));
        """, (table_name,))
        size = cursor.fetchone()[0]
        cursor.close()
        return size
    except Exception as e:
        cursor.close()
        return "N/A"

def categorize_tables(tables):
    """Categorize tables by their purpose"""
    categories = {
        'Base Case Data': [],
        'Contingency Data': [],
        'DLR (Dynamic Line Rating)': [],
        'SLR (Static Line Rating)': [],
        'System/Metadata': [],
        'SQLite Migration': []
    }
    
    for table in tables:
        table_lower = table.lower()
        if 'sqlite' in table_lower:
            categories['SQLite Migration'].append(table)
        elif table_lower.startswith('base'):
            categories['Base Case Data'].append(table)
        elif table_lower.startswith('contingency'):
            categories['Contingency Data'].append(table)
        elif table_lower.startswith('dlr'):
            categories['DLR (Dynamic Line Rating)'].append(table)
        elif table_lower.startswith('slr'):
            categories['SLR (Static Line Rating)'].append(table)
        else:
            categories['System/Metadata'].append(table)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

def generate_documentation(conn):
    """Generate comprehensive database documentation"""
    
    doc_lines = []
    
    # Header
    doc_lines.append("# PostgreSQL Database '118' - Schema Documentation")
    doc_lines.append("")
    doc_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc_lines.append(f"**Database**: {POSTGRES_CONFIG['dbname']}")
    doc_lines.append(f"**Host**: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
    doc_lines.append("")
    doc_lines.append("---")
    doc_lines.append("")
    
    # Get all tables
    tables = get_all_tables(conn)
    doc_lines.append(f"## Database Overview")
    doc_lines.append("")
    doc_lines.append(f"**Total Tables**: {len(tables)}")
    doc_lines.append("")
    
    # Categorize tables
    categories = categorize_tables(tables)
    
    doc_lines.append("### Table Categories")
    doc_lines.append("")
    for category, table_list in categories.items():
        doc_lines.append(f"- **{category}**: {len(table_list)} tables")
    doc_lines.append("")
    doc_lines.append("---")
    doc_lines.append("")
    
    # Table of Contents
    doc_lines.append("## Table of Contents")
    doc_lines.append("")
    for idx, table in enumerate(tables, 1):
        doc_lines.append(f"{idx}. [{table}](#{table.lower().replace('_', '-')})")
    doc_lines.append("")
    doc_lines.append("---")
    doc_lines.append("")
    
    # Detailed table documentation
    doc_lines.append("## Detailed Table Documentation")
    doc_lines.append("")
    
    for table in tables:
        print(f"Documenting table: {table}")
        
        doc_lines.append(f"### {table}")
        doc_lines.append("")
        
        # Get table metadata
        row_count = get_row_count(conn, table)
        table_size = get_table_size(conn, table)
        
        doc_lines.append(f"**Row Count**: {row_count:,}" if isinstance(row_count, int) else f"**Row Count**: {row_count}")
        doc_lines.append(f"**Table Size**: {table_size}")
        doc_lines.append("")
        
        # Columns
        columns = get_table_columns(conn, table)
        primary_keys = get_primary_keys(conn, table)
        
        doc_lines.append("#### Columns")
        doc_lines.append("")
        doc_lines.append("| Column Name | Data Type | Nullable | Default | Primary Key |")
        doc_lines.append("|-------------|-----------|----------|---------|-------------|")
        
        for col in columns:
            col_name, data_type, max_length, is_nullable, default = col
            
            # Format data type
            if max_length:
                data_type_str = f"{data_type}({max_length})"
            else:
                data_type_str = data_type
            
            # Format default
            default_str = str(default) if default else "-"
            if len(default_str) > 30:
                default_str = default_str[:27] + "..."
            
            # Check if primary key
            is_pk = "✓" if col_name in primary_keys else ""
            
            doc_lines.append(f"| {col_name} | {data_type_str} | {is_nullable} | {default_str} | {is_pk} |")
        
        doc_lines.append("")
        
        # Foreign Keys
        foreign_keys = get_foreign_keys(conn, table)
        if foreign_keys:
            doc_lines.append("#### Foreign Keys")
            doc_lines.append("")
            doc_lines.append("| Column | References Table | References Column |")
            doc_lines.append("|--------|------------------|-------------------|")
            for fk in foreign_keys:
                col_name, ref_table, ref_col = fk
                doc_lines.append(f"| {col_name} | {ref_table} | {ref_col} |")
            doc_lines.append("")
        
        # Indexes
        indexes = get_indexes(conn, table)
        if indexes:
            doc_lines.append("#### Indexes")
            doc_lines.append("")
            for idx_name, idx_def in indexes:
                doc_lines.append(f"- **{idx_name}**")
                doc_lines.append(f"  ```sql")
                doc_lines.append(f"  {idx_def}")
                doc_lines.append(f"  ```")
            doc_lines.append("")
        
        doc_lines.append("---")
        doc_lines.append("")
    
    # Summary by category
    doc_lines.append("## Summary by Category")
    doc_lines.append("")
    
    for category, table_list in categories.items():
        doc_lines.append(f"### {category}")
        doc_lines.append("")
        total_rows = 0
        doc_lines.append("| Table Name | Row Count | Size |")
        doc_lines.append("|------------|-----------|------|")
        
        for table in table_list:
            row_count = get_row_count(conn, table)
            table_size = get_table_size(conn, table)
            row_count_str = f"{row_count:,}" if isinstance(row_count, int) else row_count
            if isinstance(row_count, int):
                total_rows += row_count
            doc_lines.append(f"| {table} | {row_count_str} | {table_size} |")
        
        doc_lines.append(f"| **Total** | **{total_rows:,}** | |")
        doc_lines.append("")
    
    # Database statistics
    doc_lines.append("---")
    doc_lines.append("")
    doc_lines.append("## Database Statistics")
    doc_lines.append("")
    
    cursor = conn.cursor()
    
    # Total database size
    cursor.execute("SELECT pg_size_pretty(pg_database_size(%s));", (POSTGRES_CONFIG['dbname'],))
    db_size = cursor.fetchone()[0]
    doc_lines.append(f"**Total Database Size**: {db_size}")
    doc_lines.append("")
    
    # Total rows across all tables
    total_rows = sum(get_row_count(conn, table) for table in tables if isinstance(get_row_count(conn, table), int))
    doc_lines.append(f"**Total Rows (all tables)**: {total_rows:,}")
    doc_lines.append("")
    
    cursor.close()
    
    return "\n".join(doc_lines)

def main():
    print("=" * 80)
    print("PostgreSQL Database Schema Documentation Generator")
    print("=" * 80)
    print(f"Database: {POSTGRES_CONFIG['dbname']}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 80)
    print()
    
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        print(f"[OK] Connected to PostgreSQL database '{POSTGRES_CONFIG['dbname']}'")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to connect to PostgreSQL: {e}")
        return
    
    try:
        # Generate documentation
        print("Generating documentation...")
        print()
        documentation = generate_documentation(conn)
        
        # Write to file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        print()
        print("=" * 80)
        print("[OK] Documentation generated successfully!")
        print(f"Output file: {OUTPUT_FILE}")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] Failed to generate documentation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("\n[OK] Database connection closed")

if __name__ == "__main__":
    main()
