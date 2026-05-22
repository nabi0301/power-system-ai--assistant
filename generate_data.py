"""
generate_data.py — creates data.db with all tables the power system app needs
"""
import sqlite3, numpy as np, os

DB_PATH = "data.db"
np.random.seed(42)

BUS_COORDS = {
    1:(-47.507,165.097),2:(-47.481,188.962),3:(-46.545,190.083),4:(-48.084,164.030),
    5:(-48.019,163.058),6:(-48.899,163.061),7:(-42.619,186.135),8:(-48.952,173.015),
    9:(-43.451,162.401),10:(-48.807,173.969),11:(-45.638,185.097),12:(-45.765,161.289),
    13:(-42.676,185.101),14:(-42.138,184.114),15:(-50.598,172.987),16:(-50.369,173.919),
    17:(-47.965,174.868),18:(-47.965,175.817),19:(-50.478,162.989),20:(-50.354,163.917),
    21:(-50.231,164.846),22:(-50.231,164.846),23:(-52.425,162.826),24:(-55.920,166.676),
    25:(-60.998,160.830),26:(-60.479,159.906),27:(-68.178,160.394),28:(-68.053,161.334),
    29:(-68.626,162.271),30:(-61.965,144.214),31:(-68.053,161.334),32:(-68.626,162.271),
    33:(-68.626,162.271),34:(-74.191,163.371),35:(-69.480,165.217),36:(-69.480,165.217),
    37:(-69.480,165.217),38:(-74.905,152.711),39:(-74.831,153.634),40:(-74.831,154.575),
    41:(-74.831,155.515),42:(-75.412,157.402),43:(-75.271,158.357),44:(-75.271,159.311),
    45:(-75.271,160.266),46:(-75.586,161.221),47:(-75.858,162.176),48:(-75.983,163.131),
    49:(-76.722,165.980),50:(-76.722,166.925),51:(-76.722,167.871),52:(-76.722,168.816),
    53:(-76.722,169.762),54:(-77.051,174.477),55:(-77.231,175.422),56:(-77.412,176.368),
    57:(-77.412,177.313),58:(-77.412,178.259),59:(-77.781,178.259),60:(-77.558,179.204),
    61:(-77.781,180.149),62:(-78.003,181.095),63:(-77.925,182.040),64:(-77.925,182.985),
    65:(-78.590,184.876),66:(-78.590,185.822),67:(-78.590,186.767),68:(-78.590,187.712),
    69:(-43.341,161.443),70:(-45.765,160.334),71:(-45.765,159.379),72:(-45.498,158.427),
    73:(-45.498,157.472),74:(-44.385,157.474),75:(-43.831,158.410),76:(-43.720,159.364),
    77:(-43.720,160.319),78:(-43.720,161.274),79:(-43.720,162.228),80:(-44.240,163.183),
    81:(-44.240,164.138),82:(-44.240,165.093),83:(-44.240,166.047),84:(-44.240,167.002),
    85:(-48.024,159.236),86:(-47.908,160.190),87:(-47.793,161.145),88:(-47.793,162.100),
    89:(-47.793,163.054),90:(-47.793,164.009),91:(-47.793,164.964),92:(-50.513,158.424),
    93:(-50.395,159.379),94:(-50.276,160.333),95:(-50.276,161.288),96:(-50.276,162.243),
    97:(-50.276,163.197),98:(-50.276,164.152),99:(-50.276,165.107),100:(-53.596,161.781),
    101:(-53.860,162.735),102:(-53.860,163.690),103:(-53.860,164.645),104:(-53.860,165.599),
    105:(-54.399,166.554),106:(-54.399,167.509),107:(-54.399,168.464),108:(-54.399,169.418),
    109:(-54.399,170.373),110:(-55.471,172.282),111:(-55.829,173.237),112:(-56.188,174.192),
    113:(-62.994,143.259),114:(72.803,79.514),115:(143.600,52.809),116:(243.440,52.712),
    117:(303.420,52.788),118:(363.430,52.817),
}

BRANCHES_RAW = [
    (1,2),(1,3),(4,5),(3,5),(5,6),(6,7),(8,9),(8,5),(9,10),(4,11),(5,11),(11,12),
    (2,12),(3,12),(7,12),(11,13),(12,14),(13,15),(14,15),(12,16),(15,17),(16,17),
    (17,18),(18,19),(19,20),(15,19),(20,21),(21,22),(22,23),(23,24),(23,25),(26,25),
    (25,27),(27,28),(28,29),(30,17),(8,30),(26,30),(17,31),(29,31),(23,32),(31,32),
    (27,32),(15,33),(19,34),(35,36),(35,37),(33,37),(34,36),(34,37),(38,37),(37,39),
    (37,40),(30,38),(39,40),(40,41),(40,42),(41,42),(43,44),(34,43),(44,45),(45,46),
    (46,47),(46,48),(47,49),(42,49),(45,49),(48,49),(49,50),(49,51),(51,52),(52,53),
    (53,54),(49,54),(54,55),(54,56),(55,56),(56,57),(50,57),(56,58),(51,58),(54,59),
    (56,59),(55,59),(59,60),(59,61),(60,61),(60,62),(61,62),(63,59),(63,64),(64,61),
    (38,65),(64,65),(49,66),(62,66),(62,67),(65,66),(66,67),(65,68),(47,69),(49,69),
    (68,69),(24,70),(70,71),(24,72),(71,72),(71,73),(70,74),(70,75),(69,75),(74,75),
    (76,77),(69,77),(75,77),(77,78),(78,79),(77,80),(79,80),(68,81),(81,80),(77,82),
    (82,83),(83,84),(83,85),(84,85),(85,86),(86,87),(85,88),(85,89),(88,89),(89,90),
    (90,91),(89,92),(91,92),(92,93),(92,94),(93,94),(94,95),(80,96),(82,96),(94,96),
    (80,97),(80,98),(80,99),(92,100),(94,100),(95,96),(96,97),(98,100),(99,100),
    (100,101),(92,102),(101,102),(100,103),(100,104),(103,104),(103,105),(100,106),
    (104,105),(105,106),(105,107),(105,108),(106,107),(108,109),(103,110),(109,110),
    (110,111),(110,112),(17,113),(32,113),(32,114),(27,115),(114,115),(68,116),
    (12,117),(75,118),(76,118),
]
seen, BRANCHES = set(), []
for a,b in BRANCHES_RAW:
    k = (min(a,b),max(a,b))
    if k not in seen:
        seen.add(k); BRANCHES.append((a,b))
BRANCHES = BRANCHES[:186]
N_BRANCHES = len(BRANCHES)

GEN_BUSES = {1,4,6,8,10,12,15,18,19,24,25,26,27,31,32,34,36,40,42,46,49,
             54,55,56,59,61,62,65,66,69,70,72,73,74,76,77,80,85,87,89,
             90,91,92,99,100,103,104,105,107,110,111,112,116}

def kv(b):
    return 345.0 if b in {1,2,3,4,5,6,7,8,9,10,38,65,68,69} else 138.0

def bus_row(base_id, b, noise=0.0):
    v  = round(np.clip(1.0 + np.random.normal(0,0.02) + noise, 0.90, 1.10), 4)
    va = round(np.random.uniform(-25,25), 4)
    pg = round(np.random.uniform(60,350),2) if b in GEN_BUSES else 0.0
    qg = round(np.random.uniform(-30,120),2) if b in GEN_BUSES else 0.0
    pd = round(np.random.uniform(15,180),2)
    qd = round(np.random.uniform(3,70),2)
    x,y = BUS_COORDS[b]
    return (base_id, b, v, va, pg, qg, pd, qd, kv(b), x, y)

def branch_row(base_id, line_id, fb, tb, vio_boost=0.0):
    rate = round(np.random.uniform(200,600),1)
    load = np.clip(np.random.uniform(0.15,0.80) + vio_boost, 0.01, 1.30)
    mva  = round(rate*load, 2)
    pf   = round(mva*np.random.uniform(0.88,0.98), 2)
    qf   = round(np.sqrt(max(0, mva**2-pf**2)), 2)
    vio  = round((mva/rate)*100, 2)
    ll   = round(load, 4)
    return (base_id, line_id, fb, tb, pf, qf, mva, rate, vio, ll)

OUTAGES = {
    1:(35,35,37), 2:(56,55,56), 3:(90,55,56),
    4:(100,77,82), 5:(101,100,101),
}

if os.path.exists(DB_PATH): os.remove(DB_PATH)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ── BaseBusData ────────────────────────────────────────────────────────────────
c.execute("""CREATE TABLE BaseBusData(
    base_case_id INT, BUS_NUMBER INT, VM REAL, VA REAL,
    PG REAL, QG REAL, PD REAL, QD REAL, BASE_KV REAL,
    x_coord REAL, y_coord REAL)""")
rows = [bus_row(42,b) for b in range(1,119)]
c.executemany("INSERT INTO BaseBusData VALUES(?,?,?,?,?,?,?,?,?,?,?)", rows)
print(f"BaseBusData: {len(rows)} buses")

# ── BaseBranchData ─────────────────────────────────────────────────────────────
c.execute("""CREATE TABLE BaseBranchData(
    base_case_id INT, LINE_ID INT, FROM_BUS INT, TO_BUS INT,
    PF REAL, QF REAL, MVA REAL, RATE REAL, VIO REAL, LOAD_LEVEL REAL)""")
rows = [branch_row(42,i+1,fb,tb) for i,(fb,tb) in enumerate(BRANCHES)]
c.executemany("INSERT INTO BaseBranchData VALUES(?,?,?,?,?,?,?,?,?,?)", rows)
print(f"BaseBranchData: {len(rows)} branches")

# ── ContingencyScenarios ───────────────────────────────────────────────────────
c.execute("CREATE TABLE ContingencyScenarios(base_case_id INT, name TEXT)")
c.executemany("INSERT INTO ContingencyScenarios VALUES(?,?)", [
    (42,"CA_0_bus118_42"),(43,"CA_1_bus118_43"),(44,"CA_2_bus118_44"),
    (45,"CA_3_bus118_45"),(46,"CA_4_bus118_46"),
])

# ── ContingencyCases ───────────────────────────────────────────────────────────
c.execute("CREATE TABLE ContingencyCases(base_case_id INT, contingency_case_id INT, filename TEXT)")
c.executemany("INSERT INTO ContingencyCases VALUES(?,?,?)", [
    (0,1,"branch_56_outage.raw"),(0,2,"branch_90_outage.raw"),
    (0,3,"branch_123_outage.raw"),(0,4,"branch_124_outage.raw"),
    (0,5,"branch_158_outage.raw"),
])

# ── ContingencyBusData ─────────────────────────────────────────────────────────
c.execute("""CREATE TABLE ContingencyBusData(
    base_case_id INT, contingency_case_id INT,
    BUS_NUMBER INT, VM REAL, VA REAL,
    PG REAL, QG REAL, PD REAL, QD REAL)""")
rows = []
for cid in range(1,6):
    for b in range(1,119):
        r = bus_row(0, b, noise=-0.02)
        rows.append((0, cid, b, r[2], r[3], r[4], r[5], r[6], r[7]))
c.executemany("INSERT INTO ContingencyBusData VALUES(?,?,?,?,?,?,?,?,?)", rows)
print(f"ContingencyBusData: {len(rows)} rows")

# ── ContingencyBranchData ──────────────────────────────────────────────────────
c.execute("""CREATE TABLE ContingencyBranchData(
    base_case_id INT, contingency_case_id INT, BRANCH_NUMBER INT,
    FROM_BUS INT, TO_BUS INT,
    PF REAL, QF REAL, MVA REAL, RATE REAL, VIO REAL, LOAD_LEVEL REAL)""")
rows = []
for cid in range(1,6):
    tripped_idx = OUTAGES[cid][0]
    for i,(fb,tb) in enumerate(BRANCHES):
        boost = 0.3 if abs(i - tripped_idx) <= 4 else 0.0
        if i == tripped_idx:
            rows.append((0,cid,i+1,fb,tb,0,0,0,300,0,0))
        else:
            r = branch_row(0,i+1,fb,tb,vio_boost=boost)
            rows.append((0,cid)+r[1:])
c.executemany("INSERT INTO ContingencyBranchData VALUES(?,?,?,?,?,?,?,?,?,?,?)", rows)
print(f"ContingencyBranchData: {len(rows)} rows")

# ── SLR_Cases / DLR_Cases ──────────────────────────────────────────────────────
for tbl in ("SLR_Cases","DLR_Cases"):
    c.execute(f"CREATE TABLE {tbl}(base_case_id INT, contingency_case_id INT)")
    c.executemany(f"INSERT INTO {tbl} VALUES(?,?)", [(42,cid) for cid in [56,90,123,124,158]])

# ── SLR_Buses / DLR_Buses ─────────────────────────────────────────────────────
for tbl in ("SLR_Buses","DLR_Buses"):
    c.execute(f"""CREATE TABLE {tbl}(
        base_case_id INT, contingency_case_id INT,
        BUS_NUMBER INT, VM REAL, VA REAL,
        PG REAL, QG REAL, PD REAL, QD REAL)""")
    rows = []
    for cid in [56,90,123,124,158]:
        noise = 0.01 if tbl.startswith("DLR") else -0.01
        for b in range(1,119):
            r = bus_row(42,b,noise=noise)
            rows.append((42,cid,b,r[2],r[3],r[4],r[5],r[6],r[7]))
    c.executemany(f"INSERT INTO {tbl} VALUES(?,?,?,?,?,?,?,?,?)", rows)
    print(f"{tbl}: {len(rows)} rows")

# ── SLR_Branches / DLR_Branches ───────────────────────────────────────────────
for tbl,boost in (("SLR_Branches",0.05),("DLR_Branches",-0.05)):
    c.execute(f"""CREATE TABLE {tbl}(
        base_case_id INT, contingency_case_id INT, LINE_ID INT,
        FROM_BUS INT, TO_BUS INT,
        PF REAL, QF REAL, MVA REAL, RATE REAL, VIO REAL, LOAD_LEVEL REAL)""")
    rows = []
    for cid in [56,90,123,124,158]:
        for i,(fb,tb) in enumerate(BRANCHES):
            r = branch_row(42,i+1,fb,tb,vio_boost=boost)
            rows.append((42,cid)+r[1:])
    c.executemany(f"INSERT INTO {tbl} VALUES(?,?,?,?,?,?,?,?,?,?,?)", rows)
    print(f"{tbl}: {len(rows)} rows")

# ── SLR_Generator / DLR_Generator ─────────────────────────────────────────────
# GEN_ADJ = how much MW this generator is re-dispatched
for tbl,scale in (("SLR_Generator",1.0),("DLR_Generator",0.7)):
    c.execute(f"""CREATE TABLE {tbl}(
        base_case_id INT, contingency_case_id INT,
        BUS_NUMBER INT, GEN_INI REAL, GEN_NEW REAL, GEN_ADJ REAL)""")
    rows = []
    gen_list = sorted(GEN_BUSES)
    for cid in [56,90,123,124,158]:
        # pick 6-10 generators to re-dispatch per case
        np.random.seed(cid)
        redispatch = np.random.choice(gen_list, size=np.random.randint(6,11), replace=False)
        for bus in redispatch:
            ini  = round(np.random.uniform(60,300),2)
            adj  = round(np.random.uniform(-80,120)*scale, 2)
            new  = round(ini+adj, 2)
            rows.append((42, cid, bus, ini, new, adj))
    c.executemany(f"INSERT INTO {tbl} VALUES(?,?,?,?,?,?)", rows)
    print(f"{tbl}: {len(rows)} rows")

# ── SLR_Load / DLR_Load ───────────────────────────────────────────────────────
for tbl,scale in (("SLR_Load",1.0),("DLR_Load",0.6)):
    c.execute(f"""CREATE TABLE {tbl}(
        base_case_id INT, contingency_case_id INT,
        BUS_NUMBER INT, LOAD_INI REAL, LOAD_NEW REAL, LOAD_ADJ REAL)""")
    rows = []
    all_buses = list(range(1,119))
    for cid in [56,90,123,124,158]:
        np.random.seed(cid+1000)
        shed_buses = np.random.choice(all_buses, size=np.random.randint(3,8), replace=False)
        for bus in shed_buses:
            ini = round(np.random.uniform(20,150),2)
            adj = round(np.random.uniform(5,40)*scale, 2)
            new = round(ini - adj, 2)
            rows.append((42, cid, bus, ini, new, adj))
    c.executemany(f"INSERT INTO {tbl} VALUES(?,?,?,?,?,?)", rows)
    print(f"{tbl}: {len(rows)} rows")

conn.commit()
conn.close()

size_kb = os.path.getsize(DB_PATH)//1024
print(f"\ndata.db created — {size_kb} KB, all tables ready.")
