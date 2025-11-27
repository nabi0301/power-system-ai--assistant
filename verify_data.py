import psycopg2

conn = psycopg2.connect(host='localhost', port='5432', database='118', user='postgres', password='pnnl')
cursor = conn.cursor()

print('=== Generator Corrective Actions (Sample) ===')
cursor.execute("""
    SELECT cd.contingency_name, gca.bus_number, gca.gen_initial_mw, 
           gca.gen_final_mw, gca.gen_adjustment_mw, gca.kv_level
    FROM GeneratorCorrectiveActions gca
    JOIN ContingencyDetails cd ON gca.contingency_detail_id = cd.contingency_detail_id
    WHERE cd.contingency_name = 'Line_77_80_2'
    ORDER BY gca.bus_number
    LIMIT 5
""")
results = cursor.fetchall()
for row in results:
    print(f'  Bus {row[1]}: Initial={row[2]:.1f}MW, Final={row[3]:.1f}MW, Adj={row[4]:.1f}MW, KV={row[5]:.1f}')

print('\n=== Load Corrective Actions (Sample) ===')
cursor.execute("""
    SELECT cd.contingency_name, lca.bus_number, lca.load_initial_mw, 
           lca.load_final_mw, lca.load_adjustment_mw, lca.kv_level
    FROM LoadCorrectiveActions lca
    JOIN ContingencyDetails cd ON lca.contingency_detail_id = cd.contingency_detail_id
    ORDER BY lca.bus_number
    LIMIT 5
""")
results = cursor.fetchall()
for row in results:
    print(f'  Bus {row[1]}: Initial={row[2]:.1f}MW, Final={row[3]:.1f}MW, Adj={row[4]:.1f}MW, KV={row[5]:.1f}')

print('\n=== Exact CSV Comparison ===')
print('From dlr_idx_122_line_77_80_2_cor_gen.csv:')
print('BUS_NUMBER,KV_LEVEL,GEN-INI,GEN-NEW,GEN-ADJ')
print('69,138.0,396.1,485.0,88.89999999999998')
print('80,138.0,305.8,186.2,-119.60000000000002')

print('\nDatabase values for same buses:')
cursor.execute("""
    SELECT gca.bus_number, gca.kv_level, gca.gen_initial_mw, 
           gca.gen_final_mw, gca.gen_adjustment_mw
    FROM GeneratorCorrectiveActions gca
    JOIN ContingencyDetails cd ON gca.contingency_detail_id = cd.contingency_detail_id
    WHERE cd.contingency_name = 'Line_77_80_2' AND gca.bus_number IN (69, 80)
    ORDER BY gca.bus_number
""")
results = cursor.fetchall()
for row in results:
    print(f'{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}')

cursor.close()
conn.close()