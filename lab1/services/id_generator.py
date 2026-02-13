from datetime import date


class IdGenerator:
    def new_id(self, prefix: str) -> str:
        clean_prefix = prefix.strip()
        if not clean_prefix:
            clean_prefix = "id"
        return f"{clean_prefix}{date.today().strftime('%Y%m%d')}"
