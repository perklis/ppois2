SPECIAL_BOMB = "bomb"
SPECIAL_LINE_H = "line_h"
SPECIAL_LINE_V = "line_v"
SPECIAL_COLOR = "color"

def special_positions(special_type, pos, rows, cols, target_color=None, grid=None):
    
    r, c = pos
    affected = set()

    if special_type == SPECIAL_BOMB:
        for rr in range(r - 1, r + 2):
            for cc in range(c - 1, c + 2):
                if 0 <= rr < rows and 0 <= cc < cols:
                    affected.add((rr, cc))
    elif special_type == SPECIAL_LINE_H:
        for cc in range(cols):
            affected.add((r, cc))
    elif special_type == SPECIAL_LINE_V:
        for rr in range(rows):
            affected.add((rr, c))
    elif special_type == SPECIAL_COLOR and grid is not None:
        if target_color is None:
            return affected
        for rr in range(rows):
            for cc in range(cols):
                jewel = grid[rr][cc]
                if jewel and jewel.color_id == target_color:
                    affected.add((rr, cc))
        affected.add((r, c))

    return affected
