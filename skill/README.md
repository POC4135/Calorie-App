# Calorie Tracker Skill

A production-grade, multi-device calorie tracking system with AI-powered nutritional analysis, designed specifically for body recomposition goals with Indian cuisine expertise.

## Features

✅ **Multi-Device Sync** - Track from laptop and phone, automatically synced via GitHub
✅ **Indian Cuisine Database** - 200+ dishes with accurate portions and macros
✅ **Image Analysis** - Visual portion estimation from food photos
✅ **Smart Suggestions** - AI-generated pattern-based insights
✅ **Body Recomposition Tracking** - Optimized for 78kg, 29yo male, moderate activity
✅ **Interactive Dashboard** - Live Vercel-hosted dashboard with trends and analytics
✅ **Macro Targets** - Protein 156g, Fat 70g, Carbs 300g, Fiber 34g daily
✅ **Weight & Wellbeing Tracking** - Correlate nutrition with energy and progress

## Installation

### 1. Upload Skill to Claude

This skill needs to be installed in your Claude environment. Contact me if you need help with installation.

### 2. Setup GitHub Repository

1. Create GitHub repo: `https://github.com/POC4135/Calorie-App` (already done ✓)
2. Create Personal Access Token:
   - GitHub Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
   - Select repository: `Calorie-App`
   - Permissions: Contents (Read & Write)
   - Copy token

3. Create `ct_config.json`:
```json
{
  "github_token": "github_pat_YOUR_TOKEN_HERE",
  "github_repo": "POC4135/Calorie-App",
  "github_branch": "main"
}
```

4. Upload `ct_config.json` to Claude conversations (both laptop and phone)

### 3. Deploy Dashboard to Vercel

1. Connect GitHub repo to Vercel:
   - Go to https://vercel.com
   - Click "Add New Project"
   - Import `POC4135/Calorie-App`
   - Set Root Directory: `dashboard`
   - Deploy

2. Your dashboard URL: `https://calorie-app-orcin.vercel.app/`

### 4. Push Dashboard Files to GitHub

After first use, the skill will create:
- `calorie_tracker.db` - SQLite database
- `dashboard_data.json` - Dashboard data export
- `dashboard/index.html` - Dashboard HTML (already in repo)

The dashboard auto-updates when you log meals.

## Usage

### Trigger: `#ct`

All calorie tracker interactions start with `#ct` hashtag.

### Logging Meals

```
#ct had 2 rotis with dal and paneer sabzi for lunch
#ct 450 calories - oatmeal with banana and milk
#ct [upload food image]
#ct 2 dosas, sambar, coconut chutney
```

**Response includes:**
- Calorie and macro estimates
- Confidence level
- Today's running totals
- Wellbeing prompt

### Logging Weight

```
#ct weight 77.5kg
#ct 78kg weighed this morning
```

### Logging Wellbeing

```
#ct feeling tired and low energy
#ct energy 3 out of 5
```

After any meal, Claude will ask: "How's your energy level? (1-5)"

### Viewing Trends

```
#ct show trends
#ct dashboard
```

**Shows:**
- 7-day patterns
- Smart suggestions
- Macro deficits
- Dashboard link

### Custom Queries

```
#ct query protein last 7 days
#ct query days below 140g protein
#ct query restaurant vs home comparison
```

### Corrections

If estimate is wrong:

```
Actually that was 400 calories, not 550
```

Claude updates the last entry automatically.

## Dashboard

Visit: **https://calorie-app-orcin.vercel.app/**

**Sections:**
- Hero Stats: Today's totals vs targets
- 7-Day Macro Trends: Line chart
- 30-Day Weight Trend: Progress tracking
- Smart Suggestions: AI-generated insights
- Recent Meals: Last 20 entries

Auto-refreshes from GitHub on every page load.

## File Structure

```
calorie-tracker-skill/
├── SKILL.md                      # Main skill instructions
├── references/
│   └── indian_food_db.md         # 200+ Indian dishes database
├── scripts/
│   ├── db_manager.py             # SQLite operations
│   ├── github_ops.py             # GitHub sync
│   ├── calorie_estimator.py     # Nutritional analysis
│   └── pattern_analyzer.py      # Smart suggestions (TBD)
└── dashboard/
    └── index.html                # Vercel dashboard
```

## Database Schema

**Tables:**
- `meals` - Individual meal entries
- `daily_summary` - Daily aggregates
- `weight_log` - Weight tracking
- `wellbeing_log` - Energy/hunger tracking
- `user_profile` - Settings and targets
- `sync_queue` - Failed sync retry queue

## Macro Targets (Body Recomposition)

Based on 78kg, 29yo male, moderate activity (3-5x/week):

- **Protein**: 156g/day (1.8-2.2g/kg for muscle synthesis)
- **Fat**: 70g/day (0.8-1g/kg for hormonal health)
- **Carbs**: 300g/day (remaining calories, workout timing)
- **Fiber**: 34g/day (digestive health, satiety)
- **Sugar**: <50g/day (minimize added sugars)
- **Sodium**: <2,300mg/day (monitor closely, Indian diet)
- **Calories**: ~2,600 kcal/day (TDEE maintenance, no strict limit)

## Smart Suggestions Examples

**Pattern:** Your protein averages 95g on days with <3 meals (39% below target)
**Observation:** These days correlate with reported low energy at 3-4pm
**Recommendation:** Add 150g paneer (47g protein) to lunch or split into 4 meals
**Expected Impact:** Raises protein to 142g (91% of target), improves afternoon energy

## Confidence Levels

- **High (>70%)**: Exact database match, portion specified in grams
- **Medium (40-70%)**: Database match, portion estimated
- **Low (<40%)**: No match, visual estimate, unusual prep

## Multi-Device Sync

**How it works:**
1. You log meal on laptop → Claude syncs to GitHub
2. You log snack on phone → Claude pulls latest, merges, pushes
3. Dashboard always shows combined data from all devices

**Conflict resolution:** Timestamp-based ordering, no data loss

## Testing the Skill

Try these test cases:

1. **Basic meal**: `#ct had 2 rotis with dal for breakfast`
2. **User calories**: `#ct 300 calories - oatmeal with milk`
3. **Image**: Upload food photo with `#ct`
4. **Weight**: `#ct weight 77.2kg`
5. **Multi-item**: `#ct 2 parathas, yogurt, and pickle`
6. **Correction**: `#ct actually that was 400 calories`
7. **Trends**: `#ct show trends`
8. **Query**: `#ct query protein last week`

## Troubleshooting

**"Config file not found"**
- Upload `ct_config.json` to the conversation

**"GitHub sync failed"**
- Check token permissions (needs Contents: Read & Write)
- Verify repo name matches exactly
- Check network connection

**"Dashboard shows no data"**
- Log at least one meal first
- Wait 30 seconds for GitHub sync
- Refresh dashboard page

**"Estimates seem wrong"**
- Provide portion size in grams for accuracy
- Mention cooking method (fried/steamed)
- Correct estimates: "actually that was X calories"

## Limitations

- Image analysis: ±30% error margin for portions
- Database: ~200 dishes (expandable)
- Pattern analysis: Requires ≥14 days data
- Dashboard: Manual refresh (no live updates)

## Future Improvements

- Barcode scanning for packaged foods
- Restaurant menu API integration
- Meal planning based on macro gaps
- Fitness tracker integration for TDEE
- Social features (meal sharing, accountability)

## Support

For issues or questions:
1. Check this README
2. Review SKILL.md for detailed logic
3. Test with simple examples first
4. Check GitHub repo sync status

---

**Created:** May 12, 2026
**Version:** 1.0
**Target User:** Prakhar (78kg, 29yo, body recomp, moderate activity)
