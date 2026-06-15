---
name: bundesliga-today-dev
description: Development context and workflows for the Bundesliga Today Telegram bot (@BLTD_bot) — Pillow-based rendering pipeline, coordinate system, layout conventions, and iterative design workflow.
---

# Bundesliga Today — Development Context

## Project Overview

`@BLTD_bot` generates magazine-style Bundesliga infographics as PNG images using Pillow (not Playwright/HTML). The bot sends matchday results, standings tables, and top scorers to Telegram.

**Key files:**
- `render_final.py` — Main rendering script (Pillow-based)
- `output/` — Generated PNG output directory
- Fonts: Bebas Neue, Inter, Oswald (local only, never remote Google Fonts)

## Coordinate System

All layout coordinates use a **reference-based scaling system**:

```python
# Reference dimensions (design canvas)
REF_W = 2000
REF_H = 2500

# Scale factors based on actual canvas size
sx = cw / REF_W
sy = ch / REF_H

def S(x, y, w, h):
    """Scale a rectangle from reference coords to actual."""
    return int(x * sx), int(y * sy), int(w * sx), int(h * sy)
```

**CRITICAL:** All coordinates in the code are in **reference space** (pre-scaling). Never mix reference and actual pixel values.

## Layout Zones (Reference Coordinates)

| Zone | Ref Coords (x, y, w, h) | Notes |
|------|-------------------------|-------|
| Header | S(237, 324, 1445, 80) | Season + matchday text |
| Standings Table | S(352, 659, 1032, 1675) | Left side; sx0 shifted -5px from original 357 |
| Matchday Results | S(1159, sy0, 350, dynamic) | Top-right; top edge aligned with ST top (my=sy0); width=350; height is dynamic: heading + separator (75% width, 4px) + rows + 24px bottom padding + 50px extension. Left edge = TS left edge (mx=tx0). |
| Top Scorers | S(1159, dynamic, 523, dynamic) | Bottom-right; ty0 computed to align bottom edge with ST bottom; fits up to 10 rows; height is dynamic: heading + separator (75% width, 4px) + rows + 8px top padding + 50px bottom extension. Per-column fonts: Name/Rank=40px, Club=34px, Goals=36px. Club and Goals vertically centered via dy offset. |
| Footer | S(87, 1984, 1745, 50) | "Updated After Matchday N" |

## Separator Lines

Both MR and TS have a **dark gray** `(80, 80, 80)` separator line under their heading:
- Width: 75% of border width, centered
- Thickness: 4px
- Gap above heading: 20px
- Gap below separator: 10px

### MR Dynamic Height
```python
heading_h = (bbox[3] - bbox[1]) + 20 + 4 + 10  # heading + 20px gap + 4px line + 10px gap
mh = heading_h + actual_rows * mr_row_h + 24 + 50  # +24px bottom padding + 50px extension
```

### TS Dynamic Height (bottom-aligned)
```python
ts_heading_h = (bbox[3] - bbox[1]) + 20 + 4 + 10  # heading + 20px gap + 4px line + 10px gap
actual_ts_rows = min(len(top_scorers), 10)
ts_bottom = sy0 + total_table_h + 2  # ST bottom including border
th_ = ts_heading_h + actual_ts_rows * ts_row_h + 8 + 50  # 8px top padding + 50px bottom extension
ty0 = ts_bottom - th_
```

## Column Widths

### Matchday Results
| Column | Width |
|--------|-------|
| Home | 140px |
| Score | 45px |
| Away | 140px |

### Top Scorers (up to 10 rows)
| Column | Width | Font Size |
|--------|-------|-----------|
| Rank | 25px | 40px (sf_cell) |
| Name | 160px | 40px (sf_cell) |
| Club | 100px | 34px (sf_club, -6px) |
| Goals | 45px | 36px (sf_goals, -4px) |

**Vertical alignment:** Club and Goals text are vertically centered within the row height (ts_row_h) relative to Name. Computed per-row via `dy = (ts_row_h - font_height) // 2`.

**Goals column format:** `"goals/assists"` (e.g., `"35/12"`). Each scorer dict must include both `"goals"` and `"assists"` fields. If assists is `"0"` or missing, display only goals.

### Standings Table
| Column | Width |
|--------|-------|
| # | 52px |
| Club | 292px |
| W/D/L/GF/GA/PTS | 32px each |

## Rendering Rules

1. **Text truncation:** Home/Away names `[:12]`, scorer names `[:16]`, clubs `[:12]`
2. **Row limits:** MR shows up to 9 matches (`matchday_results[:9]`), TS shows up to 10 scorers (`top_scorers[:10]`)
3. **Alignment:** All columns are **left-aligned** with 4px padding (`col_x + 4`)
4. **Headings:** MR heading is `"Matchday {N} Results"`, TS heading is `"Top Scorers"`. Both are **centered** within their section width.
5. **TS Goals format:** Display as `"goals/assists"` (e.g., `"35/12"`). Each scorer dict must include `"assists"` field. If assists is `"0"` or missing, show only goals number.
6. **No grid lines:** The 50px red grid and separator lines have been removed
7. **Borders:** Only ST, MR, TS have black borders `(0, 0, 0, 255)`, width=2. Header and Footer borders removed.
8. **Footer separator:** Dark gray `(80, 80, 80)` line, 800px wide, centered, 8px above footer, width=3px
9. **MR/TS separator lines:** Dark gray `(80, 80, 80)`, 4px thick, 75% of border width, centered, drawn under heading with 20px gap above and 10px gap below
10. **Font loading:** Use `get_font("oswald", int(size * sx))` — always scale by `sx`
10. **MR top alignment:** `my = sy0` — MR top edge always matches ST top edge
11. **MR dynamic height:** `mh = heading_h + actual_rows * mr_row_h + 24 + 50` — computed from actual rows + 24px padding + 50px extension. Never hardcode `mh`.
12. **MR width:** `mw = 350` — fixed width, independent of TS width.
13. **TS dynamic height:** `th_ = ts_heading_h + actual_ts_rows * ts_row_h + 8 + 50` — computed from actual rows + 8px top padding + 50px bottom extension. `ty0 = ts_bottom - th_` aligns bottom with ST.
14. **MR left edge = TS left edge:** `mx = tx0`. Compute `tx0` BEFORE drawing MR data.

## Common Pitfalls

### 1. Deleting `draw.textbbox()` calls
When removing separator lines, be careful NOT to delete the preceding `bbox = draw.textbbox(...)` line — it's needed for the `ty += (bbox[3] - bbox[1]) + N` calculation that positions the next element.

### 2. TS height and alignment
TS uses dynamic height computation with bottom alignment to ST. Don't hardcode `ty0` or `th_` — always compute from the formula. The `ts_heading_h` includes the separator line: `(bbox[3] - bbox[1]) + 20 + 4 + 10`.

### 3. Coordinate shifts affect dependent variables
When shifting `mx` or `tx0`, the internal column positions auto-adjust because they're computed from `mx`/`tx0`. But `sx0` shifts require updating the ST border rectangle too.

### 4. Compute shared coordinates BEFORE drawing data
When MR and TS must share the same left edge (`mx = tx0`), compute `tx0` **before** drawing MR data. If `mx` is reassigned after the MR drawing loop, the data will use the old `mx` while the border uses the new one.

### 5. MR and TS bottom padding and extension
- MR: `mh = heading_h + actual_rows * mr_row_h + 24 + 50` (24px bottom padding + 50px extension)
- TS: `th_ = ts_heading_h + actual_ts_rows * ts_row_h + 8 + 50` (8px top padding + 50px bottom extension)

### 6. Shifting right edge vs left edge
When the user says "shift right edge left/right", only change `mw`/`tw` (width), keeping `mx`/`tx0` fixed. When they say "shift left edge", change `mx`/`tx0` and adjust `mw`/`tw` inversely.

### 7. Don't forget `data.get()` calls
When refactoring sections, don't accidentally remove `matchday_results = data.get("matchday_results", [])` or `top_scorers = data.get("top_scorers", [])`.

### 8. MR and TS widths are independent
MR width (`mw = 350`) and TS width (`tw = 523`) are set independently. Only the **left edge** is shared (`mx = tx0`).

### 9. Per-column font sizes in TS
Different TS columns use different font sizes: Rank/Name = 40px (`sf_cell`), Club = 34px (`sf_club`, -6px), Goals = 36px (`sf_goals`, -4px). When reducing Club width, also reduce its font size to keep text fitting. Always define the font variable before the column width section and reference it in the draw loop.

**Vertical centering with mixed fonts:** When columns in the same row use different font sizes, compute per-row vertical offset to center smaller text. See `references/vertical-centering.md` for the pattern and current values.

### 10. Watch for duplicate variable names when patching
When using `patch` to replace font definitions, the `old_string` may match multiple locations (e.g., MR and TS both have `sf_heading`). Always include enough surrounding context to make the match unique, or use `replace_all=True` intentionally. A bad patch can delete a needed variable (e.g., `sf_goals`) and create a duplicate of another (e.g., two `sf_club` lines). After patching, verify the surrounding lines are correct before running.

### 11. TS Goals column — assists format
The Goals column displays `"goals/assists"` as `"35/12"`. Each scorer dict in `top_scorers` must include an `"assists"` field. If `assists` is `"0"` or missing, only the goals number is shown. The column width is 45px. When adding new test data, always include both `"goals"` and `"assists"` keys.

## Workflow

1. Read current `render_final.py` to understand state before editing
2. Edit coordinates/widths in `render_final.py`
3. Run: `cd ~/.hermes/BundesligaToday && python render_final.py`
4. Script auto-sends to Telegram (BLTD bot + EPS_A bot duplicate)
5. Review image, iterate — user gives short correction instructions

**CRITICAL: Always read the relevant section of the file before patching.** Use `search_files` with `context=2` to find the exact lines, then verify with `read_file` at that offset.

## Communication Style

- User works iteratively with short instructions ("сделай так", "убери сетку", "сдвинь на 5px")
- Make the change directly — don't ask clarifying questions unless truly ambiguous
- When user says "отмени изменения" with numbered items, revert exactly those items
- Keep responses minimal: confirm what was done, don't explain the code
- If a change breaks the build, fix it silently and re-run
- Always verify the result works (run the script) before reporting success

## Change Log

See `references/layout-change-log.md` for a history of column width iterations, heading changes, and coordinate shifts.
