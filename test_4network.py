"""
Test script to verify 4-network comparison rendering for case 43
"""
import sys
sys.path.append('C:\\Projects\\dlr-database-project')

from network_comparison_clean import create_clean_four_network_comparison
import sqlite3

def get_sqlite_connection():
    return sqlite3.connect('C:\\Projects\\dlr-database-project\\data.db')

# Mock create_network_graph - we'll import the real one
from data_viz_fall import create_network_graph

# Test contingencies
contingencies = [55, 89, 122, 123, 157]

for cont_id in contingencies:
    print(f"\n{'='*80}")
    print(f"Testing Case 43, Contingency {cont_id}")
    print(f"{'='*80}")
    
    fig = create_clean_four_network_comparison(
        case_id=43,
        contingency_id=cont_id,
        get_sqlite_connection_func=get_sqlite_connection,
        create_network_graph_func=create_network_graph
    )
    
    if fig:
        print(f"✓ Figure created with {len(fig.data)} traces")
        print(f"✓ Figure layout: width={fig.layout.width}, height={fig.layout.height}")
        print(f"✓ Annotations: {len(fig.layout.annotations)}")
        if fig.layout.annotations:
            for i, ann in enumerate(fig.layout.annotations):
                print(f"   Annotation {i}: y={ann.y}, text_length={len(ann.text)}")
    else:
        print("✗ Figure creation failed")
