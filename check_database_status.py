import psycopg2

# Connect to PostgreSQL database
conn = psycopg2.connect(database='118', user='postgres', password='pnnl')
cur = conn.cursor()

print("=" * 70)
print("DATABASE SUMMARY - PostgreSQL '118' Database")
print("=" * 70)

# Check base cases
cur.execute("SELECT COUNT(*) FROM BaseCases WHERE processing_status = 'completed'")
base_cases_count = cur.fetchone()[0]
print(f"\n✓ Base Cases (completed): {base_cases_count:,}")

# Check base bus data
cur.execute("SELECT COUNT(*) FROM BaseBusData")
base_bus_count = cur.fetchone()[0]
print(f"✓ Base Bus Data records: {base_bus_count:,}")

# Check base branch data
cur.execute("SELECT COUNT(*) FROM BaseBranchData")
base_branch_count = cur.fetchone()[0]
print(f"✓ Base Branch Data records: {base_branch_count:,}")

# Check contingency cases
cur.execute("SELECT COUNT(*) FROM ContingencyCases WHERE processing_status = 'completed'")
contingency_cases_count = cur.fetchone()[0]
print(f"\n✓ Contingency Cases (completed): {contingency_cases_count:,}")

# Check contingency bus data
cur.execute("SELECT COUNT(*) FROM ContingencyBusData")
contingency_bus_count = cur.fetchone()[0]
print(f"✓ Contingency Bus Data records: {contingency_bus_count:,}")

# Check contingency branch data
cur.execute("SELECT COUNT(*) FROM ContingencyBranchData")
contingency_branch_count = cur.fetchone()[0]
print(f"✓ Contingency Branch Data records: {contingency_branch_count:,}")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

if base_cases_count > 0:
    print(f"✓ Base cases loaded: {base_cases_count} cases")
    print(f"  - Average buses per case: {base_bus_count / base_cases_count:.0f}")
    print(f"  - Average branches per case: {base_branch_count / base_cases_count:.0f}")

if contingency_cases_count > 0:
    print(f"\n✓ Contingency cases loaded: {contingency_cases_count} cases")
    print(f"  - Average buses per case: {contingency_bus_count / contingency_cases_count:.0f}")
    print(f"  - Average branches per case: {contingency_branch_count / contingency_cases_count:.0f}")
    
    # Check how many cases per base case
    cur.execute("""
        SELECT base_case_id, COUNT(*) as cont_count 
        FROM ContingencyCases 
        GROUP BY base_case_id 
        ORDER BY base_case_id 
        LIMIT 5
    """)
    results = cur.fetchall()
    if results:
        print(f"\n  Sample contingency distribution:")
        for base_id, count in results:
            print(f"    Base case {base_id}: {count} contingency cases")
else:
    print("\n⚠ NO CONTINGENCY CASES LOADED YET")

# Sample data check
print("\n" + "=" * 70)
print("SAMPLE DATA")
print("=" * 70)

# Sample base case
cur.execute("SELECT case_number, filename, buses_count, branches_count FROM BaseCases LIMIT 3")
print("\nSample Base Cases:")
for row in cur.fetchall():
    print(f"  Case {row[0]}: {row[1]} ({row[2]} buses, {row[3]} branches)")

# Sample contingency case
cur.execute("SELECT case_number, filename, buses_count, branches_count FROM ContingencyCases LIMIT 3")
results = cur.fetchall()
if results:
    print("\nSample Contingency Cases:")
    for row in results:
        print(f"  Case {row[0]}: {row[1]} ({row[2]} buses, {row[3]} branches)")

conn.close()
print("\n" + "=" * 70)
