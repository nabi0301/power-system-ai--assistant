import psycopg2

# Create schema for contingency case loader
conn = psycopg2.connect(
    host='localhost', 
    database='118', 
    user='postgres', 
    password='pnnl'
)
cursor = conn.cursor()

print('Creating BaseCases table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS BaseCases (
    base_case_id SERIAL PRIMARY KEY,
    case_number INTEGER UNIQUE NOT NULL,
    filename VARCHAR(255),
    case_name VARCHAR(255),
    folder_name VARCHAR(255),
    buses_count INTEGER DEFAULT 0,
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

print('Creating BaseBusData table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS BaseBusData (
    bus_data_id SERIAL PRIMARY KEY,
    base_case_id INTEGER REFERENCES BaseCases(base_case_id) ON DELETE CASCADE,
    bus_number INTEGER NOT NULL,
    vm FLOAT,
    va FLOAT,
    base_kv FLOAT,
    pg FLOAT,
    qg FLOAT,
    pd FLOAT,
    qd FLOAT,
    UNIQUE(base_case_id, bus_number)
)
""")

print('Creating ContingencyCases table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS ContingencyCases (
    contingency_case_id SERIAL PRIMARY KEY,
    base_case_id INTEGER REFERENCES BaseCases(base_case_id),
    case_number INTEGER NOT NULL,
    filename VARCHAR(255),
    case_name VARCHAR(255),
    contingency_element VARCHAR(255),
    folder_name VARCHAR(255),
    buses_count INTEGER DEFAULT 0,
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(base_case_id, case_number)
)
""")

print('Creating ContingencyBusData table...')
cursor.execute("""
CREATE TABLE IF NOT EXISTS ContingencyBusData (
    bus_data_id SERIAL PRIMARY KEY,
    contingency_case_id INTEGER REFERENCES ContingencyCases(contingency_case_id) ON DELETE CASCADE,
    bus_number INTEGER NOT NULL,
    vm FLOAT,
    va FLOAT,
    base_kv FLOAT,
    pg FLOAT,
    qg FLOAT,
    pd FLOAT,
    qd FLOAT,
    UNIQUE(contingency_case_id, bus_number)
)
""")

conn.commit()
print('✅ All tables created successfully!')
cursor.close()
conn.close()