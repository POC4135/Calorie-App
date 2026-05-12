#!/usr/bin/env python3
"""
Database Manager for Calorie Tracker
Handles SQLite operations, GitHub sync, and data export
"""

import sqlite3
import json
import os
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Database path
DB_PATH = "/mnt/user-data/outputs/calorie_tracker.db"
JSON_EXPORT_PATH = "/mnt/user-data/outputs/dashboard_data.json"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.device_id = str(uuid.uuid4())[:8]  # Short device ID for session
        
    def init_database(self, initial_weight_kg: float = 78):
        """Initialize database schema and populate with initial data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create meals table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            date TEXT NOT NULL,
            meal_description TEXT NOT NULL,
            calories REAL NOT NULL,
            protein_g REAL,
            carbs_g REAL,
            fat_g REAL,
            fiber_g REAL,
            sugar_g REAL,
            sodium_mg REAL,
            portion_size TEXT,
            portion_grams REAL,
            user_provided_calories INTEGER DEFAULT 0,
            cooking_method TEXT,
            meal_location TEXT,
            estimate_confidence TEXT,
            image_analyzed INTEGER DEFAULT 0,
            notes TEXT,
            synced_to_github INTEGER DEFAULT 0,
            device_id TEXT
        )
        ''')
        
        # Create daily_summary table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_summary (
            date TEXT PRIMARY KEY,
            total_calories REAL,
            total_protein_g REAL,
            total_carbs_g REAL,
            total_fat_g REAL,
            total_fiber_g REAL,
            total_sugar_g REAL,
            total_sodium_mg REAL,
            meal_count INTEGER,
            avg_meal_time_gap_hours REAL,
            first_meal_time TEXT,
            last_meal_time TEXT
        )
        ''')
        
        # Create weight_log table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weight_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            timestamp TEXT NOT NULL,
            notes TEXT
        )
        ''')
        
        # Create wellbeing_log table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wellbeing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            energy_level INTEGER,
            hunger_level INTEGER,
            notes TEXT,
            linked_meal_id INTEGER,
            FOREIGN KEY (linked_meal_id) REFERENCES meals(id)
        )
        ''')
        
        # Create user_profile table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Create sync_queue table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
        ''')
        
        # Populate user_profile with defaults
        now = datetime.utcnow().isoformat() + 'Z'
        profile_defaults = {
            'age': '29',
            'weight_kg': str(initial_weight_kg),
            'activity_level': 'moderate',
            'goal': 'body_recomp',
            'protein_target_g': '156',
            'fat_target_g': '70',
            'carbs_target_g': '300',
            'fiber_target_g': '34',
            'sugar_limit_g': '50',
            'sodium_limit_mg': '2300',
        }
        
        for key, value in profile_defaults.items():
            cursor.execute('''
            INSERT OR IGNORE INTO user_profile (key, value, updated_at)
            VALUES (?, ?, ?)
            ''', (key, value, now))
        
        # Add initial weight entry
        today = datetime.now().date().isoformat()
        cursor.execute('''
        INSERT INTO weight_log (date, weight_kg, timestamp, notes)
        VALUES (?, ?, ?, ?)
        ''', (today, initial_weight_kg, now, 'Initial entry'))
        
        conn.commit()
        conn.close()
        
        print(f"Database initialized at {self.db_path}")
        return True
    
    def insert_meal(self, meal_data: Dict) -> int:
        """Insert meal entry and return meal ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add device_id and timestamp if not present
        if 'device_id' not in meal_data:
            meal_data['device_id'] = self.device_id
        if 'timestamp' not in meal_data:
            meal_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        if 'date' not in meal_data:
            meal_data['date'] = datetime.now().date().isoformat()
        
        cursor.execute('''
        INSERT INTO meals (
            timestamp, date, meal_description, calories,
            protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg,
            portion_size, portion_grams, user_provided_calories,
            cooking_method, meal_location, estimate_confidence,
            image_analyzed, notes, device_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            meal_data['timestamp'],
            meal_data['date'],
            meal_data['meal_description'],
            meal_data['calories'],
            meal_data.get('protein_g'),
            meal_data.get('carbs_g'),
            meal_data.get('fat_g'),
            meal_data.get('fiber_g'),
            meal_data.get('sugar_g'),
            meal_data.get('sodium_mg'),
            meal_data.get('portion_size'),
            meal_data.get('portion_grams'),
            meal_data.get('user_provided_calories', 0),
            meal_data.get('cooking_method'),
            meal_data.get('meal_location'),
            meal_data.get('estimate_confidence'),
            meal_data.get('image_analyzed', 0),
            meal_data.get('notes'),
            meal_data['device_id']
        ))
        
        meal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update daily summary
        self.update_daily_summary(meal_data['date'])
        
        return meal_id
    
    def update_daily_summary(self, date: str):
        """Recalculate daily summary for given date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all meals for this date
        cursor.execute('''
        SELECT 
            SUM(calories) as total_cal,
            SUM(protein_g) as total_protein,
            SUM(carbs_g) as total_carbs,
            SUM(fat_g) as total_fat,
            SUM(fiber_g) as total_fiber,
            SUM(sugar_g) as total_sugar,
            SUM(sodium_mg) as total_sodium,
            COUNT(*) as meal_count,
            MIN(timestamp) as first_meal,
            MAX(timestamp) as last_meal
        FROM meals
        WHERE date = ?
        ''', (date,))
        
        row = cursor.fetchone()
        
        if row and row[0]:  # If there are meals for this date
            # Calculate average time gap between meals
            cursor.execute('''
            SELECT timestamp FROM meals
            WHERE date = ?
            ORDER BY timestamp
            ''', (date,))
            
            timestamps = [datetime.fromisoformat(t[0].replace('Z', '+00:00')) for t in cursor.fetchall()]
            
            if len(timestamps) > 1:
                gaps = [(timestamps[i+1] - timestamps[i]).total_seconds() / 3600 
                       for i in range(len(timestamps) - 1)]
                avg_gap = sum(gaps) / len(gaps)
            else:
                avg_gap = 0
            
            cursor.execute('''
            INSERT OR REPLACE INTO daily_summary (
                date, total_calories, total_protein_g, total_carbs_g,
                total_fat_g, total_fiber_g, total_sugar_g, total_sodium_mg,
                meal_count, avg_meal_time_gap_hours, first_meal_time, last_meal_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date,
                row[0],  # total_calories
                row[1],  # total_protein
                row[2],  # total_carbs
                row[3],  # total_fat
                row[4],  # total_fiber
                row[5],  # total_sugar
                row[6],  # total_sodium
                row[7],  # meal_count
                avg_gap,
                row[8],  # first_meal
                row[9]   # last_meal
            ))
        
        conn.commit()
        conn.close()
    
    def insert_weight(self, weight_kg: float, notes: str = None) -> int:
        """Insert weight entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat() + 'Z'
        today = datetime.now().date().isoformat()
        
        cursor.execute('''
        INSERT INTO weight_log (date, weight_kg, timestamp, notes)
        VALUES (?, ?, ?, ?)
        ''', (today, weight_kg, now, notes))
        
        weight_id = cursor.lastrowid
        
        # Update user profile
        cursor.execute('''
        UPDATE user_profile SET value = ?, updated_at = ?
        WHERE key = 'weight_kg'
        ''', (str(weight_kg), now))
        
        conn.commit()
        conn.close()
        
        return weight_id
    
    def insert_wellbeing(self, energy_level: int = None, hunger_level: int = None,
                        notes: str = None, linked_meal_id: int = None) -> int:
        """Insert wellbeing entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat() + 'Z'
        
        cursor.execute('''
        INSERT INTO wellbeing_log (timestamp, energy_level, hunger_level, notes, linked_meal_id)
        VALUES (?, ?, ?, ?, ?)
        ''', (now, energy_level, hunger_level, notes, linked_meal_id))
        
        wellbeing_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return wellbeing_id
    
    def get_daily_totals(self, date: str) -> Optional[Dict]:
        """Get daily summary for given date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM daily_summary WHERE date = ?', (date,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return {
                'date': row[0],
                'total_calories': row[1],
                'total_protein_g': row[2],
                'total_carbs_g': row[3],
                'total_fat_g': row[4],
                'total_fiber_g': row[5],
                'total_sugar_g': row[6],
                'total_sodium_mg': row[7],
                'meal_count': row[8],
                'avg_meal_time_gap_hours': row[9],
                'first_meal_time': row[10],
                'last_meal_time': row[11]
            }
        return None
    
    def get_user_targets(self) -> Dict:
        """Get user macro targets from profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value FROM user_profile')
        profile = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        return {
            'protein_target_g': float(profile.get('protein_target_g', 156)),
            'fat_target_g': float(profile.get('fat_target_g', 70)),
            'carbs_target_g': float(profile.get('carbs_target_g', 300)),
            'fiber_target_g': float(profile.get('fiber_target_g', 34)),
        }
    
    def export_to_json(self, days: int = 90) -> str:
        """Export database to JSON for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate cutoff date
        cutoff_date = (datetime.now().date() - timedelta(days=days)).isoformat()
        
        # Get meals
        cursor.execute('''
        SELECT * FROM meals
        WHERE date >= ?
        ORDER BY timestamp DESC
        ''', (cutoff_date,))
        
        meals = []
        for row in cursor.fetchall():
            meals.append({
                'id': row[0],
                'timestamp': row[1],
                'date': row[2],
                'meal_description': row[3],
                'calories': row[4],
                'protein_g': row[5],
                'carbs_g': row[6],
                'fat_g': row[7],
                'fiber_g': row[8],
                'sugar_g': row[9],
                'sodium_mg': row[10],
                'portion_size': row[11],
                'estimate_confidence': row[16],
                'meal_location': row[15]
            })
        
        # Get daily summaries
        cursor.execute('''
        SELECT * FROM daily_summary
        WHERE date >= ?
        ORDER BY date DESC
        ''', (cutoff_date,))
        
        daily_summaries = []
        for row in cursor.fetchall():
            daily_summaries.append({
                'date': row[0],
                'total_calories': row[1],
                'total_protein_g': row[2],
                'total_carbs_g': row[3],
                'total_fat_g': row[4],
                'total_fiber_g': row[5],
                'total_sugar_g': row[6],
                'total_sodium_mg': row[7],
                'meal_count': row[8]
            })
        
        # Get all weight logs
        cursor.execute('SELECT * FROM weight_log ORDER BY timestamp DESC')
        weight_logs = []
        for row in cursor.fetchall():
            weight_logs.append({
                'id': row[0],
                'date': row[1],
                'weight_kg': row[2],
                'timestamp': row[3]
            })
        
        # Get wellbeing logs
        cursor.execute('''
        SELECT * FROM wellbeing_log
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        ''', (cutoff_date,))
        
        wellbeing_logs = []
        for row in cursor.fetchall():
            wellbeing_logs.append({
                'id': row[0],
                'timestamp': row[1],
                'energy_level': row[2],
                'hunger_level': row[3],
                'notes': row[4]
            })
        
        # Get user profile
        cursor.execute('SELECT key, value FROM user_profile')
        user_profile = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        # Build export object
        export_data = {
            'meals': meals,
            'daily_summary': daily_summaries,
            'weight_log': weight_logs,
            'wellbeing_log': wellbeing_logs,
            'user_profile': user_profile,
            'suggestions': [],  # Populated by pattern analyzer
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Write to file
        with open(JSON_EXPORT_PATH, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return JSON_EXPORT_PATH
    
    def update_last_entry(self, calories: float = None, protein_g: float = None,
                         carbs_g: float = None, fat_g: float = None):
        """Update the most recent meal entry (for corrections)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last entry
        cursor.execute('SELECT id, date FROM meals ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False
        
        meal_id, date = row
        
        # Build update query based on provided values
        updates = []
        values = []
        
        if calories is not None:
            updates.append('calories = ?')
            values.append(calories)
        if protein_g is not None:
            updates.append('protein_g = ?')
            values.append(protein_g)
        if carbs_g is not None:
            updates.append('carbs_g = ?')
            values.append(carbs_g)
        if fat_g is not None:
            updates.append('fat_g = ?')
            values.append(fat_g)
        
        if updates:
            values.append(meal_id)
            query = f"UPDATE meals SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            
            # Recalculate daily summary
            self.update_daily_summary(date)
        
        conn.close()
        return True


# Standalone functions for CLI usage
def init_db(db_path: str = DB_PATH, initial_weight: float = 78):
    """Initialize database"""
    manager = DatabaseManager(db_path)
    return manager.init_database(initial_weight)

def export_json(db_path: str = DB_PATH, output_path: str = JSON_EXPORT_PATH):
    """Export database to JSON"""
    manager = DatabaseManager(db_path)
    return manager.export_to_json()


if __name__ == "__main__":
    # Test initialization
    print("Testing database manager...")
    init_db()
    print("Database initialized successfully")
    
    # Test export
    json_path = export_json()
    print(f"Exported to {json_path}")
