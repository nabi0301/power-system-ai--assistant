import psycopg2

conn = psycopg2.connect(host='localhost', port='5432', database='118', user='postgres', password='pnnl')
cursor = conn.cursor()

# Check contingency_cases structure
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'contingency_cases'")
columns = cursor.fetchall()
print('contingency_cases columns:', [col[0] for col in columns])

cursor.close()
conn.close()