import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_contingency_functions():
    """Fix the stored procedure to avoid window function in WHERE clause"""
    
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'database': '118',
        'user': 'postgres',
        'password': 'pnnl'
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Drop and recreate the function with fixed logic
        logging.info("Dropping and recreating populate_complete_contingency_data() function...")
        cursor.execute("DROP FUNCTION IF EXISTS populate_complete_contingency_data(integer,integer) CASCADE")
        
        cursor.execute("""
            CREATE OR REPLACE FUNCTION populate_complete_contingency_data(
                p_contingency_case_id INTEGER,
                p_base_case_id INTEGER
            )
            RETURNS TABLE(
                buses_populated INTEGER,
                branches_populated INTEGER,
                voltage_violations INTEGER,
                thermal_violations INTEGER
            ) AS $$
            DECLARE
                v_buses_populated INTEGER := 0;
                v_branches_populated INTEGER := 0;
                v_voltage_violations INTEGER := 0;
                v_thermal_violations INTEGER := 0;
            BEGIN
                -- Step 1: Populate missing bus data from base case
                INSERT INTO ContingencyBusData (
                    contingency_case_id, base_case_id, bus_number, 
                    vm, va, base_kv, pg, qg, pd, qd,
                    voltage_violation, violation_type, inherited_from_base
                )
                SELECT 
                    p_contingency_case_id, p_base_case_id, bb.bus_number,
                    bb.vm, bb.va, bb.base_kv, bb.pg, bb.qg, bb.pd, bb.qd,
                    0, 'none', TRUE
                FROM base_buses bb
                WHERE bb.case_id = p_base_case_id
                AND bb.bus_number NOT IN (
                    SELECT bus_number 
                    FROM ContingencyBusData 
                    WHERE contingency_case_id = p_contingency_case_id
                );
                
                GET DIAGNOSTICS v_buses_populated = ROW_COUNT;
                
                -- Step 2: Update existing bus data with base case values where missing
                UPDATE ContingencyBusData cbd
                SET 
                    base_kv = COALESCE(cbd.base_kv, bb.base_kv),
                    pg = COALESCE(cbd.pg, bb.pg),
                    qg = COALESCE(cbd.qg, bb.qg),
                    pd = COALESCE(cbd.pd, bb.pd),
                    qd = COALESCE(cbd.qd, bb.qd)
                FROM base_buses bb
                WHERE cbd.contingency_case_id = p_contingency_case_id
                AND cbd.bus_number = bb.bus_number
                AND bb.case_id = p_base_case_id;
                
                -- Step 3: Calculate voltage violations for all buses
                UPDATE ContingencyBusData 
                SET 
                    voltage_violation = CASE
                        WHEN vm > 1.05 THEN vm - 1.05
                        WHEN vm < 0.95 THEN 0.95 - vm
                        ELSE 0
                    END,
                    violation_type = CASE
                        WHEN vm > 1.05 THEN 'high'
                        WHEN vm < 0.95 THEN 'low'
                        ELSE 'none'
                    END
                WHERE contingency_case_id = p_contingency_case_id;
                
                -- Step 4: Populate missing branch data from base case using CTE
                WITH numbered_branches AS (
                    SELECT bb.from_bus, bb.to_bus, bb.circuit_id, bb.pf, bb.qf, bb.rate,
                           ROW_NUMBER() OVER (ORDER BY bb.from_bus, bb.to_bus, bb.circuit_id) as branch_number
                    FROM base_branches bb
                    WHERE bb.case_id = p_base_case_id
                )
                INSERT INTO ContingencyBranchData (
                    contingency_case_id, base_case_id, branch_number,
                    from_bus, to_bus, pf, qf, rate_a,
                    mva_from, thermal_violation, violation_percentage,
                    status, inherited_from_base
                )
                SELECT 
                    p_contingency_case_id, p_base_case_id, nb.branch_number,
                    nb.from_bus, nb.to_bus, nb.pf, nb.qf, nb.rate,
                    SQRT(POWER(nb.pf, 2) + POWER(nb.qf, 2)), -- mva_from
                    CASE 
                        WHEN nb.rate > 0 AND SQRT(POWER(nb.pf, 2) + POWER(nb.qf, 2)) > nb.rate 
                        THEN SQRT(POWER(nb.pf, 2) + POWER(nb.qf, 2)) - nb.rate
                        ELSE 0
                    END, -- thermal_violation
                    CASE 
                        WHEN nb.rate > 0 
                        THEN (SQRT(POWER(nb.pf, 2) + POWER(nb.qf, 2)) / nb.rate - 1) * 100
                        ELSE 0
                    END, -- violation_percentage
                    1, TRUE
                FROM numbered_branches nb
                WHERE nb.branch_number NOT IN (
                    SELECT branch_number 
                    FROM ContingencyBranchData 
                    WHERE contingency_case_id = p_contingency_case_id
                );
                
                GET DIAGNOSTICS v_branches_populated = ROW_COUNT;
                
                -- Step 5: Update existing branch data with calculated values using CTE
                WITH numbered_branches AS (
                    SELECT bb.rate,
                           ROW_NUMBER() OVER (ORDER BY bb.from_bus, bb.to_bus, bb.circuit_id) as branch_number
                    FROM base_branches bb
                    WHERE bb.case_id = p_base_case_id
                )
                UPDATE ContingencyBranchData cbd
                SET 
                    mva_from = SQRT(POWER(COALESCE(pf, 0), 2) + POWER(COALESCE(qf, 0), 2)),
                    rate_a = COALESCE(cbd.rate_a, nb.rate)
                FROM numbered_branches nb
                WHERE cbd.contingency_case_id = p_contingency_case_id
                AND cbd.branch_number = nb.branch_number;
                
                -- Step 6: Calculate thermal violations for all branches
                UPDATE ContingencyBranchData 
                SET 
                    thermal_violation = CASE
                        WHEN rate_a > 0 AND mva_from > rate_a THEN mva_from - rate_a
                        ELSE 0
                    END,
                    violation_percentage = CASE
                        WHEN rate_a > 0 THEN (mva_from / rate_a - 1) * 100
                        ELSE 0
                    END
                WHERE contingency_case_id = p_contingency_case_id;
                
                -- Step 7: Count violations
                SELECT COUNT(*) INTO v_voltage_violations
                FROM ContingencyBusData 
                WHERE contingency_case_id = p_contingency_case_id 
                AND voltage_violation > 0;
                
                SELECT COUNT(*) INTO v_thermal_violations
                FROM ContingencyBranchData 
                WHERE contingency_case_id = p_contingency_case_id 
                AND thermal_violation > 0;
                
                -- Step 8: Update contingency case summary
                UPDATE ContingencyCases 
                SET 
                    max_voltage_violation = (
                        SELECT COALESCE(MAX(voltage_violation), 0)
                        FROM ContingencyBusData 
                        WHERE contingency_case_id = p_contingency_case_id
                    ),
                    max_thermal_violation = (
                        SELECT COALESCE(MAX(thermal_violation), 0)
                        FROM ContingencyBranchData 
                        WHERE contingency_case_id = p_contingency_case_id
                    ),
                    violation_count = v_voltage_violations + v_thermal_violations,
                    processing_status = 'completed'
                WHERE contingency_case_id = p_contingency_case_id;
                
                RETURN QUERY SELECT v_buses_populated, v_branches_populated, v_voltage_violations, v_thermal_violations;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Also fix the identify_contingency_element function
        logging.info("Fixing identify_contingency_element() function...")
        cursor.execute("DROP FUNCTION IF EXISTS identify_contingency_element(integer,integer) CASCADE")
        
        cursor.execute("""
            CREATE OR REPLACE FUNCTION identify_contingency_element(
                p_contingency_case_id INTEGER,
                p_base_case_id INTEGER
            )
            RETURNS TEXT AS $$
            DECLARE
                v_contingency_element TEXT := '';
                v_missing_branch RECORD;
            BEGIN
                -- Find branches that exist in base case but not in contingency case using CTE
                FOR v_missing_branch IN
                    WITH numbered_branches AS (
                        SELECT bb.from_bus, bb.to_bus, bb.circuit_id,
                               ROW_NUMBER() OVER (ORDER BY bb.from_bus, bb.to_bus, bb.circuit_id) as branch_num
                        FROM base_branches bb
                        WHERE bb.case_id = p_base_case_id
                    )
                    SELECT nb.from_bus, nb.to_bus, nb.circuit_id, nb.branch_num
                    FROM numbered_branches nb
                    WHERE nb.branch_num NOT IN (
                        SELECT branch_number 
                        FROM ContingencyBranchData 
                        WHERE contingency_case_id = p_contingency_case_id
                        AND NOT inherited_from_base
                    )
                    LIMIT 3  -- Most contingencies involve 1-2 elements
                LOOP
                    IF v_contingency_element != '' THEN
                        v_contingency_element := v_contingency_element || ', ';
                    END IF;
                    
                    v_contingency_element := v_contingency_element || 
                        'Line ' || v_missing_branch.from_bus || '-' || v_missing_branch.to_bus;
                    
                    IF v_missing_branch.circuit_id IS NOT NULL AND v_missing_branch.circuit_id != '1' THEN
                        v_contingency_element := v_contingency_element || '-' || v_missing_branch.circuit_id;
                    END IF;
                    
                    -- Mark this as a contingency element
                    UPDATE ContingencyBranchData 
                    SET is_contingency_element = TRUE
                    WHERE contingency_case_id = p_contingency_case_id 
                    AND branch_number = v_missing_branch.branch_num;
                END LOOP;
                
                IF v_contingency_element = '' THEN
                    v_contingency_element := 'Unknown contingency element';
                END IF;
                
                RETURN v_contingency_element;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        conn.commit()
        logging.info("✅ Fixed both populate_complete_contingency_data() and identify_contingency_element() functions!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error fixing contingency functions: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Contingency Data Processing Functions")
    print("=" * 50)
    
    success = fix_contingency_functions()
    
    if success:
        print("\n✅ Function fix completed successfully!")
        print("Both stored procedures now use CTEs instead of window functions in WHERE clauses.")
    else:
        print("\n❌ Function fix failed. Check the logs.")