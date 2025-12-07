"""
ETL Pipeline for Pharmacovigilance Database
Loads drug data from TSV/CSV files into SQLite database
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR
DB_PATH = BASE_DIR / 'pharma.db'

def create_database_schema(conn):
    """Create database tables"""
    cursor = conn.cursor()
    
    # Drugs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drugs (
            cid TEXT PRIMARY KEY,
            drug_name TEXT NOT NULL,
            drugbank_id TEXT,
            synonyms TEXT,
            cas TEXT,
            unii TEXT,
            inchi_key TEXT
        )
    ''')
    
    # ATC codes table (one-to-many with drugs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atc_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cid TEXT NOT NULL,
            atc_code TEXT NOT NULL,
            atc_level1 TEXT,
            atc_level2 TEXT,
            atc_level3 TEXT,
            atc_level4 TEXT,
            atc_level5 TEXT,
            FOREIGN KEY (cid) REFERENCES drugs(cid)
        )
    ''')
    
    # Side effects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS side_effects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meddra_code TEXT UNIQUE NOT NULL,
            side_effect_name TEXT NOT NULL,
            term_type TEXT
        )
    ''')
    
    # Drug-Side Effect mapping (many-to-many)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drug_side_effects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cid TEXT NOT NULL,
            side_effect_id INTEGER NOT NULL,
            FOREIGN KEY (cid) REFERENCES drugs(cid),
            FOREIGN KEY (side_effect_id) REFERENCES side_effects(id)
        )
    ''')
    
    # Create indexes for fast lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_drug_name ON drugs(drug_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_drugbank_id ON drugs(drugbank_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_atc_cid ON atc_codes(cid)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_atc_code ON atc_codes(atc_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_side_effect_name ON side_effects(side_effect_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_dse_cid ON drug_side_effects(cid)')
    
    conn.commit()
    print("✓ Database schema created")

def extract_atc_hierarchy(atc_code):
    """Extract hierarchical levels from ATC code (e.g., A01BC23)"""
    if not atc_code or len(atc_code) < 7:
        return None, None, None, None, atc_code
    
    return (
        atc_code[0],           # Level 1: A
        atc_code[:3],          # Level 2: A01
        atc_code[:4],          # Level 3: A01B
        atc_code[:5],          # Level 4: A01BC
        atc_code               # Level 5: A01BC23
    )

def load_drug_names(conn):
    """Load drug names from drug_names (1).tsv"""
    print("\n📥 Loading drug names...")
    
    file_path = DATA_DIR / 'drug_names (1).tsv'
    if not file_path.exists():
        print(f"⚠️  Warning: {file_path} not found")
        return
    
    df = pd.read_csv(file_path, sep='\t', header=None, names=['cid', 'drug_name'])
    df['cid'] = df['cid'].astype(str)
    
    # Insert into drugs table
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute('''
            INSERT OR IGNORE INTO drugs (cid, drug_name)
            VALUES (?, ?)
        ''', (row['cid'], row['drug_name']))
    
    conn.commit()
    print(f"✓ Loaded {len(df)} drug names")

def load_atc_codes(conn):
    """Load ATC codes from drug_atc.tsv"""
    print("\n📥 Loading ATC codes...")
    
    file_path = DATA_DIR / 'drug_atc.tsv'
    if not file_path.exists():
        print(f"⚠️  Warning: {file_path} not found")
        return
    
    df = pd.read_csv(file_path, sep='\t', header=None, names=['cid', 'atc_code'])
    df['cid'] = df['cid'].astype(str)
    
    cursor = conn.cursor()
    for _, row in df.iterrows():
        levels = extract_atc_hierarchy(row['atc_code'])
        cursor.execute('''
            INSERT INTO atc_codes (cid, atc_code, atc_level1, atc_level2, atc_level3, atc_level4, atc_level5)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (row['cid'], row['atc_code'], *levels))
    
    conn.commit()
    print(f"✓ Loaded {len(df)} ATC code mappings")

def load_drugbank_vocabulary(conn):
    """Load DrugBank vocabulary and merge with existing drugs"""
    print("\n📥 Loading DrugBank vocabulary...")
    
    file_path = DATA_DIR / 'drugbank vocabulary.csv'
    if not file_path.exists():
        print(f"⚠️  Warning: {file_path} not found")
        return
    
    df = pd.read_csv(file_path)
    
    cursor = conn.cursor()
    updated = 0
    
    for _, row in df.iterrows():
        # Try to match by drug name (case-insensitive)
        common_name = row.get('Common name', '')
        if pd.isna(common_name) or not common_name:
            continue
        
        cursor.execute('''
            UPDATE drugs 
            SET drugbank_id = ?,
                synonyms = ?,
                cas = ?,
                unii = ?,
                inchi_key = ?
            WHERE LOWER(drug_name) = LOWER(?)
        ''', (
            row.get('DrugBank ID', ''),
            row.get('Synonyms', ''),
            row.get('CAS', ''),
            row.get('UNII', ''),
            row.get('Standard InChI Key', ''),
            common_name
        ))
        
        if cursor.rowcount > 0:
            updated += 1
    
    conn.commit()
    print(f"✓ Updated {updated} drugs with DrugBank metadata")

def load_side_effects(conn):
    """Load side effects from meddra_all_se (3) 2.tsv"""
    print("\n📥 Loading side effects...")
    
    file_path = DATA_DIR / 'meddra_all_se (3) 2.tsv'
    if not file_path.exists():
        print(f"⚠️  Warning: {file_path} not found")
        return
    
    # Read file (no header, 6 columns)
    df = pd.read_csv(
        file_path, 
        sep='\t', 
        header=None,
        names=['stereo_cid', 'flat_cid', 'umls_code', 'term_type', 'mapping_code', 'side_effect_name']
    )
    
    # Use stereo_cid (column 1) to match with drug_atc and drug_names
    df['cid'] = df['stereo_cid'].astype(str)
    
    # Filter to only PT (Preferred Term) to avoid duplicates
    df_pt = df[df['term_type'] == 'PT'].copy()
    
    cursor = conn.cursor()
    
    # Insert unique side effects
    unique_se = df_pt[['umls_code', 'side_effect_name', 'term_type']].drop_duplicates()
    for _, row in unique_se.iterrows():
        cursor.execute('''
            INSERT OR IGNORE INTO side_effects (meddra_code, side_effect_name, term_type)
            VALUES (?, ?, ?)
        ''', (row['umls_code'], row['side_effect_name'], row['term_type']))
    
    conn.commit()
    print(f"✓ Loaded {len(unique_se)} unique side effects")
    
    # Insert drug-side effect mappings
    print("\n📥 Loading drug-side effect mappings...")
    for _, row in df_pt.iterrows():
        # Get side_effect_id
        cursor.execute('SELECT id FROM side_effects WHERE meddra_code = ?', (row['umls_code'],))
        result = cursor.fetchone()
        if result:
            se_id = result[0]
            cursor.execute('''
                INSERT INTO drug_side_effects (cid, side_effect_id)
                VALUES (?, ?)
            ''', (row['cid'], se_id))
    
    conn.commit()
    print(f"✓ Loaded {len(df_pt)} drug-side effect mappings")

def print_database_stats(conn):
    """Print database statistics"""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("DATABASE STATISTICS")
    print("="*50)
    
    cursor.execute('SELECT COUNT(*) FROM drugs')
    print(f"📊 Total drugs: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM atc_codes')
    print(f"📊 Total ATC code mappings: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(DISTINCT atc_level2) FROM atc_codes WHERE atc_level2 IS NOT NULL')
    print(f"📊 Unique ATC Level-2 categories: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM side_effects')
    print(f"📊 Total unique side effects: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM drug_side_effects')
    print(f"📊 Total drug-side effect mappings: {cursor.fetchone()[0]}")
    
    cursor.execute('''
        SELECT side_effect_name, COUNT(*) as count 
        FROM drug_side_effects dse
        JOIN side_effects se ON dse.side_effect_id = se.id
        GROUP BY side_effect_name
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    print("\n🔝 Top 10 most common side effects:")
    for i, (name, count) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {name}: {count} drugs")
    
    print("="*50 + "\n")

def main():
    """Main ETL pipeline"""
    print("🚀 Starting ETL Pipeline for Pharmacovigilance Database")
    print("="*50)
    
    # Create database connection
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Step 1: Create schema
        create_database_schema(conn)
        
        # Step 2: Load drug names
        load_drug_names(conn)
        
        # Step 3: Load ATC codes
        load_atc_codes(conn)
        
        # Step 4: Load DrugBank vocabulary (optional enrichment)
        load_drugbank_vocabulary(conn)
        
        # Step 5: Load side effects
        load_side_effects(conn)
        
        # Step 6: Print statistics
        print_database_stats(conn)
        
        print("✅ ETL Pipeline completed successfully!")
        print(f"📁 Database saved to: {DB_PATH}")
        
    except Exception as e:
        print(f"❌ Error during ETL: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
