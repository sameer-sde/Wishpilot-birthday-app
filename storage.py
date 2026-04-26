import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "birthdays.json"
SETTINGS_FILE = BASE_DIR / "settings.json"


DEFAULT_SETTINGS = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "",
    "sender_name": "WishPilot",
    "password": "",
    "use_tls": True,
    "music_enabled": False,
    "scheduler_enabled": True,
    "check_hour": 9,
    "check_minute": 0,
    "upcoming_days": 30,
    "theme": "dark",
    "music_file": "",
    "last_auto_run": "",
}


class Storage:
    def __init__(self):
        self._ensure_files()

    def _ensure_files(self):
        if not DATA_FILE.exists():
            self._write_json(DATA_FILE, [])
        if not SETTINGS_FILE.exists():
            self._write_json(SETTINGS_FILE, dict(DEFAULT_SETTINGS))

    def _read_json(self, path, fallback):
        try:
            raw = path.read_text(encoding="utf-8").strip()
            if not raw:
                raise ValueError("Empty JSON file")
            data = json.loads(raw)
            return data
        except (json.JSONDecodeError, FileNotFoundError, ValueError, TypeError):
            safe_fallback = dict(fallback) if isinstance(fallback, dict) else list(fallback)
            self._write_json(path, safe_fallback)
            return safe_fallback

    def _write_json(self, path, payload):
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def _read_contacts(self):
        data = self._read_json(DATA_FILE, [])
        return data if isinstance(data, list) else []

    def _write_contacts(self, contacts):
        self._write_json(DATA_FILE, contacts)

    def list_contacts(self):
        return self._read_contacts()

    def get_contact(self, contact_id):
        for row in self._read_contacts():
            if row.get("id") == contact_id:
                return row
        return None

    def add_contact(self, payload):
        contacts = self._read_contacts()
        next_id = max((c.get("id", 0) for c in contacts), default=0) + 1

        new_contact = {
            "id": next_id,
            "name": str(payload.get("name", "")).strip(),
            "email": str(payload.get("email", "")).strip(),
            "birth_date": str(payload.get("birth_date", "")).strip(),
            "subject_template": str(payload.get("subject_template", "")),
            "body_template": str(payload.get("body_template", "")),
            "active": bool(payload.get("active", True)),
            "last_sent_year": None,
        }

        contacts.append(new_contact)
        self._write_contacts(contacts)
        return new_contact

    def update_contact(self, contact_id, payload):
        contacts = self._read_contacts()

        for idx, row in enumerate(contacts):
            if row.get("id") == contact_id:
                updated = dict(row)
                updated.update(payload)
                updated["name"] = str(updated.get("name", "")).strip()
                updated["email"] = str(updated.get("email", "")).strip()
                updated["birth_date"] = str(updated.get("birth_date", "")).strip()
                updated["subject_template"] = str(updated.get("subject_template", ""))
                updated["body_template"] = str(updated.get("body_template", ""))
                updated["active"] = bool(updated.get("active", True))
                contacts[idx] = updated
                self._write_contacts(contacts)
                return updated

        raise ValueError("Contact not found.")

    def delete_contact(self, contact_id):
        contacts = self._read_contacts()
        filtered = [row for row in contacts if row.get("id") != contact_id]
        self._write_contacts(filtered)
        return True

    def mark_sent(self, contact_id, year):
        contacts = self._read_contacts()

        for row in contacts:
            if row.get("id") == contact_id:
                row["last_sent_year"] = int(year)
                self._write_contacts(contacts)
                return row

        raise ValueError("Contact not found.")

    def load_settings(self):
        data = self._read_json(SETTINGS_FILE, dict(DEFAULT_SETTINGS))
        merged = dict(DEFAULT_SETTINGS)

        if isinstance(data, dict):
            merged.update(data)

        return merged

    def save_settings(self, payload):
        merged = dict(DEFAULT_SETTINGS)

        if isinstance(payload, dict):
            merged.update(payload)

        self._write_json(SETTINGS_FILE, merged)
        return dict(merged)