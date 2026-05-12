#!/usr/bin/env python3
"""
Calorie and Macro Estimator
Handles nutritional analysis for Indian cuisine
"""

import re
from typing import Dict, Tuple, Optional

# Indian food database (abbreviated - load from references/indian_food_db.md in production)
INDIAN_FOOD_DB = {
    # Breads
    'roti': {'cal': 100, 'protein': 3, 'carbs': 18, 'fat': 2.5, 'fiber': 3, 'portion_g': 40},
    'chapati': {'cal': 100, 'protein': 3, 'carbs': 18, 'fat': 2.5, 'fiber': 3, 'portion_g': 40},
    'paratha': {'cal': 180, 'protein': 4, 'carbs': 25, 'fat': 7, 'fiber': 2.5, 'portion_g': 60},
    'naan': {'cal': 260, 'protein': 7, 'carbs': 45, 'fat': 5, 'fiber': 2, 'portion_g': 90},
    
    # Rice
    'rice': {'cal': 205, 'protein': 4, 'carbs': 45, 'fat': 0.5, 'fiber': 0.6, 'portion_g': 158},
    'biryani': {'cal': 350, 'protein': 22, 'carbs': 45, 'fat': 10, 'fiber': 2, 'portion_g': 240},
    
    # Dals
    'dal': {'cal': 115, 'protein': 9, 'carbs': 20, 'fat': 0.5, 'fiber': 8, 'portion_g': 240},
    
    # Paneer
    'paneer': {'cal': 265, 'protein': 18, 'carbs': 3, 'fat': 20, 'fiber': 0, 'portion_g': 100},
    
    # South Indian
    'dosa': {'cal': 133, 'protein': 3, 'carbs': 22, 'fat': 3, 'fiber': 2, 'portion_g': 60},
    'idli': {'cal': 39, 'protein': 2, 'carbs': 8, 'fat': 0.3, 'fiber': 0.5, 'portion_g': 30},
    'vada': {'cal': 145, 'protein': 4, 'carbs': 18, 'fat': 6, 'fiber': 2, 'portion_g': 45},
    'sambar': {'cal': 90, 'protein': 4, 'carbs': 15, 'fat': 2, 'fiber': 4, 'portion_g': 240},
    
    # Add more items from database...
}

class CalorieEstimator:
    def __init__(self):
        self.food_db = INDIAN_FOOD_DB
    
    def parse_portion(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Extract portion size from text"""
        # Match patterns like "150g", "2 rotis", "1 cup"
        patterns = [
            r'(\d+\.?\d*)\s*g(?:rams?)?',
            r'(\d+\.?\d*)\s*ml',
            r'(\d+\.?\d*)\s*cup',
            r'(\d+)\s+(?:pieces?|rotis?|dosas?|idlis?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                amount = float(match.group(1))
                unit = match.group(0).split(match.group(1))[1].strip()
                return amount, unit
        
        return None, None
    
    def estimate_meal(self, description: str, user_provided_cal: Optional[float] = None) -> Dict:
        """
        Estimate calories and macros for a meal description
        
        Returns dict with: calories, protein_g, carbs_g, fat_g, fiber_g, 
                          confidence, breakdown
        """
        description_lower = description.lower()
        
        # If user provided calories, estimate macros based on that
        if user_provided_cal:
            return self.estimate_macros_from_calories(user_provided_cal, description_lower)
        
        # Parse for food items
        total_cal = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_fiber = 0
        breakdown = []
        confidence_scores = []
        
        for food_name, food_data in self.food_db.items():
            if food_name in description_lower:
                # Check for quantity
                quantity = 1  # default
                
                # Extract number before food name
                pattern = rf'(\d+)\s+{food_name}'
                match = re.search(pattern, description_lower)
                if match:
                    quantity = int(match.group(1))
                
                # Check for portion in grams
                portion_match = re.search(rf'{food_name}.*?(\d+\.?\d*)\s*g', description_lower)
                if portion_match:
                    grams = float(portion_match.group(1))
                    quantity = grams / food_data['portion_g']
                
                # Calculate
                cal = food_data['cal'] * quantity
                protein = food_data['protein'] * quantity
                carbs = food_data['carbs'] * quantity
                fat = food_data['fat'] * quantity
                fiber = food_data['fiber'] * quantity
                
                total_cal += cal
                total_protein += protein
                total_carbs += carbs
                total_fat += fat
                total_fiber += fiber
                
                breakdown.append({
                    'item': food_name,
                    'quantity': quantity,
                    'calories': round(cal, 1)
                })
                
                confidence_scores.append(0.8)  # High confidence for DB matches
        
        # Estimate confidence
        if not breakdown:
            # No DB matches, use generic estimation
            confidence = 'low'
            # Make a rough guess based on description length and keywords
            total_cal = 400  # Default medium meal
            total_protein = 15
            total_carbs = 50
            total_fat = 12
            total_fiber = 5
        elif len(breakdown) == 1:
            confidence = 'high'
        else:
            confidence = 'medium' if len(breakdown) <= 3 else 'medium'
        
        return {
            'calories': round(total_cal, 1),
            'protein_g': round(total_protein, 1),
            'carbs_g': round(total_carbs, 1),
            'fat_g': round(total_fat, 1),
            'fiber_g': round(total_fiber, 1),
            'sugar_g': round(total_carbs * 0.1, 1),  # Rough estimate
            'sodium_mg': 400,  # Generic Indian food sodium
            'confidence': confidence,
            'breakdown': breakdown
        }
    
    def estimate_macros_from_calories(self, calories: float, description: str) -> Dict:
        """Estimate macro breakdown when user provides total calories"""
        # Use typical Indian food ratios
        # Approximate: 20% protein, 50% carbs, 30% fat
        
        protein_cal = calories * 0.20
        carbs_cal = calories * 0.50
        fat_cal = calories * 0.30
        
        return {
            'calories': calories,
            'protein_g': round(protein_cal / 4, 1),  # 4 cal per gram
            'carbs_g': round(carbs_cal / 4, 1),
            'fat_g': round(fat_cal / 9, 1),  # 9 cal per gram
            'fiber_g': round(carbs_cal / 4 * 0.15, 1),  # ~15% of carbs
            'sugar_g': round(carbs_cal / 4 * 0.10, 1),
            'sodium_mg': 400,
            'confidence': 'medium',
            'breakdown': [{'item': 'user-provided', 'calories': calories}]
        }

def estimate_meal(description: str, user_calories: Optional[float] = None) -> Dict:
    """Standalone function for meal estimation"""
    estimator = CalorieEstimator()
    return estimator.estimate_meal(description, user_calories)

if __name__ == "__main__":
    # Test
    print("Test 1: 2 rotis with dal")
    result = estimate_meal("2 rotis with dal")
    print(result)
    
    print("\nTest 2: User provided 450 calories")
    result = estimate_meal("oatmeal with milk", user_calories=450)
    print(result)
