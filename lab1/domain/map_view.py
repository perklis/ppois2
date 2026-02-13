from exceptions import ValidationError


class MapView:
    def __init__(self, rows: list[str], cols: int) -> None:
        if not rows:
            raise ValidationError("Карта должна иметь хотя бы одну строку")
        if int(cols) <= 0:
            raise ValidationError("Карта должна иметь хотя бы один столбец")

        self.rows = [r.strip().upper() for r in rows]
        self.cols = int(cols)

        self._cell_w = 3 

    def render(self, occupied_cells: dict[str, str]) -> str:
        indent = " " * 4

        header_cells = [str(i).rjust(self._cell_w) for i in range(1, self.cols + 1)]
        lines = [indent + "".join(header_cells)]

        for r in self.rows:
            row_cells = []
            for c in range(1, self.cols + 1):
                cell_id = f"{r}{c}"
                mark = "X" if cell_id in occupied_cells else "."
                row_cells.append(mark.rjust(self._cell_w))
            lines.append(r.rjust(3) + " " + "".join(row_cells))

        lines.append("")
        lines.append("X — достопримечательность,. — пусто")
        return "\n".join(lines)

    def normalize_cell_id(self, cell_id: str) -> str:
        v = cell_id.strip().upper()
        if len(v) < 2:
            raise ValidationError("Введите клетку карты(A1)")
        return v
