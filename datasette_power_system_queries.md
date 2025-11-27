# Power System Analysis Queries for Datasette

Copy and paste these queries into the Datasette SQL interface at http://localhost:8001

## Find buses with highest power demand

```sql
SELECT BUS_NUMBER, VM as voltage_pu, PD as load_mw, BASE_KV
FROM BaseBusData 
WHERE base_case_id = 0 AND PD > 0
ORDER BY PD DESC 
LIMIT 10;
```

## Identify transmission bottlenecks

```sql
SELECT From_Bus, To_Bus, 
       ROUND(MVA, 2) as current_flow_mva,
       ROUND(RATE, 2) as thermal_rating_mva,
       ROUND((MVA/RATE*100), 2) as loading_percentage
FROM BaseBranchData 
WHERE base_case_id = 0 AND RATE > 0
ORDER BY (MVA/RATE) DESC 
LIMIT 15;
```

## Voltage profile by base voltage level

```sql
SELECT BASE_KV as voltage_level_kv,
       COUNT(*) as bus_count,
       ROUND(AVG(VM), 4) as avg_voltage_pu,
       ROUND(MIN(VM), 4) as min_voltage_pu,
       ROUND(MAX(VM), 4) as max_voltage_pu
FROM BaseBusData 
WHERE base_case_id = 0
GROUP BY BASE_KV
ORDER BY BASE_KV DESC;
```

## Power balance analysis

```sql
SELECT 
    ROUND(SUM(CASE WHEN PG > 0 THEN PG ELSE 0 END), 2) as total_generation_mw,
    ROUND(SUM(CASE WHEN PD > 0 THEN PD ELSE 0 END), 2) as total_load_mw,
    ROUND(SUM(PG) - SUM(PD), 2) as net_injection_mw,
    COUNT(CASE WHEN PG > 0 THEN 1 END) as generator_count,
    COUNT(CASE WHEN PD > 0 THEN 1 END) as load_count
FROM BaseBusData 
WHERE base_case_id = 0;
```

## Lines operating near thermal limits

```sql
SELECT From_Bus, To_Bus,
       ROUND(MVA, 2) as flow_mva,
       ROUND(RATE, 2) as rating_mva,
       ROUND((MVA/RATE*100), 2) as loading_pct,
       CASE 
           WHEN (MVA/RATE*100) > 95 THEN 'Critical'
           WHEN (MVA/RATE*100) > 85 THEN 'High'
           ELSE 'Normal'
       END as status
FROM BaseBranchData 
WHERE base_case_id = 0 AND RATE > 0 AND (MVA/RATE*100) > 80
ORDER BY (MVA/RATE) DESC;
```

