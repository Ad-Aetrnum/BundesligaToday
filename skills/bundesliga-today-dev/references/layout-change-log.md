# Layout Change Log

## 2026-06-16 Session

### TS Goals Column — Assists Format
- **Format**: `"goals/assists"` displayed as e.g. `"35/12"` (goals/assists with slash separator)
- **Data requirement**: Each scorer dict must include both `"goals"` and `"assists"` fields
- **Fallback**: If `assists` is `"0"` or missing, only goals number is shown
- **Column width**: 25px → **45px** (to fit the "35/12" format)

### TS Column Widths — Updated
- Rank=25, Name=160 (was 150), Club=135 (was 140), Goals=45 (was 25)
- Total data width: 365px, border tw=523px (unchanged)

## 2026-06-03 Session

### Column Widths — Final Values
- **MR**: Home=140, Score=45, Away=140 (total data=325px, border mw=350px)
- **TS**: Rank=25, Name=160, Club=135, Goals=45 (total=365px, border tw=523px)

### Heading Changes
- "MD 34 RESULTS" → "Matchday 34 Results" (title case, centered)
- "TOP SCORERS" → "Top Scorers" (title case, centered)

### Separator Lines (MR & TS)
- **Color**: Dark gray `(80, 80, 80)` for both MR and TS
- **Width**: 75% of border width, centered
- **Thickness**: 4px
- **Gap above heading**: 20px
- **Gap below separator**: 10px

### MR Layout
- Top edge aligned with ST top: `my = sy0`
- Left edge aligned with TS left: `mx = tx0` (computed BEFORE drawing data)
- Width: `mw = 350` (fixed, independent of TS)
- Height: dynamic — `mh = heading_h + actual_rows * mr_row_h + 24 + 50`
  - heading_h = text_height + 20 (gap) + 4 (line) + 10 (gap)
  - +24 bottom padding + 50px extension
- Up to 9 matches shown
- Dark gray separator line (75% width, centered) under heading

### TS Layout
- Bottom edge aligned with ST bottom: `ty0 = ts_bottom - th_`
- Width: `tw = 523`
- Height: dynamic — `th_ = ts_heading_h + actual_ts_rows * ts_row_h + 8 + 50`
  - +8px top padding + 50px bottom extension
- Up to 10 scorers shown
- Dark gray separator line (75% width, centered) under heading
- Name column: 160px

### Borders
- Only ST, MR, TS have black borders `(0,0,0,255)`, width=2
- Header and Footer borders removed
- Grid lines removed

### Footer Separator
- Dark gray `(80,80,80)`, 800px wide, centered, 8px above footer, width=3px

### Key Pitfalls Discovered
1. When removing separator lines, don't delete preceding `draw.textbbox()` calls
2. Compute `tx0` BEFORE drawing MR data (otherwise data uses old `mx`, border uses new)
3. When refactoring, don't accidentally remove `data.get()` calls
4. "Shift right edge" = change width only; "shift left edge" = change position + inverse width
5. ST border drawn twice (standalone + DEBUG_BORDERS) — keep both in sync
6. MR and TS widths are INDEPENDENT — only left edge is shared
7. When adding/removing separator lines, update `heading_h` and `mh`/`th_` calculations accordingly
