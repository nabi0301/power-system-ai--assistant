# knowledge_base_setup.py
import sqlite3
from datetime import datetime
import os

def setup_sqlite_knowledge_base(db_path: str = 'knowledge_base.db'):
    """Set up SQLite knowledge base with power system information"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create main concepts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS power_system_concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT,
            keywords TEXT,
            difficulty_level TEXT DEFAULT 'intermediate',
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create FAQ table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frequently_asked_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create definitions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS technical_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            example TEXT,
            related_terms TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Sample power system concepts
    concepts = [
        {
            'title': 'Voltage Regulation',
            'content': 'Voltage regulation is the process of maintaining voltage within acceptable limits throughout the power system. It involves controlling reactive power flow using devices like transformers with tap changers, capacitor banks, and voltage regulators. Proper voltage regulation ensures equipment operates efficiently and safely.',
            'category': 'voltage_control',
            'keywords': 'voltage regulation reactive power transformer tap changer capacitor',
            'difficulty_level': 'intermediate',
            'source': 'IEEE Standard 1547'
        },
        {
            'title': 'Dynamic Line Rating (DLR)',
            'content': 'Dynamic Line Rating uses real-time weather conditions and conductor temperature measurements to determine the safe ampacity of transmission lines. Unlike static ratings that assume worst-case conditions, DLR can increase line capacity by 10-40% during favorable weather conditions (cool temperatures, high wind speeds).',
            'category': 'transmission',
            'keywords': 'DLR dynamic line rating ampacity weather conductor temperature transmission capacity',
            'difficulty_level': 'advanced',
            'source': 'CIGRE Technical Brochure 299'
        },
        {
            'title': 'Static Line Rating (SLR)',
            'content': 'Static Line Rating is a conservative approach that uses fixed thermal limits for transmission lines based on worst-case weather conditions (high temperature, low wind speed). While safer and simpler to implement, SLR often underutilizes transmission capacity.',
            'category': 'transmission',
            'keywords': 'SLR static line rating thermal limits conservative transmission',
            'difficulty_level': 'beginner',
            'source': 'IEEE Standard 738'
        },
        {
            'title': 'Contingency Analysis',
            'content': 'Contingency analysis evaluates power system security by simulating equipment outages and assessing their impact. N-1 analysis ensures the system remains stable after any single component failure. This analysis is crucial for maintaining system reliability and preventing cascading failures.',
            'category': 'analysis',
            'keywords': 'contingency analysis N-1 security reliability outage simulation',
            'difficulty_level': 'intermediate',
            'source': 'NERC Reliability Standards'
        },
        {
            'title': 'Power Flow Analysis',
            'content': 'Power flow analysis calculates the steady-state operating conditions of a power system. It determines voltage magnitudes and phase angles at each bus, and power flows through transmission lines. This analysis is fundamental for system planning and operation.',
            'category': 'analysis',
            'keywords': 'power flow load flow voltage angle bus transmission Newton-Raphson',
            'difficulty_level': 'intermediate',
            'source': 'Power System Analysis by Grainger & Stevenson'
        },
        {
            'title': 'Bus Types in Power Systems',
            'content': 'Power system buses are classified into three types: 1) Slack/Reference bus - voltage magnitude and angle are specified, 2) PV/Generator bus - real power and voltage magnitude are specified, 3) PQ/Load bus - real and reactive power are specified.',
            'category': 'fundamentals',
            'keywords': 'bus types slack PV PQ generator load reference voltage power',
            'difficulty_level': 'beginner',
            'source': 'Power System Engineering Textbook'
        },
        {
            'title': 'IEEE 118-Bus Test System',
            'content': 'The IEEE 118-bus test system is a standard benchmark for power system analysis. It represents a portion of the American Electric Power System with 118 buses, 186 branches, and 54 generators. The system is widely used for testing algorithms and validating power system analysis tools.',
            'category': 'test_systems',
            'keywords': 'IEEE 118 bus test system benchmark AEP American Electric Power',
            'difficulty_level': 'intermediate',
            'source': 'IEEE Power Engineering Society'
        },
        {
            'title': 'Thermal Overload Protection',
            'content': 'Thermal overload protection prevents conductors from exceeding their temperature limits. When current exceeds the thermal rating, conductor temperature rises, causing sag and potential equipment damage. Protection systems monitor loading and temperature to prevent thermal violations.',
            'category': 'protection',
            'keywords': 'thermal overload protection conductor temperature current rating sag',
            'difficulty_level': 'intermediate',
            'source': 'IEEE C37.2 Standard'
        }
    ]
    
    # Insert concepts
    for concept in concepts:
        cursor.execute("""
            INSERT OR IGNORE INTO power_system_concepts (title, content, category, keywords, difficulty_level, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (concept['title'], concept['content'], concept['category'], 
              concept['keywords'], concept['difficulty_level'], concept['source']))
    
    # Sample FAQs
    faqs = [
        {
            'question': 'What is the difference between DLR and SLR?',
            'answer': 'DLR (Dynamic Line Rating) uses real-time weather data to determine transmission line capacity, while SLR (Static Line Rating) uses conservative fixed limits. DLR can provide 10-40% more capacity during favorable weather conditions.',
            'category': 'transmission',
            'tags': 'DLR SLR comparison transmission capacity'
        },
        {
            'question': 'What causes voltage violations in power systems?',
            'answer': 'Voltage violations occur when bus voltages fall outside acceptable limits (typically 0.95-1.05 pu). Common causes include heavy loading, reactive power shortages, equipment outages, or inadequate voltage control devices.',
            'category': 'voltage_control',
            'tags': 'voltage violations limits reactive power'
        },
        {
            'question': 'How does contingency analysis help in power system operation?',
            'answer': 'Contingency analysis simulates equipment failures to ensure the system can handle outages without violating limits. It helps operators identify potential problems and take preventive actions before failures occur.',
            'category': 'reliability',
            'tags': 'contingency N-1 reliability security'
        },
        {
            'question': 'What is the IEEE 118-bus system used for?',
            'answer': 'The IEEE 118-bus system is a standard test case for validating power system analysis algorithms. It provides a realistic network topology for testing optimization, contingency analysis, and other power system studies.',
            'category': 'test_systems',
            'tags': 'IEEE 118 bus test validation benchmark'
        },
        {
            'question': 'How do I interpret power flow results?',
            'answer': 'Power flow results show voltage magnitudes and angles at each bus, and power flows on each branch. Look for voltage violations (outside 0.95-1.05 pu), thermal overloads (>100% of rating), and reactive power limits.',
            'category': 'analysis',
            'tags': 'power flow interpretation voltage thermal reactive'
        }
    ]
    
    # Insert FAQs
    for faq in faqs:
        cursor.execute("""
            INSERT OR IGNORE INTO frequently_asked_questions (question, answer, category, tags)
            VALUES (?, ?, ?, ?)
        """, (faq['question'], faq['answer'], faq['category'], faq['tags']))
    
    # Sample technical definitions
    definitions = [
        {
            'term': 'Per Unit System',
            'definition': 'A normalization technique where system quantities are expressed as fractions of base values, eliminating units and simplifying calculations.',
            'example': 'A voltage of 115 kV on a 138 kV base is 115/138 = 0.833 pu',
            'related_terms': 'base values, normalization, voltage magnitude',
            'category': 'fundamentals'
        },
        {
            'term': 'Thermal Rating',
            'definition': 'The maximum continuous current a conductor can carry without exceeding its temperature limit, considering heat generation and dissipation.',
            'example': 'A transmission line with 1000 A thermal rating can carry up to 1000 amperes continuously',
            'related_terms': 'ampacity, conductor temperature, heat balance',
            'category': 'transmission'
        },
        {
            'term': 'Reactive Power',
            'definition': 'Power that oscillates between source and load, measured in VARs. It is necessary for maintaining voltage levels but does not contribute to real work.',
            'example': 'Capacitive reactive power (leading) raises voltage, inductive reactive power (lagging) lowers voltage',
            'related_terms': 'VARs, voltage control, power factor',
            'category': 'fundamentals'
        },
        {
            'term': 'Contingency',
            'definition': 'An unexpected outage or failure of a power system component, such as a generator, transmission line, or transformer.',
            'example': 'N-1 contingency analysis simulates the outage of any single component',
            'related_terms': 'N-1, outage, reliability, security',
            'category': 'reliability'
        },
        {
            'term': 'Load Flow',
            'definition': 'Another term for power flow analysis - the calculation of steady-state voltages and power flows in a power system.',
            'example': 'Load flow studies determine if the system can supply all loads without violations',
            'related_terms': 'power flow, steady state, Newton-Raphson',
            'category': 'analysis'
        }
    ]
    
    # Insert definitions
    for defn in definitions:
        cursor.execute("""
            INSERT OR REPLACE INTO technical_definitions (term, definition, example, related_terms, category)
            VALUES (?, ?, ?, ?, ?)
        """, (defn['term'], defn['definition'], defn['example'], defn['related_terms'], defn['category']))
    
    # Create indexes for better search performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_keywords ON power_system_concepts(keywords)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_category ON power_system_concepts(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_faq_tags ON frequently_asked_questions(tags)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_definitions_term ON technical_definitions(term)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_title ON power_system_concepts(title)")
    
    conn.commit()
    conn.close()
    
    print(f"✅ SQLite knowledge base setup complete at {db_path}")
    print(f"   - {len(concepts)} power system concepts")
    print(f"   - {len(faqs)} frequently asked questions")
    print(f"   - {len(definitions)} technical definitions")
    
    return True

def check_knowledge_base_exists(db_path: str = 'knowledge_base.db') -> bool:
    """Check if knowledge base exists and has data"""
    if not os.path.exists(db_path):
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist and have data
        cursor.execute("SELECT COUNT(*) FROM power_system_concepts")
        concept_count = cursor.fetchone()[0]
        
        conn.close()
        return concept_count > 0
        
    except Exception:
        return False

if __name__ == "__main__":
    setup_sqlite_knowledge_base()