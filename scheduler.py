from datetime import date, datetime

from database import list_contacts, mark_sent
from email_service import send_email


class BirthdayScheduler:
    def __init__(self, log_callback):
        self.log = log_callback
        self.last_scheduler_run_key = None

    def contacts_due_today(self, today=None):
        today = today or date.today()
        due = []

        for row in list_contacts():
            if not row["active"]:
                continue

            try:
                dob = datetime.strptime(row["birth_date"], "%Y-%m-%d").date()
            except ValueError:
                self.log(f"Skipping invalid date for {row['name']}: {row['birth_date']}")
                continue

            if (
                dob.month == today.month
                and dob.day == today.day
                and row["last_sent_year"] != today.year
            ):
                due.append(row)

        return due

    def render_template(self, template, row):
        age = ""

        try:
            dob = datetime.strptime(row["birth_date"], "%Y-%m-%d").date()
            age = str(date.today().year - dob.year)
        except Exception:
            pass

        return template.format(
            name=row["name"],
            email=row["email"],
            birth_date=row["birth_date"],
            age=age,
        )

    def send_due_birthdays(self, config, today=None):
        today = today or date.today()
        due = self.contacts_due_today(today)

        if not due:
            self.log("No birthdays due today.")
            return 0

        sent_count = 0

        for row in due:
            subject = self.render_template(row["subject_template"], row)
            body = self.render_template(row["body_template"], row)

            try:
                send_email(config, row["email"], subject, body)
                mark_sent(row["id"], today.year)
                sent_count += 1
                self.log(f"Sent birthday email to {row['name']} <{row['email']}>")
            except Exception as exc:
                self.log(f"Failed to send to {row['name']} <{row['email']}>: {exc}")

        return sent_count

    def should_run_now(self, config, now=None):
        now = now or datetime.now()

        if not config.get("scheduler_enabled", True):
            return False

        run_key = now.strftime("%Y-%m-%d %H:%M")
        target_hour = int(config.get("check_hour", 9))
        target_minute = int(config.get("check_minute", 0))

        if (
            now.hour == target_hour
            and now.minute == target_minute
            and self.last_scheduler_run_key != run_key
        ):
            self.last_scheduler_run_key = run_key
            return True

        return False
