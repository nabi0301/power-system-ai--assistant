import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_contingency_functions():
    """Create stored procedures for contingency data inheritance and violation calculations"""
    
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
        
        # Create the main data inheritance function
        logging.info("Creating populate_complete_contingency_data() function...")
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
                v_bus_record RECORD;
                v_branch_record RECORD;
                v_voltage_violation DECIMAL;
                v_thermal_violation DECIMAL;
                v_mva_flow DECIMAL;
                v_violation_pct DECIMAL;
            BEGIN
                -- Step 1: Populate missing bus data from base case
                FOR v_bus_record IN 
                    SELECT bb.bus_number, bb.vm, bb.va, bb.base_kv, bb.pg, bb.qg, bb.pd, bb.qd
                    FROM base_buses bb
                    WHERE bb.case_id = p_base_case_id
                    AND bb.bus_number NOT IN (
                        SELECT bus_number 
                        FROM ContingencyBusData 
                        WHERE contingency_case_id = p_contingency_case_id
                    )
                LOOP
                    -- Insert missing bus data inherited from base case
                    INSERT INTO ContingencyBusData (
                        contingency_case_id, base_case_id, bus_number, 
                        vm, va, base_kv, pg, qg, pd, qd,
                        voltage_violation, violation_type, inherited_from_base
                    ) VALUES (
                        p_contingency_case_id, p_base_case_id, v_bus_record.bus_number,
                        v_bus_record.vm, v_bus_record.va, v_bus_record.base_kv,
                        v_bus_record.pg, v_bus_record.qg, v_bus_record.pd, v_bus_record.qd,
                        0, 'none', TRUE
                    );
                    
                    v_buses_populated := v_buses_populated + 1;
                END LOOP;
                
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
                
                -- Step 4: Populate missing branch data from base case
                FOR v_branch_record IN 
                    SELECT bb.from_bus, bb.to_bus, bb.circuit_id, bb.pf, bb.qf, bb.rate,
                           ROW_NUMBER() OVER (ORDER BY bb.from_bus, bb.to_bus, bb.circuit_id) as branch_number
                    FROM base_branches bb
                    WHERE bb.case_id = p_base_case_id
                LOOP
                    -- Check if this branch already exists in contingency data
                    IF NOT EXISTS (
                        SELECT 1 FROM ContingencyBranchData 
                        WHERE contingency_case_id = p_contingency_case_id 
                        AND branch_number = v_branch_record.branch_number
                    ) THEN
                        -- Calculate MVA flow
                        v_mva_flow := SQRT(POWER(v_branch_record.pf, 2) + POWER(v_branch_record.qf, 2));
                        
                        -- Calculate thermal violation
                        IF v_branch_record.rate > 0 AND v_mva_flow > v_branch_record.rate THEN
                            v_thermal_violation := v_mva_flow - v_branch_record.rate;
                            v_violation_pct := (v_mva_flow / v_branch_record.rate - 1) * 100;
                        ELSE
                            v_thermal_violation := 0;
                            v_violation_pct := 0;
                        END IF;
                        
                        -- Insert missing branch data inherited from base case
                        INSERT INTO ContingencyBranchData (
                            contingency_case_id, base_case_id, branch_number,
                            from_bus, to_bus, pf, qf, rate_a,
                            mva_from, thermal_violation, violation_percentage,
                            status, inherited_from_base
                        ) VALUES (
                            p_contingency_case_id, p_base_case_id, v_branch_record.branch_number,
                            v_branch_record.from_bus, v_branch_record.to_bus, 
                            v_branch_record.pf, v_branch_record.qf, v_branch_record.rate,
                            v_mva_flow, v_thermal_violation, v_violation_pct,
                            1, TRUE
                        );
                        
                        v_branches_populated := v_branches_populated + 1;
                    END IF;
                END LOOP;
                
                -- Step 5: Update existing branch data with calculated values
                UPDATE ContingencyBranchData 
                SET 
                    mva_from = SQRT(POWER(COALESCE(pf, 0), 2) + POWER(COALESCE(qf, 0), 2)),
                    rate_a = COALESCE(rate_a, (
                        SELECT bb.rate 
                        FROM base_branches bb 
                        WHERE bb.case_id = p_base_case_id 
                        AND ROW_NUMBER() OVER (ORDER BY bb.from_bus, bb.to_bus, bb.circuit_id) = branch_number
                        LIMIT 1
                    ))
                WHERE contingency_case_id = p_contingency_case_id;
                
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
        
        # Create a helper function to identify contingency elements
        logging.info("Creating identify_contingency_element() function...")
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
                -- Find branches that exist in base case but not in contingency case (removed branches)
                FOR v_missing_branch IN
                    SELECT bb.from_bus, bb.to_bus, bb.circuit_id,
                           ROW_NUMBER() OVER (ORDER BY bb.from_bus, bb.to_bus, bb.circuit_id) as branch_num
                    FROM base_branches bb
                    WHERE bb.case_id = p_base_case_id
                    AND ROW_NUMBER() OVER (ORDER BY bb.from_bus, bb.to_bus, bb.circuit_id) NOT IN (
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
        
        # Create analysis views for easy querying
        logging.info("Creating contingency analysis views...")
        cursor.execute("""
            CREATE OR REPLACE VIEW ContingencyViolationSummary AS
            SELECT 
                cc.contingency_case_id,
                cc.base_case_id,
                cc.case_number,
                cc.contingency_element,
                cc.max_voltage_violation,
                cc.max_thermal_violation,
                cc.violation_count,
                COUNT(CASE WHEN cbd.voltage_violation > 0 THEN 1 END) as voltage_violation_buses,
                COUNT(CASE WHEN cbr.thermal_violation > 0 THEN 1 END) as thermal_violation_branches,
                MAX(cbr.violation_percentage) as max_thermal_percentage
            FROM ContingencyCases cc
            LEFT JOIN ContingencyBusData cbd ON cc.contingency_case_id = cbd.contingency_case_id
            LEFT JOIN ContingencyBranchData cbr ON cc.contingency_case_id = cbr.contingency_case_id
            GROUP BY cc.contingency_case_id, cc.base_case_id, cc.case_number, 
                     cc.contingency_element, cc.max_voltage_violation, 
                     cc.max_thermal_violation, cc.violation_count;
        """)
        
        cursor.execute("""
            CREATE OR REPLACE VIEW WorstContingencies AS
            SELECT 
                contingency_case_id,
                base_case_id,
                case_number,
                contingency_element,
                max_voltage_violation,
                max_thermal_violation,
                violation_count,
                RANK() OVER (ORDER BY violation_count DESC, max_thermal_violation DESC) as severity_rank
            FROM ContingencyCases
            WHERE processing_status = 'completed'
            ORDER BY severity_rank
            LIMIT 50;
        """)
        
        conn.commit()
        logging.info("✅ Contingency functions and views created successfully!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error creating contingency functions: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Creating Contingency Data Processing Functions")
    print("=" * 50)
    
    success = create_contingency_functions()
    
    if success:
        print("\n✅ Functions creation completed successfully!")
        print("\nCreated functions:")
        print("  - populate_complete_contingency_data()")
        print("  - identify_contingency_element()")
        print("  - ContingencyViolationSummary view")
        print("  - WorstContingencies view")
    else:
        print("\n❌ Functions creation failed. Check the logs.")