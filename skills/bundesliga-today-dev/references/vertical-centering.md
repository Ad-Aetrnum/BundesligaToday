# Vertical Centering with Mixed Font Sizes in Pillow

## Problem
When table columns use different font sizes, text aligns at the baseline but appears visually off-center within the row.

## Solution
Compute per-row vertical offset for each column based on its font height vs the row height:

```python
# In the row drawing loop:
club_bbox = draw.textbbox((0, 0), club_text, font=sf_club)
club_h = club_bbox[3] - club_bbox[1]
club_dy = (ts_row_h - club_h) // 2

goals_bbox = draw.textbbox((0, 0), goals_text, font=sf_goals)
goals_h = goals_bbox[3] - goals_bbox[1]
goals_dy = (ts_row_h - goals_h) // 2

# Draw: Name at base y, Club/Goals shifted down by dy
draw.text((name_x, ty_ts), name_text, font=sf_cell)           # base
draw.text((club_x, ty_ts + club_dy), club_text, font=sf_club) # centered
draw.text((goals_x, ty_ts + goals_dy), goals_text, font=sf_goals) # centered
```

## Current TS Font Sizes
| Column | Font Variable | Size | dy (at ts_row_h=50sy) |
|--------|--------------|------|----------------------|
| Rank | sf_cell | 40px | 0 (base) |
| Name | sf_cell | 40px | 0 (base) |
| Club | sf_club | 34px | ~3px |
| Goals | sf_goals | 36px | ~2px |

## Notes
- `draw.textbbox()` is used instead of `font.getsize()` (deprecated in Pillow 10+)
- The largest font in the row should use the base `ty_ts` (no offset)
- Only smaller fonts need a positive `dy` to push them down toward center
