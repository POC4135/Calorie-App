---
name: calorie-tracker
description: Multi-device calorie and macro tracking system with AI-powered nutritional analysis. Trigger whenever user includes '#ct' hashtag followed by meal description or food images. Handles Indian cuisine portions, estimates calories and macros (protein, carbs, fat, fiber, sugar, sodium), maintains SQLite database synced via GitHub, tracks weight and wellbeing, generates pattern-based insights for body recomposition goals. Also triggers for weight logging, wellbeing entries, trend queries, or dashboard access requests. Use this skill for ANY calorie tracking, meal logging, nutrition analysis, macro budget tracking, or dietary pattern analysis tasks.
---

# Calorie Tracker Skill

A production-grade multi-device calorie tracking system designed for body recomposition with intelligent pattern analysis and actionable nutritional insights.

## User Profile

- **Age**: 29 years old
- **Weight**: 78kg (tracked, updates via weight log entries)
- **Activity Level**: Moderately active (3-5 days/week moderate exercise)
- **Goal**: Body recomposition (simultaneous fat loss and muscle gain)
- **Dietary Context**: Indian diet (home-cooked and restaurant)
- **Measurement Preferences**: Grams, ml, or unit counts

## Macro Targets (Body Recomposition)

Based on user profile and body recomposition research:

- **Calories**: ~2,600 kcal/day (TDEE maintenance, no strict budget but tracked for trends)
- **Protein**: 156g/day (1.8-2.2g/kg target, critical for muscle synthesis)
- **Fat**: 70g/day (0.8-1g/kg, hormonal health)
- **Carbs**: 300g/day (remaining calories, timing around workouts)
- **Fiber**: 30-38g/day (digestive health, satiety)
- **Sugar**: <50g/day (minimize added sugars)
- **Sodium**: <2,300mg/day (Indian diet monitoring)

## Trigger Mechanism

**Primary trigger**: `#ct` hashtag followed by meal description or image

**Examples**:
- `#ct had 2 rotis with dal and paneer sabzi for lunch`
- `#ct [image of dosa plate]`
- `#ct 450 calories breakfast - oats with banana`
- `#ct weight 77.5kg` (weight logging)
- `#ct feeling tired, low energy` (wellbeing logging)
- `#ct show trends` (dashboard/analysis request)
- `#ct query protein last 7 days` (custom queries)

## Core Workflow

### 1. Initial Setup (First Use Only)

On first `#ct` trigger in any conversation:

1. Check for config file at `/mnt/user-data/uploads/ct_config.json`
2. If missing, prompt user to upload it with structure:
```json
{
  "github_token": "github_pat_...",
  "github_repo": "username/repo-name",
  "github_branch": "main"
}
```
3. Initialize database if not exists:
   - Create SQLite schema (see Database Schema section)
   - Create initial weight entry (78kg, current date)
   - Push to GitHub
4. If database exists in GitHub, pull and load locally

### 2. Meal Logging Workflow

**Input Processing**:
1. Parse meal description for:
   - Food items (extract specific dishes, ingredients)
   - Portion sizes (grams, ml, unit counts)
   - User-provided calorie count (if present, don't re-estimate)
   - Cooking method mentions (fried, steamed, boiled, baked, raw)
   - Location context (home, restaurant, outside)
   - Timing (if retroactive entry specified)

2. **Calorie and Macro Estimation**:
   - If user provides calorie count: use it, estimate only macros
   - If portion size given: use Indian food database (see references/indian_food_db.md)
   - If image provided: analyze visually (see Image Analysis section)
   - For multi-item meals: estimate each component, sum totals
   - Calculate confidence score (high/medium/low) based on:
     - Specificity of description (specific dish name vs "food")
     - Portion clarity (exact grams vs "some")
     - Image quality (if image used)
     - Database match quality (exact match vs approximation)

3. **Confirmation Logic**:
   - If confidence < 70% OR margin of error > 30%: confirm with user
   - Show estimate: "I estimate this is ~650 calories (520-780 range). Does that sound right?"
   - If user corrects: use their value as final
   - If confidence ≥ 70%: log directly, show what was logged

4. **Database Operations**:
   - Pull latest database from GitHub (conflict resolution)
   - Insert meal entry into `meals` table
   - Update `daily_summary` aggregates
   - Check sync queue for pending operations
   - Export to JSON for dashboard
   - Push to GitHub (both SQLite + JSON)
   - If push fails: add to sync_queue, mark unsynced

5. **Wellbeing Prompt**:
   - After logging meal: "How's your energy level right now? (1-5 scale, optional)"
   - If user responds: log to `wellbeing_log` table with linked_meal_id
   - If user skips: no problem, continue

6. **Response Format**:
```
Logged: 2 rotis (200g), dal (1 cup), paneer sabzi (150g)
Estimates:
  Calories: 685 kcal
  Protein: 38g (24% of daily target)
  Carbs: 95g (32% of daily target)
  Fat: 18g (26% of daily target)
  Fiber: 12g
  Confidence: High

Today's totals: 1,240 / ~2,600 kcal | Protein: 82g / 156g (53%)

How's your energy level? (1-5, or skip)
```

### 3. Image Analysis Workflow

When user shares food image with `#ct`:

1. **Visual Identification**:
   - Identify all food items in image
   - Note presentation style (plate, bowl, thali, banana leaf)
   - Identify surrounding objects for scale (phone, utensils, hands, cups)

2. **Portion Estimation**:
   - **Plate-based**: Assume standard 25cm diameter unless scale reference visible
   - **Volume estimation**: Use shadows, viewing angle, food height
   - **Scale references**: 
     - Phone visible: precise scaling (iPhone ~14-16cm height)
     - Hand visible: approximate scaling (adult hand ~18-20cm)
     - Utensils: spoon ~15cm, fork ~18cm
   - **Indian cuisine norms**: 
     - Thali portions (standard restaurant serving sizes)
     - Home-cooked visual portions
     - Roti/dosa size variations (6-8 inch typical)

3. **Confidence Scoring**:
   - High (>70%): Clear view, scale reference, single well-lit dish
   - Medium (40-70%): Partial occlusion, no scale, multiple dishes
   - Low (<40%): Poor lighting, unclear food, extreme angles

4. **Confirmation Logic**:
   - If confidence < 70%: "I see dosa with chutney and sambar. Estimating 2 medium dosas (~120g total), 3 tbsp chutney (~45g), 1 cup sambar (~240ml). Does this match what you had?"
   - If confidence ≥ 70%: Log directly, state estimate in response

5. **Image Handling**: Delete image after analysis (not stored in DB)

### 4. Weight Logging

Trigger: `#ct weight [value]kg` or `#ct [value]kg`

Examples:
- `#ct weight 77.5kg`
- `#ct 77.8kg weighed this morning`

Workflow:
1. Extract weight value
2. Insert into `weight_log` table with current timestamp
3. Update `user_profile` table
4. Sync to GitHub
5. Response: "Weight logged: 77.5kg (0.5kg since last entry 3 days ago)"

### 5. Wellbeing Logging

Trigger: `#ct feeling [description]` or `#ct energy [1-5]`

Examples:
- `#ct feeling tired and sluggish`
- `#ct energy 2 out of 5`
- `#ct hungry again 2 hours after lunch`

Workflow:
1. Parse energy level (1-5 scale) or sentiment
2. Extract hunger cues if present
3. Insert into `wellbeing_log` table
4. If recent meal (within 4 hours): link to that meal_id
5. Response: "Wellbeing logged. I'll correlate this with your nutrition patterns."

### 6. Trend Analysis and Dashboard

Trigger: `#ct show trends` / `#ct dashboard` / `#ct analysis`

Workflow:
1. Generate dashboard URL: User's Vercel deployment
2. Run pattern correlation analysis (see Pattern Analysis section)
3. Generate smart suggestions
4. Response format:
```
Dashboard: https://calorie-app-orcin.vercel.app/

Recent Patterns (last 7 days):
- Avg calories: 2,380 kcal/day (92% of maintenance)
- Protein: 128g/day (82% of target) - NEEDS IMPROVEMENT
- Fiber: 22g/day (73% of target)
- 3 days below 140g protein threshold

Smart Suggestions:
1. LOW PROTEIN ALERT: You averaged 95g protein on days with <3 meals (39% below target). These days correlate with reported low energy at 3-4pm. Add 150g paneer (47g protein) to lunch or split into 4 meals. Expected impact: raises protein to 142g (91% of target).

2. FIBER OPPORTUNITY: Your fiber intake averages 18g on restaurant days vs 28g on home days. Restaurant meals lack vegetables. Add side salad or request extra vegetables.

Visit dashboard for full visualizations and weight trends.
```

### 7. Custom Queries

Trigger: `#ct query [description]`

Examples:
- `#ct query protein last 7 days`
- `#ct query days below 140g protein this month`
- `#ct query restaurant vs home macro comparison`

Workflow:
1. Parse query intent
2. Map to built-in query function (see Query Functions section) OR construct SQL
3. Execute query against local database
4. Format results as table or summary
5. If complex analysis needed, suggest viewing dashboard

Built-in Query Functions:
- `query_daily_summary(start_date, end_date)` - daily aggregates
- `query_macro_trends(days=30)` - rolling averages
- `query_protein_deficit_days(threshold=156)` - days below target
- `query_meal_timing_pattern()` - frequency and timing analysis
- `query_weight_correlation()` - weight vs calorie/macro trends
- `query_location_breakdown()` - home vs restaurant comparison
- `query_cooking_method_impact()` - cooking method macro differences
- `custom_query(sql)` - arbitrary SQL execution

## Database Schema

**File**: `calorie_tracker.db` (SQLite)
**Location**: Local session + GitHub repo root
**Export**: `dashboard_data.json` (for Vercel dashboard)

### Tables

#### meals
Primary meal logging table.

```sql
CREATE TABLE meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,  -- ISO 8601 with timezone
    date TEXT NOT NULL,  -- YYYY-MM-DD for aggregation
    meal_description TEXT NOT NULL,
    calories REAL NOT NULL,
    protein_g REAL,
    carbs_g REAL,
    fat_g REAL,
    fiber_g REAL,
    sugar_g REAL,
    sodium_mg REAL,
    portion_size TEXT,  -- "150g", "2 rotis", "1 cup"
    portion_grams REAL,  -- normalized to grams
    user_provided_calories INTEGER DEFAULT 0,  -- boolean
    cooking_method TEXT,  -- fried/steamed/boiled/raw/baked
    meal_location TEXT,  -- home/restaurant/outside
    estimate_confidence TEXT,  -- high/medium/low
    image_analyzed INTEGER DEFAULT 0,  -- boolean
    notes TEXT,
    synced_to_github INTEGER DEFAULT 0,  -- boolean
    device_id TEXT  -- for conflict resolution
);
```

#### daily_summary
Aggregated daily totals, updated after each meal entry.

```sql
CREATE TABLE daily_summary (
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
);
```

#### weight_log
Weight tracking over time.

```sql
CREATE TABLE weight_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    weight_kg REAL NOT NULL,
    timestamp TEXT NOT NULL,
    notes TEXT
);
```

#### wellbeing_log
Energy, hunger, and mood tracking for correlation analysis.

```sql
CREATE TABLE wellbeing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    energy_level INTEGER,  -- 1-5 scale
    hunger_level INTEGER,  -- 1-5 scale
    notes TEXT,
    linked_meal_id INTEGER,  -- foreign key to meals.id
    FOREIGN KEY (linked_meal_id) REFERENCES meals(id)
);
```

#### user_profile
Key-value store for user settings and metadata.

```sql
CREATE TABLE user_profile (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

Initial entries:
- `age`: 29
- `weight_kg`: 78
- `activity_level`: moderate
- `goal`: body_recomp
- `protein_target_g`: 156
- `fat_target_g`: 70
- `carbs_target_g`: 300
- `fiber_target_g`: 34
- `sugar_limit_g`: 50
- `sodium_limit_mg`: 2300

#### sync_queue
Queue for failed GitHub operations, retry on next sync.

```sql
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,  -- insert/update/delete
    table_name TEXT NOT NULL,
    record_id INTEGER,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    synced INTEGER DEFAULT 0  -- boolean
);
```

## Pattern Analysis Engine

Run automatically during trend/dashboard requests, also weekly background analysis.

### Correlation Patterns

1. **Protein-Energy Correlation**
   - Query: Days with protein < 140g
   - Check: Wellbeing logs on those days
   - Pattern: Low protein → afternoon energy dips?
   - Recommendation: Protein timing and amounts

2. **Fiber-Satiety Correlation**
   - Query: Meal time gaps by fiber intake
   - Pattern: High fiber meals → longer satiety duration?
   - Recommendation: Fiber distribution across meals

3. **Sugar-Energy Correlation**
   - Query: Sugar intake vs energy crashes
   - Pattern: High sugar → energy instability?
   - Recommendation: Sugar reduction strategies

4. **Meal Timing Irregularity**
   - Query: Variance in meal timing day-to-day
   - Pattern: Irregular timing → hunger spikes?
   - Recommendation: Consistent meal schedule

5. **Cooking Method Impact**
   - Query: Fried vs steamed calorie differences
   - Pattern: Cooking method accuracy drift?
   - Recommendation: Adjust portion assumptions

6. **Location Analysis**
   - Query: Home vs restaurant macro differences
   - Pattern: Restaurant → lower protein, higher sodium?
   - Recommendation: Restaurant ordering strategies

7. **Weekend vs Weekday**
   - Query: Macro patterns by day of week
   - Pattern: Weekend protein drops?
   - Recommendation: Weekend meal prep

8. **Weight-Calorie Correlation**
   - Query: Weight change vs calorie trends
   - Pattern: Plateau despite calorie deficit?
   - Recommendation: Reverse diet or refeed strategy

### Suggestion Generation Format

```
Pattern: [Observation from data]
Observation: [Correlation found]
Recommendation: [Specific actionable step]
Expected Impact: [Quantified outcome]
```

Example:
```
Pattern: Your protein averages 95g on days with <3 meals (39% below target)
Observation: These days correlate with reported low energy at 3-4pm
Recommendation: Add 150g paneer (47g protein) to lunch or split into 4 meals
Expected Impact: Raises protein to 142g (91% of target), improves afternoon energy
```

## Conflict Resolution (Multi-Device Sync)

**Problem**: Laptop and phone both logging simultaneously, need to merge without data loss.

**Solution**: Pull-merge-push with timestamp-based ordering and queue retry.

### Sync Algorithm

```
1. Pre-Log Check:
   - Read ct_config.json for GitHub credentials
   - Fetch latest calorie_tracker.db from GitHub
   - Load into local SQLite

2. Merge Check:
   - Query sync_queue for unsynced operations
   - Apply queued operations in timestamp order
   - Check for conflicts (same device_id + timestamp)
   - If conflict: keep both entries, flag for review

3. New Entry:
   - Insert meal/weight/wellbeing entry
   - Update daily_summary aggregates
   - Export to dashboard_data.json

4. Push Attempt:
   - Git add calorie_tracker.db + dashboard_data.json
   - Git commit with message: "Log from [device_id] at [timestamp]"
   - Git push to GitHub

5. Failure Handling:
   - If push fails: add operation to sync_queue
   - Mark entry as synced=0
   - Response includes: "Logged locally. Will sync when online."
   - Next successful sync: process queue, retry failed operations

6. Device ID Generation:
   - First use in session: generate UUID, store in session
   - Include in every database write
   - Used for conflict detection and debugging
```

### Edge Cases

- **Simultaneous logs within same second**: Use device_id as tiebreaker, keep both
- **Database corrupted in GitHub**: Prompt user, offer to restore from local
- **Sync queue grows large (>50 items)**: Warn user, suggest manual sync check
- **GitHub rate limits**: Exponential backoff, queue locally, retry

## GitHub Integration

**Files in repo**:
- `calorie_tracker.db` - SQLite database (binary)
- `dashboard_data.json` - Exported data for Vercel dashboard
- `dashboard/` - Dashboard HTML/CSS/JS (see Dashboard section)

**Commit messages**:
- `Initial database setup`
- `Log from [device_id] at [timestamp]`
- `Weight update: [weight]kg`
- `Dashboard data refresh`

**Branch**: Always use branch specified in config (typically `main`)

## Indian Food Database

**File**: `references/indian_food_db.md`

Contains:
- 200+ common Indian dishes with portion sizes and macros
- Regional variations (North Indian, South Indian, Bengali, Gujarati)
- Cooking method adjustments (fried vs steamed, ghee vs oil)
- Restaurant vs home-cooked multipliers
- Street food items
- Desserts and snacks

**Usage**: When user mentions a dish name, lookup in database for baseline estimates.

**Example entries**:
- Roti (whole wheat): 100 kcal, 3g protein, 18g carbs, 2.5g fat per piece (~40g)
- Paratha (plain): 180 kcal, 4g protein, 25g carbs, 7g fat per piece (~60g)
- Paneer tikka: 265 kcal, 18g protein, 8g carbs, 18g fat per 150g serving
- Biryani (chicken): 350 kcal, 22g protein, 45g carbs, 10g fat per cup (240g)

## Dashboard Specification

**File**: `scripts/generate_dashboard.py` (generates dashboard HTML)
**Output**: `dashboard/index.html` (committed to GitHub, auto-deployed by Vercel)

### Dashboard Sections

#### 1. Hero Stats (Top Cards)
- Today's calories, protein, carbs, fat (with % ring charts vs targets)
- Current weight with 7-day trend sparkline
- Logging streak counter (consecutive days with entries)

#### 2. Macro Overview (Main Content)
- Stacked area chart: 30-day calorie/protein/carbs/fat trends
- Gauge charts: Today's macros as % of targets
- Heatmap: 90-day protein adequacy (color-coded: green >90%, yellow 70-90%, red <70%)

#### 3. Pattern Insights (Right Sidebar)
- AI-generated smart suggestions (refreshed weekly)
- Meal timing distribution (24-hour clock visualization)
- Cooking method breakdown (pie chart: fried/steamed/boiled/raw)
- Location analysis (home vs restaurant macro comparison bar chart)

#### 4. Correlation Analysis (Expandable Section)
- Scatter plot: Protein intake vs energy levels
- Line chart: Weight trend vs calorie trend (dual-axis, 90 days)
- Bar chart: Fiber intake vs meal satiety duration

#### 5. Recent Logs (Bottom Table)
- Last 20 meal entries with expandable details
- Columns: Date/Time, Meal, Calories, Protein, Carbs, Fat, Location, Confidence
- Filters: Date range, location, confidence level
- Export button: Download as CSV

#### 6. Quick Actions (Floating Action Buttons)
- Refresh dashboard data
- View sync status
- Download full database (SQLite file)
- Open custom query interface

### Styling
- **Aesthetic**: Minimal, clinical, data-focused
- **Colors**: 
  - Background: #FFFFFF (white)
  - Primary: #2563EB (blue)
  - Success: #10B981 (green)
  - Warning: #F59E0B (amber)
  - Danger: #EF4444 (red)
  - Text: #111827 (near-black)
  - Borders: #E5E7EB (light gray)
- **Typography**: 
  - Headings: Inter, 600 weight
  - Body: Inter, 400 weight
  - Monospace: JetBrains Mono (for numbers, SQL)
- **Layout**: CSS Grid, mobile-responsive (breakpoint 768px)

### Data Loading
- Dashboard reads from `dashboard_data.json` in repo root
- JSON structure:
```json
{
  "meals": [...],  // recent 90 days
  "daily_summary": [...],  // 90 days
  "weight_log": [...],  // all entries
  "wellbeing_log": [...],  // 90 days
  "user_profile": {...},
  "suggestions": [...],  // latest AI suggestions
  "last_updated": "2026-05-12T14:30:00Z"
}
```
- Auto-refresh on page load (always fetches latest from GitHub)
- Manual refresh button for immediate update

## Error Handling

### Common Errors and Responses

1. **Config file missing**:
   - "I need your GitHub config to sync data. Please upload ct_config.json with your GitHub token and repo details."
   - Show example structure

2. **GitHub push failed**:
   - Log locally, add to sync_queue
   - "Logged locally. GitHub sync failed (network issue?). Will retry on next log."

3. **Invalid food description**:
   - "I couldn't identify any food items. Can you describe what you ate more specifically?"
   - Example: "#ct food" → too vague

4. **Image analysis failed**:
   - "I couldn't analyze this image clearly. Can you describe the meal and portion sizes?"

5. **Database corruption**:
   - "Database appears corrupted. I can restore from your last GitHub backup. Proceed?"
   - If yes: fetch from GitHub, overwrite local

6. **Conflicting entries**:
   - Rare, but if timestamp collision detected: log both, flag for review
   - "I detected duplicate entries from different devices. Both are saved. Check dashboard."

7. **User corrects estimate**:
   - "Got it, updating to 400 calories instead of my estimate of 550."
   - Update last entry, re-sync

## Script Reference

### scripts/db_manager.py
Core database operations: init, insert, update, query, sync.

Functions:
- `init_database()` - create schema, initial data
- `insert_meal(meal_data)` - add meal entry
- `update_daily_summary(date)` - recalculate daily aggregates
- `sync_to_github(db_path, config)` - push to GitHub
- `pull_from_github(config)` - fetch latest from GitHub
- `process_sync_queue()` - retry failed operations
- `export_to_json(db_path)` - generate dashboard JSON

### scripts/calorie_estimator.py
Nutritional analysis and estimation logic.

Functions:
- `estimate_meal(description, portion, user_cal)` - main estimation
- `lookup_indian_food(dish_name)` - database lookup
- `analyze_image(image_path)` - visual portion estimation
- `calculate_macros(calories, dish_type)` - macro breakdown
- `confidence_score(factors)` - estimate confidence level

### scripts/pattern_analyzer.py
Correlation analysis and smart suggestions.

Functions:
- `analyze_protein_energy_correlation(db_path, days)` - protein vs energy
- `analyze_fiber_satiety(db_path, days)` - fiber vs meal gaps
- `analyze_meal_timing(db_path, days)` - timing patterns
- `analyze_location_impact(db_path, days)` - home vs restaurant
- `generate_suggestions(analysis_results)` - create actionable insights

### scripts/generate_dashboard.py
Dashboard HTML generation.

Functions:
- `generate_dashboard_html(json_data)` - create full HTML
- `create_chart_config(data, type)` - Chart.js configs
- `calculate_trends(data, days)` - rolling averages
- `format_suggestions(suggestions)` - suggestion cards

### scripts/github_ops.py
GitHub API interactions.

Functions:
- `authenticate(config)` - validate token
- `fetch_file(repo, path, branch)` - download file
- `push_file(repo, path, content, message, branch)` - upload file
- `check_rate_limit()` - API quota check

## Testing the Skill

Create test cases covering:

1. **Basic meal logging**:
   - `#ct had 2 rotis with dal for breakfast`
   - `#ct 300 calories - oatmeal with milk`
   
2. **Image analysis**:
   - Upload thali image with `#ct`
   - Upload dosa plate with `#ct this was my lunch`

3. **Weight logging**:
   - `#ct weight 77.2kg`
   - `#ct 78kg this morning`

4. **Multi-item meals**:
   - `#ct 2 parathas, yogurt, and pickle`
   - `#ct rice, dal, two sabzis, raita`

5. **Corrections**:
   - Log meal, then: `#ct actually that was 400 calories not 600`

6. **Trends**:
   - `#ct show trends`
   - `#ct query protein last week`

7. **Multi-device sync**:
   - Log from laptop, then immediately from phone
   - Check both entries appear in database

8. **Wellbeing**:
   - After meal log, respond to energy prompt: `3`
   - Separate entry: `#ct feeling hungry 2 hours after lunch`

## Success Criteria

- Meal logged within 10 seconds (including GitHub sync)
- Calorie estimates within ±20% of actual (for known portions)
- Image analysis confidence >70% for clear, well-lit images
- Dashboard updates within 30 seconds of logging
- Zero data loss across device switches
- Pattern suggestions actionable and specific (not generic)
- User correction rate <10% (estimates are accurate enough)

## Limitations and Future Improvements

**Current limitations**:
- Image analysis ±30% error margin for portions
- Indian food database covers ~200 dishes (expandable)
- Pattern analysis requires ≥14 days of data for reliable insights
- Dashboard auto-refresh requires page reload (no WebSocket live updates)

**Potential improvements**:
- Barcode scanning for packaged foods
- Restaurant menu API integration
- Meal photo gallery (requires cloud storage decision)
- Meal planning and suggestions based on macro gaps
- Integration with fitness tracker for TDEE adjustments
- Social features (meal sharing, accountability partners)

---

**End of SKILL.md**

For Indian food database details, see `references/indian_food_db.md`.
For complete Python implementation, see `scripts/` directory.
