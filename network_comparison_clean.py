"""
CLEAN NETWORK COMPARISON - Simple side-by-side comparison
"""
import pandas as pd
import plotly.graph_objects as go


def create_clean_network_comparison(case_id, contingency_id, get_sqlite_connection_func, create_network_graph_func):
    """
    Simple, clean network comparison - just two networks side-by-side
    """
    try:
        print(f"\n{'='*80}")
        print(f"CLEAN COMPARISON: Base {case_id} vs Contingency {contingency_id}")
        print(f"{'='*80}\n")
        
        # IEEE 118-bus system coordinates
        bus_coordinates = {
            1: (-47.50737232, 165.09677911), 2: (-47.48101205, 188.96190091), 3: (-33.74294251, 148.20627117),
            4: (6.48813946, 156.95036981), 5: (-13.30543962, 134.37167744), 6: (-22.67062556, 164.45228095),
            7: (-22.75367467, 181.34579360), 8: (-21.52562388, 123.36119999), 9: (-16.54981411, 79.24030951),
            10: (-16.35246374, 42.49273424), 11: (-5.75612464, 178.52208273), 12: (-27.70634892, 195.58634975),
            13: (18.12553656, 170.11451904), 14: (32.26863246, 191.63339926), 15: (83.52070213, 156.18482592),
            16: (25.52092120, 182.22133529), 17: (81.91702528, 132.27500498), 18: (114.95399518, 144.35913961),
            19: (132.45554767, 154.00832093), 20: (152.04689697, 136.14816271), 21: (162.21549628, 117.80060459),
            22: (172.00124178, 94.42349513), 23: (175.96082007, 72.67303169), 24: (203.13490349, 61.58709027),
            25: (175.96839147, 43.69050772), 26: (175.59642041, 28.49215735), 27: (149.16729068, 47.56554191),
            28: (116.63798923, 57.32021278), 29: (107.03080234, 79.15182492), 30: (78.70902689, 120.94132802),
            31: (97.12404608, 97.70937949), 32: (142.13268341, 84.25494148), 33: (141.43463138, 177.59428262),
            34: (195.06095237, 196.66376940), 35: (219.34234996, 179.91195434), 36: (234.52352777, 201.92229117),
            37: (192.78789306, 173.97901890), 38: (192.41147717, 156.11220325), 39: (167.32266984, 196.00796185),
            40: (180.77963360, 212.28654704), 41: (188.48483059, 234.53394681), 42: (221.25904878, 255.80463146),
            43: (231.88730044, 231.61581272), 44: (311.95643780, 192.12025597), 45: (328.43153139, 219.14217775),
            46: (334.23898644, 193.61890383), 47: (362.95860866, 199.40754204), 48: (352.66259702, 211.91348941),
            49: (375.05566831, 226.63506386), 50: (399.88705507, 234.52473184), 51: (375.86714648, 247.36935552),
            52: (372.14976767, 267.14514221), 53: (385.87924835, 278.49321727), 54: (401.72083562, 283.05240782),
            55: (436.88027147, 265.80466838), 56: (422.76888711, 250.52309298), 57: (415.57744017, 227.26049372),
            58: (401.80009858, 255.18223303), 59: (499.29346739, 275.82825642), 60: (465.15213230, 224.19255783),
            61: (479.68914465, 207.95495520), 62: (453.87473361, 203.74396070), 63: (506.34607499, 261.33459544),
            64: (480.78284514, 190.20898638), 65: (380.81932556, 179.15545823), 66: (381.19605808, 193.75789201),
            67: (420.03784937, 209.07335245), 68: (367.00248284, 108.00082662), 69: (359.64296413, 97.40331247),
            70: (331.10879924, 100.78968465), 71: (287.73075214, 98.27500931), 72: (244.81861363, 90.84031413),
            73: (287.85640365, 115.75326771), 74: (342.09009396, 63.94032378), 75: (367.02346517, 71.89136259),
            76: (382.69432165, 47.05825230), 77: (394.64903866, 68.65304881), 78: (392.59028168, 83.57682964),
            79: (405.36681833, 90.09630124), 80: (425.34492877, 89.15119980), 81: (426.27896208, 103.50284036),
            82: (407.85864971, 54.81134225), 83: (407.93776364, 38.58419738), 84: (396.50824340, 30.32411768),
            85: (408.05399274, 19.56267058), 86: (389.92343368, 9.07376983), 87: (390.05185363, 1.10293045),
            88: (407.77953579, -2.22979699), 89: (431.87412088, 8.28161104), 90: (441.36779177, -16.61974073),
            91: (453.99085787, -3.58352413), 92: (448.47534763, 21.75441929), 93: (432.11439280, 30.46671809),
            94: (441.74187365, 38.71703064), 95: (449.19225653, 49.33685405), 96: (427.60372707, 60.65346602),
            97: (437.38396617, 74.08349415), 98: (460.56415057, 69.33118910), 99: (477.00421933, 77.99172200),
            100: (463.20421152, 43.27047649), 101: (476.42405056, 25.44249556), 102: (466.56118136, 12.67878248),
            103: (490.61181427, 24.27336757), 104: (528.52301133, 39.34701189), 105: (542.45975926, 20.51594453),
            106: (545.23070003, 57.16424896), 107: (571.42717605, 41.53290031), 108: (539.21901852, -3.63333660),
            109: (527.77958441, 2.59025109), 110: (498.97616514, -2.43197702), 111: (504.53830962, -25.19402480),
            112: (492.82901715, -25.10282500), 113: (107.17908940, 128.81269497), 114: (124.98913133, 74.46140021),
            115: (132.87994761, 58.62643901), 116: (374.08281651, 122.56293846), 117: (-26.12054262, 217.68970209),
            118: (363.42982092, 52.81659048)
        }
        
        # Get database connection
        conn = get_sqlite_connection_func()
        
        # Query base case data
        base_buses = pd.read_sql_query(
            f"SELECT Bus_Number as BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD FROM BaseBusData WHERE base_case_id = {case_id}", 
            conn
        )
        base_branches = pd.read_sql_query(
            f"SELECT from_bus as FROM_BUS, to_bus as TO_BUS, pf as PF, qf as QF, mva as MVA, rate as RATE, vio as VIO FROM BaseBranchData WHERE base_case_id = {case_id}", 
            conn
        )
        
        # Query contingency case data
        cont_buses = pd.read_sql_query(
            f"SELECT bus_number as BUS_NUMBER, vm as VM, va as VA, base_kv as BASE_KV, pg as PG, qg as QG, pd as PD, qd as QD FROM ContingencyBusData WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        cont_branches = pd.read_sql_query(
            f"SELECT from_bus as FROM_BUS, to_bus as TO_BUS, pf as PF, qf as QF, mva as MVA, rate as RATE, vio as VIO FROM ContingencyBranchData WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        
        conn.close()
        
        # Add coordinates to bus data
        base_buses['x_coord'] = base_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[0])
        base_buses['y_coord'] = base_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[1])
        cont_buses['x_coord'] = cont_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[0])
        cont_buses['y_coord'] = cont_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[1])
        
        print(f"✓ Loaded: Base ({len(base_buses)}B, {len(base_branches)}Br), Cont ({len(cont_buses)}B, {len(cont_branches)}Br)")
        print(f"✓ Added coordinates to {len(base_buses)} base buses and {len(cont_buses)} contingency buses")
        
        # Create figures using working function
        base_fig = create_network_graph_func(
            buses=base_buses,
            branches=base_branches,
            title=f"Base {case_id}",
            min_load=base_branches['PF'].min() if not base_branches.empty else 0,
            max_load=base_branches['PF'].max() if not base_branches.empty else 100,
            case_id=0,
            tripped_branch_info=None
        )
        
        cont_fig = create_network_graph_func(
            buses=cont_buses,
            branches=cont_branches,
            title=f"Contingency {contingency_id}",
            min_load=cont_branches['PF'].min() if not cont_branches.empty else 0,
            max_load=cont_branches['PF'].max() if not cont_branches.empty else 100,
            case_id=contingency_id,
            tripped_branch_info=None
        )
        
        # Copy base figure completely
        combined = go.Figure(base_fig)
        
        # Offset contingency to the right (increased gap)
        x_offset = 900
        for trace in cont_fig.data:
            new_trace = go.Scatter(trace)
            if hasattr(trace, 'x') and trace.x:
                new_trace.x = [x + x_offset if x is not None else None for x in trace.x]
            if hasattr(trace, 'name'):
                new_trace.name = f"C:{trace.name}" if trace.name else "Cont"
            combined.add_trace(new_trace)
        
        # Extend x-axis
        if combined.layout.xaxis.range:
            combined.update_xaxes(range=[combined.layout.xaxis.range[0], combined.layout.xaxis.range[1] + x_offset])
        
        # Calculate comparison metrics
        base_total_load = base_buses['PD'].sum() if not base_buses.empty else 0
        cont_total_load = cont_buses['PD'].sum() if not cont_buses.empty else 0
        base_total_gen = base_buses['PG'].sum() if not base_buses.empty else 0
        cont_total_gen = cont_buses['PG'].sum() if not cont_buses.empty else 0
        base_violations = len(base_branches[base_branches['VIO'] >= 99.99]) if not base_branches.empty and 'VIO' in base_branches.columns else 0
        cont_violations = len(cont_branches[cont_branches['VIO'] >= 99.99]) if not cont_branches.empty and 'VIO' in cont_branches.columns else 0
        
        # Calculate max loading
        if not base_branches.empty and 'MVA' in base_branches.columns and 'RATE' in base_branches.columns:
            base_max_loading = (base_branches['MVA'] / base_branches['RATE'].replace(0, 1) * 100).max()
        else:
            base_max_loading = 0
            
        if not cont_branches.empty and 'MVA' in cont_branches.columns and 'RATE' in cont_branches.columns:
            cont_max_loading = (cont_branches['MVA'] / cont_branches['RATE'].replace(0, 1) * 100).max()
        else:
            cont_max_loading = 0
        
        # Create analysis text
        analysis_text = (
            f"<b>📊 COMPARISON ANALYSIS</b><br>"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
            f"<b>Generation:</b> Base: {base_total_gen:.1f} MW → Cont: {cont_total_gen:.1f} MW (Δ {cont_total_gen - base_total_gen:+.1f} MW)<br>"
            f"<b>Load Demand:</b> Base: {base_total_load:.1f} MW → Cont: {cont_total_load:.1f} MW (Δ {cont_total_load - base_total_load:+.1f} MW)<br>"
            f"<b>Line Violations:</b> Base: {base_violations} → Cont: {cont_violations} (Δ {cont_violations - base_violations:+d})<br>"
            f"<b>Max Loading:</b> Base: {base_max_loading:.1f}% → Cont: {cont_max_loading:.1f}% (Δ {cont_max_loading - base_max_loading:+.1f}%)<br>"
            f"<b>System Impact:</b> {'⚠️ <b>DEGRADED</b>' if cont_violations > base_violations else '✅ <b>STABLE</b>'} - "
            f"Contingency caused {cont_violations - base_violations if cont_violations > base_violations else 0} additional violations"
        )
        
        combined.update_layout(
            title={
                'text': f"<b>Base {case_id} (left) vs Contingency {contingency_id} (right)</b>",
                'font': {'color': 'white', 'size': 18}
            },
            width=1800,
            annotations=[
                dict(
                    text=analysis_text,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.12,
                    xanchor='center', yanchor='top',
                    showarrow=False,
                    font=dict(size=12, color='white', family='Courier New'),
                    align='left',
                    bgcolor='rgba(44, 62, 80, 0.9)',
                    bordercolor='#3498db',
                    borderwidth=2,
                    borderpad=10
                )
            ]
        )
        
        print(f"✓ Combined: {len(combined.data)} traces\n")
        return combined
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_clean_slr_dlr_comparison(case_id, contingency_id, get_sqlite_connection_func, create_network_graph_func):
    """
    Simple, clean SLR vs DLR network comparison - just two networks side-by-side
    For case 43 only
    """
    try:
        print(f"\n{'='*80}")
        print(f"CLEAN SLR/DLR COMPARISON: Case {case_id}, Contingency {contingency_id}")
        print(f"{'='*80}\n")
        
        # IEEE 118-bus system coordinates
        bus_coordinates = {
            1: (-47.50737232, 165.09677911), 2: (-47.48101205, 188.96190091), 3: (-33.74294251, 148.20627117),
            4: (6.48813946, 156.95036981), 5: (-13.30543962, 134.37167744), 6: (-22.67062556, 164.45228095),
            7: (-22.75367467, 181.34579360), 8: (-21.52562388, 123.36119999), 9: (-16.54981411, 79.24030951),
            10: (-16.35246374, 42.49273424), 11: (-5.75612464, 178.52208273), 12: (-27.70634892, 195.58634975),
            13: (18.12553656, 170.11451904), 14: (32.26863246, 191.63339926), 15: (83.52070213, 156.18482592),
            16: (25.52092120, 182.22133529), 17: (81.91702528, 132.27500498), 18: (114.95399518, 144.35913961),
            19: (132.45554767, 154.00832093), 20: (152.04689697, 136.14816271), 21: (162.21549628, 117.80060459),
            22: (172.00124178, 94.42349513), 23: (175.96082007, 72.67303169), 24: (203.13490349, 61.58709027),
            25: (175.96839147, 43.69050772), 26: (175.59642041, 28.49215735), 27: (149.16729068, 47.56554191),
            28: (116.63798923, 57.32021278), 29: (107.03080234, 79.15182492), 30: (78.70902689, 120.94132802),
            31: (97.12404608, 97.70937949), 32: (142.13268341, 84.25494148), 33: (141.43463138, 177.59428262),
            34: (195.06095237, 196.66376940), 35: (219.34234996, 179.91195434), 36: (234.52352777, 201.92229117),
            37: (192.78789306, 173.97901890), 38: (192.41147717, 156.11220325), 39: (167.32266984, 196.00796185),
            40: (180.77963360, 212.28654704), 41: (188.48483059, 234.53394681), 42: (221.25904878, 255.80463146),
            43: (231.88730044, 231.61581272), 44: (311.95643780, 192.12025597), 45: (328.43153139, 219.14217775),
            46: (334.23898644, 193.61890383), 47: (362.95860866, 199.40754204), 48: (352.66259702, 211.91348941),
            49: (375.05566831, 226.63506386), 50: (399.88705507, 234.52473184), 51: (375.86714648, 247.36935552),
            52: (372.14976767, 267.14514221), 53: (385.87924835, 278.49321727), 54: (401.72083562, 283.05240782),
            55: (436.88027147, 265.80466838), 56: (422.76888711, 250.52309298), 57: (415.57744017, 227.26049372),
            58: (401.80009858, 255.18223303), 59: (499.29346739, 275.82825642), 60: (465.15213230, 224.19255783),
            61: (479.68914465, 207.95495520), 62: (453.87473361, 203.74396070), 63: (506.34607499, 261.33459544),
            64: (480.78284514, 190.20898638), 65: (380.81932556, 179.15545823), 66: (381.19605808, 193.75789201),
            67: (420.03784937, 209.07335245), 68: (367.00248284, 108.00082662), 69: (359.64296413, 97.40331247),
            70: (331.10879924, 100.78968465), 71: (287.73075214, 98.27500931), 72: (244.81861363, 90.84031413),
            73: (287.85640365, 115.75326771), 74: (342.09009396, 63.94032378), 75: (367.02346517, 71.89136259),
            76: (382.69432165, 47.05825230), 77: (394.64903866, 68.65304881), 78: (392.59028168, 83.57682964),
            79: (405.36681833, 90.09630124), 80: (425.34492877, 89.15119980), 81: (426.27896208, 103.50284036),
            82: (407.85864971, 54.81134225), 83: (407.93776364, 38.58419738), 84: (396.50824340, 30.32411768),
            85: (408.05399274, 19.56267058), 86: (389.92343368, 9.07376983), 87: (390.05185363, 1.10293045),
            88: (407.77953579, -2.22979699), 89: (431.87412088, 8.28161104), 90: (441.36779177, -16.61974073),
            91: (453.99085787, -3.58352413), 92: (448.47534763, 21.75441929), 93: (432.11439280, 30.46671809),
            94: (441.74187365, 38.71703064), 95: (449.19225653, 49.33685405), 96: (427.60372707, 60.65346602),
            97: (437.38396617, 74.08349415), 98: (460.56415057, 69.33118910), 99: (477.00421933, 77.99172200),
            100: (463.20421152, 43.27047649), 101: (476.42405056, 25.44249556), 102: (466.56118136, 12.67878248),
            103: (490.61181427, 24.27336757), 104: (528.52301133, 39.34701189), 105: (542.45975926, 20.51594453),
            106: (545.23070003, 57.16424896), 107: (571.42717605, 41.53290031), 108: (539.21901852, -3.63333660),
            109: (527.77958441, 2.59025109), 110: (498.97616514, -2.43197702), 111: (504.53830962, -25.19402480),
            112: (492.82901715, -25.10282500), 113: (107.17908940, 128.81269497), 114: (124.98913133, 74.46140021),
            115: (132.87994761, 58.62643901), 116: (374.08281651, 122.56293846), 117: (-26.12054262, 217.68970209),
            118: (363.42982092, 52.81659048)
        }
        
        # Get database connection
        conn = get_sqlite_connection_func()
        
        # Query base case bus data (same for both SLR and DLR)
        base_buses = pd.read_sql_query(
            f"SELECT Bus_Number as BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD FROM BaseBusData WHERE base_case_id = {case_id}", 
            conn
        )
        
        # Query SLR branch data
        slr_branches = pd.read_sql_query(
            f"SELECT From_Bus as FROM_BUS, To_Bus as TO_BUS, PF, QF, MVA, RATE, VIO FROM SLRBranchData WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        
        # Query DLR branch data
        dlr_branches = pd.read_sql_query(
            f"SELECT From_Bus as FROM_BUS, To_Bus as TO_BUS, PF, QF, MVA, RATE, VIO FROM DLRBranchData WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        
        conn.close()
        
        # Add coordinates to bus data (same buses for both)
        base_buses['x_coord'] = base_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[0])
        base_buses['y_coord'] = base_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[1])
        
        print(f"✓ Loaded: Buses ({len(base_buses)}B), SLR ({len(slr_branches)}Br), DLR ({len(dlr_branches)}Br)")
        print(f"✓ Added coordinates to {len(base_buses)} buses")
        
        # Create figures using working function
        slr_fig = create_network_graph_func(
            buses=base_buses,
            branches=slr_branches,
            title=f"SLR - Case {case_id}, Cont {contingency_id}",
            min_load=slr_branches['PF'].min() if not slr_branches.empty else 0,
            max_load=slr_branches['PF'].max() if not slr_branches.empty else 100,
            case_id=0,
            tripped_branch_info=None
        )
        
        dlr_fig = create_network_graph_func(
            buses=base_buses,
            branches=dlr_branches,
            title=f"DLR - Case {case_id}, Cont {contingency_id}",
            min_load=dlr_branches['PF'].min() if not dlr_branches.empty else 0,
            max_load=dlr_branches['PF'].max() if not dlr_branches.empty else 100,
            case_id=contingency_id,
            tripped_branch_info=None
        )
        
        # Copy SLR figure completely
        combined = go.Figure(slr_fig)
        
        # Offset DLR to the right (same gap as base/contingency comparison)
        x_offset = 900
        for trace in dlr_fig.data:
            new_trace = go.Scatter(trace)
            if hasattr(trace, 'x') and trace.x:
                new_trace.x = [x + x_offset if x is not None else None for x in trace.x]
            if hasattr(trace, 'name'):
                new_trace.name = f"D:{trace.name}" if trace.name else "DLR"
            combined.add_trace(new_trace)
        
        # Extend x-axis
        if combined.layout.xaxis.range:
            combined.update_xaxes(range=[combined.layout.xaxis.range[0], combined.layout.xaxis.range[1] + x_offset])
        
        combined.update_layout(
            title=f"<b>SLR (left) vs DLR (right) - Case {case_id}, Contingency {contingency_id}</b>",
            width=1800
        )
        
        print(f"✓ Combined: {len(combined.data)} traces\n")
        return combined
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_clean_four_network_comparison(case_id, contingency_id, get_sqlite_connection_func, create_network_graph_func):
    """
    Comprehensive 4-network comparison for case 43:
    - Top Left: Base case
    - Top Right: Contingency case
    - Bottom Left: SLR with blue diamond generators
    - Bottom Right: DLR with green diamond generators
    """
    try:
        print(f"\n{'='*80}")
        print(f"4-NETWORK COMPARISON: Case {case_id}, Contingency {contingency_id}")
        print(f"{'='*80}\n")
        
        # IEEE 118-bus system coordinates
        bus_coordinates = {
            1: (-47.50737232, 165.09677911), 2: (-47.48101205, 188.96190091), 3: (-33.74294251, 148.20627117),
            4: (6.48813946, 156.95036981), 5: (-13.30543962, 134.37167744), 6: (-22.67062556, 164.45228095),
            7: (-22.75367467, 181.34579360), 8: (-21.52562388, 123.36119999), 9: (-16.54981411, 79.24030951),
            10: (-16.35246374, 42.49273424), 11: (-5.75612464, 178.52208273), 12: (-27.70634892, 195.58634975),
            13: (18.12553656, 170.11451904), 14: (32.26863246, 191.63339926), 15: (83.52070213, 156.18482592),
            16: (25.52092120, 182.22133529), 17: (81.91702528, 132.27500498), 18: (114.95399518, 144.35913961),
            19: (132.45554767, 154.00832093), 20: (152.04689697, 136.14816271), 21: (162.21549628, 117.80060459),
            22: (172.00124178, 94.42349513), 23: (175.96082007, 72.67303169), 24: (203.13490349, 61.58709027),
            25: (175.96839147, 43.69050772), 26: (175.59642041, 28.49215735), 27: (149.16729068, 47.56554191),
            28: (116.63798923, 57.32021278), 29: (107.03080234, 79.15182492), 30: (78.70902689, 120.94132802),
            31: (97.12404608, 97.70937949), 32: (142.13268341, 84.25494148), 33: (141.43463138, 177.59428262),
            34: (195.06095237, 196.66376940), 35: (219.34234996, 179.91195434), 36: (234.52352777, 201.92229117),
            37: (192.78789306, 173.97901890), 38: (192.41147717, 156.11220325), 39: (167.32266984, 196.00796185),
            40: (180.77963360, 212.28654704), 41: (188.48483059, 234.53394681), 42: (221.25904878, 255.80463146),
            43: (231.88730044, 231.61581272), 44: (311.95643780, 192.12025597), 45: (328.43153139, 219.14217775),
            46: (334.23898644, 193.61890383), 47: (362.95860866, 199.40754204), 48: (352.66259702, 211.91348941),
            49: (375.05566831, 226.63506386), 50: (399.88705507, 234.52473184), 51: (375.86714648, 247.36935552),
            52: (372.14976767, 267.14514221), 53: (385.87924835, 278.49321727), 54: (401.72083562, 283.05240782),
            55: (436.88027147, 265.80466838), 56: (422.76888711, 250.52309298), 57: (415.57744017, 227.26049372),
            58: (401.80009858, 255.18223303), 59: (499.29346739, 275.82825642), 60: (465.15213230, 224.19255783),
            61: (479.68914465, 207.95495520), 62: (453.87473361, 203.74396070), 63: (506.34607499, 261.33459544),
            64: (480.78284514, 190.20898638), 65: (380.81932556, 179.15545823), 66: (381.19605808, 193.75789201),
            67: (420.03784937, 209.07335245), 68: (367.00248284, 108.00082662), 69: (359.64296413, 97.40331247),
            70: (331.10879924, 100.78968465), 71: (287.73075214, 98.27500931), 72: (244.81861363, 90.84031413),
            73: (287.85640365, 115.75326771), 74: (342.09009396, 63.94032378), 75: (367.02346517, 71.89136259),
            76: (382.69432165, 47.05825230), 77: (394.64903866, 68.65304881), 78: (392.59028168, 83.57682964),
            79: (405.36681833, 90.09630124), 80: (425.34492877, 89.15119980), 81: (426.27896208, 103.50284036),
            82: (407.85864971, 54.81134225), 83: (407.93776364, 38.58419738), 84: (396.50824340, 30.32411768),
            85: (408.05399274, 19.56267058), 86: (389.92343368, 9.07376983), 87: (390.05185363, 1.10293045),
            88: (407.77953579, -2.22979699), 89: (431.87412088, 8.28161104), 90: (441.36779177, -16.61974073),
            91: (453.99085787, -3.58352413), 92: (448.47534763, 21.75441929), 93: (432.11439280, 30.46671809),
            94: (441.74187365, 38.71703064), 95: (449.19225653, 49.33685405), 96: (427.60372707, 60.65346602),
            97: (437.38396617, 74.08349415), 98: (460.56415057, 69.33118910), 99: (477.00421933, 77.99172200),
            100: (463.20421152, 43.27047649), 101: (476.42405056, 25.44249556), 102: (466.56118136, 12.67878248),
            103: (490.61181427, 24.27336757), 104: (528.52301133, 39.34701189), 105: (542.45975926, 20.51594453),
            106: (545.23070003, 57.16424896), 107: (571.42717605, 41.53290031), 108: (539.21901852, -3.63333660),
            109: (527.77958441, 2.59025109), 110: (498.97616514, -2.43197702), 111: (504.53830962, -25.19402480),
            112: (492.82901715, -25.10282500), 113: (107.17908940, 128.81269497), 114: (124.98913133, 74.46140021),
            115: (132.87994761, 58.62643901), 116: (374.08281651, 122.56293846), 117: (-26.12054262, 217.68970209),
            118: (363.42982092, 52.81659048)
        }
        
        # Get database connection
        conn = get_sqlite_connection_func()
        
        # ===== Query all network data =====
        # Base case
        base_buses = pd.read_sql_query(
            f"SELECT Bus_Number as BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD FROM BaseBusData WHERE base_case_id = {case_id}", 
            conn
        )
        base_branches = pd.read_sql_query(
            f"SELECT from_bus as FROM_BUS, to_bus as TO_BUS, pf as PF, qf as QF, mva as MVA, rate as RATE, vio as VIO FROM BaseBranchData WHERE base_case_id = {case_id}", 
            conn
        )
        
        # Contingency case
        cont_buses = pd.read_sql_query(
            f"SELECT bus_number as BUS_NUMBER, vm as VM, va as VA, base_kv as BASE_KV, pg as PG, qg as QG, pd as PD, qd as QD FROM ContingencyBusData WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        cont_branches = pd.read_sql_query(
            f"SELECT from_bus as FROM_BUS, to_bus as TO_BUS, pf as PF, qf as QF, mva as MVA, rate as RATE, vio as VIO FROM ContingencyBranchData WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        
        # SLR case (uses base buses but SLR branches)
        slr_branches = pd.read_sql_query(
            f"SELECT From_Bus as FROM_BUS, To_Bus as TO_BUS, PF, QF, MVA, RATE, VIO FROM SLRBranchData WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        
        # DLR case (uses base buses but DLR branches)
        dlr_branches = pd.read_sql_query(
            f"SELECT From_Bus as FROM_BUS, To_Bus as TO_BUS, PF, QF, MVA, RATE, VIO FROM DLRBranchData WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        
        # ===== Query generator data =====
        # SLR generators
        slr_gen = pd.read_sql_query(
            f"SELECT BUS_NUMBER, GEN_INI, GEN_NEW, GEN_ADJ FROM SLR_Generator WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        
        # DLR generators
        dlr_gen = pd.read_sql_query(
            f"SELECT BUS_NUMBER, GEN_INI, GEN_NEW, GEN_ADJ FROM DLR_Generator WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}", 
            conn
        )
        
        conn.close()
        
        print(f"[OK] Loaded Base: {len(base_buses)}B, {len(base_branches)}Br")
        print(f"[OK] Loaded Cont: {len(cont_buses)}B, {len(cont_branches)}Br")
        print(f"[OK] Loaded SLR: {len(base_buses)}B, {len(slr_branches)}Br, {len(slr_gen)} generators")
        print(f"[OK] Loaded DLR: {len(base_buses)}B, {len(dlr_branches)}Br, {len(dlr_gen)} generators")
        
        # Debug: Check VIO values from database
        print(f"\n{'='*80}")
        print(f"DATABASE VIO VALUES - Case {case_id}, Contingency {contingency_id}")
        print(f"{'='*80}")
        
        if not slr_branches.empty and 'VIO' in slr_branches.columns:
            slr_vio_high = slr_branches[slr_branches['VIO'] >= 100]
            print(f"📊 SLR Branch Data:")
            print(f"   • Total branches: {len(slr_branches)}")
            print(f"   • VIO range: min={slr_branches['VIO'].min():.2f}%, max={slr_branches['VIO'].max():.2f}%, mean={slr_branches['VIO'].mean():.2f}%")
            print(f"   • Violations (VIO >= 100%): {len(slr_vio_high)} branches")
            if len(slr_vio_high) > 0:
                print(f"   - Violated branches (first 5):")
                for idx, row in slr_vio_high.head(5).iterrows():
                    print(f"      - Branch {int(row['FROM_BUS'])}-{int(row['TO_BUS'])}: VIO={row['VIO']:.2f}%, MVA={row['MVA']:.2f}, RATE={row['RATE']:.2f}")
            else:
                print(f"   - [OK] NO VIOLATIONS in SLR data (all VIO < 100%)")
        else:
            print(f"[WARN] SLR branches empty or no VIO column")
            
        if not dlr_branches.empty and 'VIO' in dlr_branches.columns:
            dlr_vio_high = dlr_branches[dlr_branches['VIO'] >= 100]
            print(f"\n📊 DLR Branch Data:")
            print(f"   • Total branches: {len(dlr_branches)}")
            print(f"   • VIO range: min={dlr_branches['VIO'].min():.2f}%, max={dlr_branches['VIO'].max():.2f}%, mean={dlr_branches['VIO'].mean():.2f}%")
            print(f"   • Violations (VIO >= 100%): {len(dlr_vio_high)} branches")
            if len(dlr_vio_high) > 0:
                print(f"   - Violated branches (first 5):")
                for idx, row in dlr_vio_high.head(5).iterrows():
                    print(f"      - Branch {int(row['FROM_BUS'])}-{int(row['TO_BUS'])}: VIO={row['VIO']:.2f}%, MVA={row['MVA']:.2f}, RATE={row['RATE']:.2f}")
            else:
                print(f"   - [OK] NO VIOLATIONS in DLR data (all VIO < 100%)")
        else:
            print(f"[WARN] DLR branches empty or no VIO column")
            
        print(f"{'='*80}\n")
        
        # ===== CHECK IF SLR/DLR DATA EXISTS =====
        # If no SLR/DLR data, fall back to 2-network comparison (Base vs Contingency)
        if slr_branches.empty and dlr_branches.empty:
            print("[WARN] No SLR/DLR data found - creating Base vs Contingency comparison only")
            
            # Detect tripped branch (specific contingency mappings)
            contingency_tripped_map = {
                55: (35, 37),   # Branch 56: from_bus 35 to_bus 37
                89: (55, 56),   # Branch 90: from_bus 55 to_bus 56
                122: (77, 80),  # Branch 123: from_bus 77 to_bus 80
                123: (77, 82),  # Branch 124: from_bus 77 to_bus 82
                157: (100, 101) # Branch 158: from_bus 100 to_bus 101
            }
            
            tripped_branch_info = None
            if contingency_id in contingency_tripped_map:
                from_bus, to_bus = contingency_tripped_map[contingency_id]
                tripped_branch_info = {
                    'from_bus': from_bus,
                    'to_bus': to_bus,
                    'branch': f'{from_bus}-{to_bus}'  # Add 'branch' key for compatibility with data_viz_fall.py
                }
                print(f"  [OK] Tripped branch for contingency {contingency_id} (fallback): Bus {from_bus} -> Bus {to_bus}")
            else:
                print(f"  [INFO] No tripped branch mapping for contingency {contingency_id} (fallback)")
            
            # Add coordinates to bus data
            base_buses['x_coord'] = base_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[0])
            base_buses['y_coord'] = base_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[1])
            cont_buses['x_coord'] = cont_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[0])
            cont_buses['y_coord'] = cont_buses['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[1])
            
            # Create base and contingency figures
            base_fig = create_network_graph_func(
                buses=base_buses,
                branches=base_branches,
                title=f"Base {case_id}",
                min_load=base_branches['PF'].min() if not base_branches.empty else 0,
                max_load=base_branches['PF'].max() if not base_branches.empty else 100,
                case_id=0,
                tripped_branch_info=None
            )
            
            cont_fig = create_network_graph_func(
                buses=cont_buses,
                branches=cont_branches,
                title=f"Contingency {contingency_id}",
                min_load=cont_branches['PF'].min() if not cont_branches.empty else 0,
                max_load=cont_branches['PF'].max() if not cont_branches.empty else 100,
                case_id=contingency_id,
                tripped_branch_info=tripped_branch_info  # Pass tripped branch info for red cross marker
            )
            
            # Copy base figure
            combined = go.Figure(base_fig)
            
            # Offset contingency to the right
            x_offset = 900
            for trace in cont_fig.data:
                new_trace = go.Scatter(trace)
                if hasattr(trace, 'x') and trace.x:
                    new_trace.x = [x + x_offset if x is not None else None for x in trace.x]
                if hasattr(trace, 'name'):
                    new_trace.name = f"Cont:{trace.name}" if trace.name else "Cont"
                combined.add_trace(new_trace)
            
            # Extend x-axis
            if combined.layout.xaxis.range:
                combined.update_xaxes(range=[combined.layout.xaxis.range[0], combined.layout.xaxis.range[1] + x_offset])
            
            # Calculate comparison metrics
            base_total_load = base_buses['PD'].sum() if not base_buses.empty else 0
            cont_total_load = cont_buses['PD'].sum() if not cont_buses.empty else 0
            base_total_gen = base_buses['PG'].sum() if not base_buses.empty else 0
            cont_total_gen = cont_buses['PG'].sum() if not cont_buses.empty else 0
            base_loss = base_total_gen - base_total_load
            cont_loss = cont_total_gen - cont_total_load
            base_violations = len(base_branches[base_branches['VIO'] >= 99.99]) if not base_branches.empty and 'VIO' in base_branches.columns else 0
            cont_violations = len(cont_branches[cont_branches['VIO'] >= 99.99]) if not cont_branches.empty and 'VIO' in cont_branches.columns else 0
            
            # Calculate max loading
            if not base_branches.empty and 'MVA' in base_branches.columns and 'RATE' in base_branches.columns:
                base_max_loading = (base_branches['MVA'] / base_branches['RATE'].replace(0, 1) * 100).max()
            else:
                base_max_loading = 0
                
            if not cont_branches.empty and 'MVA' in cont_branches.columns and 'RATE' in cont_branches.columns:
                cont_max_loading = (cont_branches['MVA'] / cont_branches['RATE'].replace(0, 1) * 100).max()
            else:
                cont_max_loading = 0
            
            # Create analysis text
            analysis_text = (
                f"<b>📊 NETWORK COMPARISON ANALYSIS</b> (SLR/DLR data not available)<br>"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
                f"<b>Generation:</b> Base: {base_total_gen:.1f} MW → Cont: {cont_total_gen:.1f} MW (Δ {cont_total_gen - base_total_gen:+.1f} MW, "
                f"{((cont_total_gen - base_total_gen) / base_total_gen * 100) if base_total_gen > 0 else 0:+.2f}%)<br>"
                f"<b>Load Demand:</b> Base: {base_total_load:.1f} MW → Cont: {cont_total_load:.1f} MW (Δ {cont_total_load - base_total_load:+.1f} MW, "
                f"{((cont_total_load - base_total_load) / base_total_load * 100) if base_total_load > 0 else 0:+.2f}%)<br>"
                f"<b>System Loss:</b> Base: {base_loss:.1f} MW → Cont: {cont_loss:.1f} MW (Δ {cont_loss - base_loss:+.1f} MW, "
                f"{((cont_loss - base_loss) / base_loss * 100) if base_loss > 0 else 0:+.2f}%)<br>"
                f"<b>Line Violations:</b> Base: {base_violations} → Cont: {cont_violations} (Δ {cont_violations - base_violations:+d} violations)<br>"
                f"<b>Max Line Loading:</b> Base: {base_max_loading:.1f}% → Cont: {cont_max_loading:.1f}% (Δ {cont_max_loading - base_max_loading:+.1f}%)<br>"
                f"<b>Contingency Impact:</b> {'⚠️ <b>CRITICAL</b> - System degraded significantly' if cont_violations > base_violations + 2 else '⚠️ <b>MODERATE</b> - System slightly degraded' if cont_violations > base_violations else '✅ <b>STABLE</b> - System remains stable'} | "
                f"{'Requires mitigation strategy' if cont_violations > base_violations else 'No immediate action needed'}"
            )
            
            combined.update_layout(
                title={
                    'text': f"<b>Network Comparison - Base {case_id} (left) vs Contingency {contingency_id} (right)</b><br>"
                            f"<sub>Note: SLR/DLR comparison data not available for this case</sub>",
                    'font': {'color': 'white', 'size': 18}
                },
                width=1800,
                height=800,
                annotations=[
                    dict(
                        text=analysis_text,
                        xref="paper", yref="paper",
                        x=0.5, y=-0.15,
                        xanchor='center', yanchor='top',
                        showarrow=False,
                        font=dict(size=11, color='white', family='Courier New'),
                        align='left',
                        bgcolor='rgba(44, 62, 80, 0.95)',
                        bordercolor='#3498db',
                        borderwidth=2,
                        borderpad=10
                    )
                ]
            )
            
            print(f"✓ Created 2-network comparison (Base vs Contingency only)")
            return combined
        
        # ===== CONTINUE WITH 4-NETWORK COMPARISON IF SLR/DLR DATA EXISTS =====
        
        # Add coordinates to all bus data
        for df in [base_buses, cont_buses]:
            if not df.empty:
                df['x_coord'] = df['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[0])
                df['y_coord'] = df['BUS_NUMBER'].map(lambda x: bus_coordinates.get(int(x), (0, 0))[1])
        
        # Create copies for SLR and DLR (they share base bus topology)
        slr_buses = base_buses.copy()
        dlr_buses = base_buses.copy()
        
        # ===== Detect tripped branch (specific contingency mappings) =====
        # Map contingency IDs to their tripped branches (contingency_id: (from_bus, to_bus))
        contingency_tripped_map = {
            55: (35, 37),   # Branch 56: from_bus 35 to_bus 37
            89: (55, 56),   # Branch 90: from_bus 55 to_bus 56
            122: (77, 80),  # Branch 123: from_bus 77 to_bus 80
            123: (77, 82),  # Branch 124: from_bus 77 to_bus 82
            157: (100, 101) # Branch 158: from_bus 100 to_bus 101
        }
        
        tripped_branch_info = None
        if contingency_id in contingency_tripped_map:
            from_bus, to_bus = contingency_tripped_map[contingency_id]
            tripped_branch_info = {
                'from_bus': from_bus,
                'to_bus': to_bus,
                'branch': f'{from_bus}-{to_bus}'  # Add 'branch' key for compatibility with data_viz_fall.py
            }
            print(f"  [OK] Tripped branch for contingency {contingency_id}: Bus {from_bus} -> Bus {to_bus}")
        else:
            print(f"  [INFO] No tripped branch mapping for contingency {contingency_id}")
        
        # ===== Create 4 individual network figures =====
        base_fig = create_network_graph_func(
            buses=base_buses,
            branches=base_branches,
            title=f"Base {case_id}",
            min_load=base_branches['PF'].min() if not base_branches.empty else 0,
            max_load=base_branches['PF'].max() if not base_branches.empty else 100,
            case_id=0,
            tripped_branch_info=None
        )
        
        cont_fig = create_network_graph_func(
            buses=cont_buses,
            branches=cont_branches,
            title=f"Contingency {contingency_id}",
            min_load=cont_branches['PF'].min() if not cont_branches.empty else 0,
            max_load=cont_branches['PF'].max() if not cont_branches.empty else 100,
            case_id=contingency_id,
            tripped_branch_info=tripped_branch_info  # Pass tripped branch info for red cross marker
        )
        
        slr_fig = create_network_graph_func(
            buses=slr_buses,
            branches=slr_branches,  # Use actual VIO data from database
            title=f"SLR",
            min_load=slr_branches['PF'].min() if not slr_branches.empty else 0,
            max_load=slr_branches['PF'].max() if not slr_branches.empty else 100,
            case_id=0,
            tripped_branch_info=None
        )
        
        dlr_fig = create_network_graph_func(
            buses=dlr_buses,
            branches=dlr_branches,  # Use actual VIO data from database
            title=f"DLR",
            min_load=dlr_branches['PF'].min() if not dlr_branches.empty else 0,
            max_load=dlr_branches['PF'].max() if not dlr_branches.empty else 100,
            case_id=0,
            tripped_branch_info=None
        )
        
        # ===== Add generator diamond markers to SLR and DLR figures =====
        def add_generator_diamonds(fig, buses_df, gen_df, color, label):
            """Add diamond markers for generators with GEN_ADJ values"""
            if gen_df.empty:
                print(f"  No {label} generators to display")
                return
            
            # Normalize column names (case-insensitive)
            gen_col_lower = {col.lower(): col for col in gen_df.columns}
            
            # Rename columns to standard uppercase format
            if 'bus_number' in gen_col_lower and 'BUS_NUMBER' not in gen_df.columns:
                gen_df = gen_df.rename(columns={gen_col_lower['bus_number']: 'BUS_NUMBER'})
            if 'gen_adj' in gen_col_lower and 'GEN_ADJ' not in gen_df.columns:
                gen_df = gen_df.rename(columns={gen_col_lower['gen_adj']: 'GEN_ADJ'})
            
            # Check if required columns exist after normalization
            if 'BUS_NUMBER' not in gen_df.columns or 'GEN_ADJ' not in gen_df.columns:
                print(f"  Missing required columns in {label} generator data: {gen_df.columns.tolist()}")
                return
            
            # Filter generators with non-zero GEN_ADJ
            gen_df = gen_df[gen_df['GEN_ADJ'].abs() > 0.01].copy()
            if gen_df.empty:
                print(f"  No {label} generators with significant GEN_ADJ")
                return
            
            # Extract positions from existing figure's node trace
            node_trace = None
            for trace in fig.data:
                if hasattr(trace, 'mode') and 'markers' in trace.mode:
                    node_trace = trace
            
            if node_trace is None or not hasattr(node_trace, 'x'):
                print(f"  Could not find node trace for {label} generators")
                return
            
            # Create bus number to position mapping
            bus_to_pos = {}
            for i, bus_num in enumerate(buses_df['BUS_NUMBER'].values):
                if i < len(node_trace.x) and i < len(node_trace.y):
                    bus_to_pos[int(bus_num)] = (node_trace.x[i], node_trace.y[i])
            
            # Extract coordinates for generator buses
            gen_x, gen_y, gen_text, gen_adj_values = [], [], [], []
            for _, gen_row in gen_df.iterrows():
                bus_num = int(gen_row['BUS_NUMBER'])
                if bus_num in bus_to_pos:
                    x, y = bus_to_pos[bus_num]
                    gen_x.append(x)
                    gen_y.append(y)
                    gen_text.append(f"Bus {bus_num}")
                    gen_adj_values.append(gen_row['GEN_ADJ'])
            
            if gen_x:
                fig.add_trace(go.Scatter(
                    x=gen_x,
                    y=gen_y,
                    mode='markers',
                    marker=dict(
                        size=20,
                        color=color,
                        symbol='diamond',
                        line=dict(width=2, color='white'),
                        opacity=0.9
                    ),
                    name=f'{label} Gen',
                    hovertemplate='<b>%{text}</b><br>GEN_ADJ: %{customdata:.1f} MW<extra></extra>',
                    customdata=gen_adj_values,
                    text=gen_text,
                    showlegend=True
                ))
                print(f"  ✓ Added {len(gen_x)} {color} {label} generator diamonds")
        
        add_generator_diamonds(slr_fig, slr_buses, slr_gen, 'blue', 'SLR')
        add_generator_diamonds(dlr_fig, dlr_buses, dlr_gen, 'green', 'DLR')
        
        # ===== Calculate performance metrics for all 4 networks =====
        def calculate_metrics(buses_df, branches_df, label):
            """Calculate performance metrics for a network"""
            metrics = {
                'total_gen': buses_df['PG'].sum() if 'PG' in buses_df.columns else 0,
                'total_load': buses_df['PD'].sum() if 'PD' in buses_df.columns else 0,
                'avg_voltage': buses_df['VM'].mean() if 'VM' in buses_df.columns else 0,
                'voltage_violations': len(buses_df[(buses_df['VM'] < 0.95) | (buses_df['VM'] > 1.05)]) if 'VM' in buses_df.columns else 0,
                'branch_violations': 0,
                'max_loading': 0
            }
            
            # Count branch violations (VIO >= 99.99 or MVA > RATE)
            if not branches_df.empty:
                if 'VIO' in branches_df.columns:
                    metrics['branch_violations'] = len(branches_df[branches_df['VIO'] >= 99.99])
                elif 'MVA' in branches_df.columns and 'RATE' in branches_df.columns:
                    metrics['branch_violations'] = len(branches_df[branches_df['MVA'] > branches_df['RATE']])
                
                # Calculate max loading percentage
                if 'MVA' in branches_df.columns and 'RATE' in branches_df.columns:
                    loading = (branches_df['MVA'] / branches_df['RATE'] * 100).replace([float('inf'), -float('inf')], 0)
                    metrics['max_loading'] = loading.max() if not loading.empty else 0
            
            print(f"  {label} Metrics: Gen={metrics['total_gen']:.1f}MW, Load={metrics['total_load']:.1f}MW, "
                  f"V_vio={metrics['voltage_violations']}, Br_vio={metrics['branch_violations']}")
            
            return metrics
        
        base_metrics = calculate_metrics(base_buses, base_branches, "Base")
        cont_metrics = calculate_metrics(cont_buses, cont_branches, "Cont")
        slr_metrics = calculate_metrics(slr_buses, slr_branches, "SLR")
        dlr_metrics = calculate_metrics(dlr_buses, dlr_branches, "DLR")
        
        # ===== Arrange 4 networks in 2x2 grid =====
        # Layout: Base (0,0), Contingency (1,0), SLR (0,1), DLR (1,1)
        # Use x_offset for horizontal spacing, y_offset for vertical spacing
        x_offset = 900
        y_offset = -350  # Negative to move bottom row down
        
        # Start with base figure (top-left, no offset)
        combined = go.Figure(base_fig)
        
        # Add Contingency (top-right, x offset only)
        for trace in cont_fig.data:
            new_trace = go.Scatter(trace)
            if hasattr(trace, 'x') and trace.x:
                new_trace.x = [x + x_offset if x is not None else None for x in trace.x]
            if hasattr(trace, 'name'):
                new_trace.name = f"Cont:{trace.name}" if trace.name else "Cont"
            combined.add_trace(new_trace)
        
        # Add SLR (bottom-left, y offset only)
        for trace in slr_fig.data:
            new_trace = go.Scatter(trace)
            if hasattr(trace, 'y') and trace.y:
                new_trace.y = [y + y_offset if y is not None else None for y in trace.y]
            if hasattr(trace, 'name'):
                new_trace.name = f"SLR:{trace.name}" if trace.name else "SLR"
            combined.add_trace(new_trace)
        
        # Add DLR (bottom-right, both x and y offset)
        for trace in dlr_fig.data:
            new_trace = go.Scatter(trace)
            if hasattr(trace, 'x') and trace.x:
                new_trace.x = [x + x_offset if x is not None else None for x in trace.x]
            if hasattr(trace, 'y') and trace.y:
                new_trace.y = [y + y_offset if y is not None else None for y in trace.y]
            if hasattr(trace, 'name'):
                new_trace.name = f"DLR:{trace.name}" if trace.name else "DLR"
            combined.add_trace(new_trace)
        
        # Extend axes to accommodate all 4 networks
        # Get axis ranges with fallback defaults
        if combined.layout.xaxis.range:
            x_min = combined.layout.xaxis.range[0]
            x_max = combined.layout.xaxis.range[1]
        else:
            # Use default coordinate ranges from IEEE 118-bus system
            x_min = -100
            x_max = 600
        
        if combined.layout.yaxis.range:
            y_min = combined.layout.yaxis.range[0]
            y_max = combined.layout.yaxis.range[1]
        else:
            # Use default coordinate ranges from IEEE 118-bus system
            y_min = -30
            y_max = 300
        
        # Update axis ranges to accommodate all 4 networks
        combined.update_xaxes(range=[x_min, x_max + x_offset])
        combined.update_yaxes(range=[y_min + y_offset, y_max])
        
        # ===== Create performance metrics summary text =====
        def format_metric_row(label, base_val, cont_val, slr_val, dlr_val, unit=""):
            """Format a single metric row for comparison table"""
            return f"{label:.<20} Base: {base_val}{unit:>6}  |  Cont: {cont_val}{unit:>6}  |  SLR: {slr_val}{unit:>6}  |  DLR: {dlr_val}{unit:>6}"
        
        # Calculate losses
        base_loss = base_metrics['total_gen'] - base_metrics['total_load']
        cont_loss = cont_metrics['total_gen'] - cont_metrics['total_load']
        slr_loss = slr_metrics['total_gen'] - slr_metrics['total_load']
        dlr_loss = dlr_metrics['total_gen'] - dlr_metrics['total_load']
        
        # Create comprehensive summary
        summary_text = (
            f"\n{'='*120}\n"
            f"PERFORMANCE METRICS SUMMARY - Case {case_id}, Contingency {contingency_id}\n"
            f"{'='*120}\n\n"
            f"{'METRIC':<20} {'BASE':>15} {'CONTINGENCY':>20} {'SLR':>15} {'DLR':>15}\n"
            f"{'-'*120}\n"
            f"{'Generation':<20} {base_metrics['total_gen']:>12.1f} MW {cont_metrics['total_gen']:>17.1f} MW {slr_metrics['total_gen']:>12.1f} MW {dlr_metrics['total_gen']:>12.1f} MW\n"
            f"{'Load Demand':<20} {base_metrics['total_load']:>12.1f} MW {cont_metrics['total_load']:>17.1f} MW {slr_metrics['total_load']:>12.1f} MW {dlr_metrics['total_load']:>12.1f} MW\n"
            f"{'System Loss':<20} {base_loss:>12.1f} MW {cont_loss:>17.1f} MW {slr_loss:>12.1f} MW {dlr_loss:>12.1f} MW\n"
            f"{'Loss Percentage':<20} {base_loss/base_metrics['total_gen']*100:>12.2f} %  {cont_loss/cont_metrics['total_gen']*100:>17.2f} %  {slr_loss/slr_metrics['total_gen']*100:>12.2f} %  {dlr_loss/dlr_metrics['total_gen']*100:>12.2f} %\n"
            f"{'-'*120}\n"
            f"{'Avg Voltage':<20} {base_metrics['avg_voltage']:>12.4f} pu {cont_metrics['avg_voltage']:>17.4f} pu {slr_metrics['avg_voltage']:>12.4f} pu {dlr_metrics['avg_voltage']:>12.4f} pu\n"
            f"{'Voltage Violations':<20} {base_metrics['voltage_violations']:>15} {cont_metrics['voltage_violations']:>20} {slr_metrics['voltage_violations']:>15} {dlr_metrics['voltage_violations']:>15}\n"
            f"{'Line Violations':<20} {base_metrics['branch_violations']:>15} {cont_metrics['branch_violations']:>20} {slr_metrics['branch_violations']:>15} {dlr_metrics['branch_violations']:>15}\n"
            f"{'Max Line Loading':<20} {base_metrics['max_loading']:>12.1f} %  {cont_metrics['max_loading']:>17.1f} %  {slr_metrics['max_loading']:>12.1f} %  {dlr_metrics['max_loading']:>12.1f} %\n"
            f"{'-'*120}\n\n"
            f"COMPARATIVE ANALYSIS:\n"
            f"  • Contingency Impact: {cont_metrics['branch_violations'] - base_metrics['branch_violations']:+d} line violations compared to base case\n"
            f"  • SLR Performance: {slr_metrics['branch_violations']} violations ({slr_metrics['branch_violations'] - cont_metrics['branch_violations']:+d} vs contingency)\n"
            f"  • DLR Performance: {dlr_metrics['branch_violations']} violations ({dlr_metrics['branch_violations'] - cont_metrics['branch_violations']:+d} vs contingency)\n"
            f"  • Best Solution: {'DLR' if dlr_metrics['branch_violations'] < slr_metrics['branch_violations'] else 'SLR' if slr_metrics['branch_violations'] < dlr_metrics['branch_violations'] else 'TIE'} "
            f"(Fewer violations)\n"
            f"  • Loss Comparison: SLR={slr_loss:.1f}MW ({slr_loss-cont_loss:+.1f}), DLR={dlr_loss:.1f}MW ({dlr_loss-cont_loss:+.1f}) vs Contingency\n"
            f"{'='*120}\n"
        )
        
        print(summary_text)
        
        # Create visual comparison analysis for figure annotation
        best_solution = 'DLR' if dlr_metrics['branch_violations'] < slr_metrics['branch_violations'] else 'SLR' if slr_metrics['branch_violations'] < dlr_metrics['branch_violations'] else 'TIE'
        violation_improvement = slr_metrics['branch_violations'] - dlr_metrics['branch_violations']
        
        analysis_annotation = (
            f"<b>📊 4-NETWORK COMPARISON ANALYSIS</b><br>"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
            f"<b>BASE vs CONTINGENCY:</b> +{cont_metrics['branch_violations'] - base_metrics['branch_violations']} violations | "
            f"Gen Δ {cont_metrics['total_gen'] - base_metrics['total_gen']:+.1f} MW | "
            f"Loss Δ {cont_loss - base_loss:+.1f} MW<br>"
            f"<b>CONTINGENCY vs SLR:</b> {slr_metrics['branch_violations'] - cont_metrics['branch_violations']:+d} violations | "
            f"Gen Δ {slr_metrics['total_gen'] - cont_metrics['total_gen']:+.1f} MW | "
            f"Loss Δ {slr_loss - cont_loss:+.1f} MW | "
            f"Max Loading: {slr_metrics['max_loading']:.1f}%<br>"
            f"<b>CONTINGENCY vs DLR:</b> {dlr_metrics['branch_violations'] - cont_metrics['branch_violations']:+d} violations | "
            f"Gen Δ {dlr_metrics['total_gen'] - cont_metrics['total_gen']:+.1f} MW | "
            f"Loss Δ {dlr_loss - cont_loss:+.1f} MW | "
            f"Max Loading: {dlr_metrics['max_loading']:.1f}%<br>"
            f"<b>SLR vs DLR:</b> {'✅ <b>DLR WINS</b>' if best_solution == 'DLR' else '⚠️ <b>SLR BETTER</b>' if best_solution == 'SLR' else '➖ <b>TIE</b>'} | "
            f"Δ Violations: {violation_improvement:+d} (SLR - DLR) | "
            f"{'DLR reduces violations by ' + str(abs(violation_improvement)) if violation_improvement > 0 else 'SLR reduces violations by ' + str(abs(violation_improvement)) if violation_improvement < 0 else 'Equal performance'}"
        )
        
        # Update layout with title and increased height for better visibility
        combined.update_layout(
            title={
                'text': f"<b>4-Network Comparison - Case {case_id}, Contingency {contingency_id}</b><br>" +
                        f"<sub>Top: Base (left) vs Contingency (right) | Bottom: SLR with blue generators (left) vs DLR with green generators (right)</sub>",
                'font': {'color': 'white', 'size': 18}
            },
            width=1900,
            height=1050,
            annotations=[
                dict(
                    text=analysis_annotation,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.08,
                    xanchor='center', yanchor='top',
                    showarrow=False,
                    font=dict(size=11, color='white', family='Courier New'),
                    align='left',
                    bgcolor='rgba(44, 62, 80, 0.95)',
                    bordercolor='#3498db',
                    borderwidth=2,
                    borderpad=10
                )
            ]
        )
        
        print(f"✓ Combined: {len(combined.data)} traces in 2x2 grid\n")
        return combined
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
