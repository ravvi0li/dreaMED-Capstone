"""
Utility functions for the Flask app
"""

import sqlite3
from pathlib import Path
from fuzzywuzzy import fuzz
import json

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'pharma.db'

def search_drugs(query, limit=10):
    """
    Search for drugs by name (with fuzzy matching)
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of matching drugs
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # First try exact match
    cursor.execute('''
        SELECT cid, drug_name, drugbank_id
        FROM drugs
        WHERE LOWER(drug_name) LIKE LOWER(?)
        LIMIT ?
    ''', (f'%{query}%', limit))
    
    results = cursor.fetchall()
    conn.close()
    
    drugs = []
    for row in results:
        drugs.append({
            'cid': row[0],
            'name': row[1],
            'drugbank_id': row[2] if row[2] else None
        })
    
    return drugs

def get_all_drugs(limit=None):
    """Get all drugs from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if limit:
        cursor.execute('SELECT cid, drug_name FROM drugs LIMIT ?', (limit,))
    else:
        cursor.execute('SELECT cid, drug_name FROM drugs')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{'cid': row[0], 'name': row[1]} for row in results]

def get_top_side_effects(limit=20):
    """Get most common side effects"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT se.side_effect_name, COUNT(*) as count
        FROM drug_side_effects dse
        JOIN side_effects se ON dse.side_effect_id = se.id
        GROUP BY se.side_effect_name
        ORDER BY count DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return [{'name': row[0], 'count': row[1]} for row in results]

def get_database_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute('SELECT COUNT(*) FROM drugs')
    stats['total_drugs'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM side_effects')
    stats['total_side_effects'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM drug_side_effects')
    stats['total_mappings'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT atc_level2) FROM atc_codes WHERE atc_level2 IS NOT NULL')
    stats['total_atc_categories'] = cursor.fetchone()[0]
    
    conn.close()
    
    return stats
