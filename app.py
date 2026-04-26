import math
import random
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk

from email_service import send_email
from storage import Storage

try:
    from music import MusicPlayer
except Exception:
    class MusicPlayer:
        def __init__(self, logger):
            self.logger = logger
            self.is_playing = False

        def play(self, path):
            raise RuntimeError("Music feature unavailable because pygame is not installed.")

        def stop(self):
            self.is_playing = False


APP_TITLE = "WishPilot"
DEFAULT_SUBJECT = "Happy Birthday, {name}! 🎉"
DEFAULT_BODY = (
    "Hi {name},\n\n"
    "Wishing you a very Happy Birthday! 🎂🎉\n"
    "Hope your day is filled with joy, laughter, and cake!\n\n"
    "Best wishes,\n{sender_name}"
)

SCHEDULER_INTERVAL_MS = 60_000
CONFETTI_STEPS = 110
BALLOON_STEPS = 160

LIGHT = {
    "bg": "#f4f7fb",
    "panel": "#ffffff",
    "panel_2": "#e9eef8",
    "text": "#18212f",
    "muted": "#5f6b7a",
    "accent": "#4f46e5",
    "accent_2": "#4338ca",
    "entry": "#ffffff",
    "entry_border": "#cfd8e3",
    "canvas": "#eef3fb",
    "button_bg": "#2b3444",
    "button_fg": "#ffffff",
    "button_active": "#3b4960",
}

DARK = {
    "bg": "#0f1420",
    "panel": "#161c28",
    "panel_2": "#202838",
    "text": "#edf2ff",
    "muted": "#9aa8bf",
    "accent": "#7c8cff",
    "accent_2": "#9d5cff",
    "entry": "#111827",
    "entry_border": "#2e3a4f",
    "canvas": "#111827",
    "button_bg": "#2b3444",
    "button_fg": "#ffffff",
    "button_active": "#3b4960",
}


class WishPilotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1380x860")
        self.minsize(1180, 760)

        self.storage = Storage()
        self.settings = self.storage.load_settings()
        self.theme_name = self.settings.get("theme", "dark")
        self.palette = DARK if self.theme_name == "dark" else LIGHT

        self.selected_contact_id = None
        self.current_view = "all"
        self.confetti_items = []
        self.balloon_items = []
        self.balloon_generation = 0
        self.custom_buttons = []

        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.birth_date_var = tk.StringVar()
        self.subject_var = tk.StringVar(value=DEFAULT_SUBJECT)
        self.active_var = tk.BooleanVar(value=True)

        self.smtp_host_var = tk.StringVar(value=self.settings.get("smtp_host", "smtp.gmail.com"))
        self.smtp_port_var = tk.StringVar(value=str(self.settings.get("smtp_port", 587)))
        self.sender_email_var = tk.StringVar(value=self.settings.get("sender_email", ""))
        self.sender_name_var = tk.StringVar(value=self.settings.get("sender_name", "WishPilot"))
        self.password_var = tk.StringVar(value=self.settings.get("password", ""))
        self.use_tls_var = tk.BooleanVar(value=self.settings.get("use_tls", True))
        self.enable_music_var = tk.BooleanVar(value=self.settings.get("music_enabled", False))
        self.scheduler_enabled_var = tk.BooleanVar(value=self.settings.get("scheduler_enabled", True))
        self.check_hour_var = tk.StringVar(value=str(self.settings.get("check_hour", 9)))
        self.check_minute_var = tk.StringVar(value=str(self.settings.get("check_minute", 0)))
        self.days_ahead_var = tk.StringVar(value=str(self.settings.get("upcoming_days", 30)))
        self.music_file_var = tk.StringVar(value=self.settings.get("music_file", ""))

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self._build_ui()
        self.music = MusicPlayer(self.log)

        self.apply_theme()
        self.refresh_dashboard()
        self.start_scheduler_loop()
        self.log("WishPilot started.")

    def make_button(self, parent, text, command, width=None):
        btn = tk.Label(
            parent,
            text=text,
            cursor="hand2",
            font=("Helvetica", 11, "bold"),
            padx=16,
            pady=10,
            bd=0,
            relief="flat"
        )
        btn.command = command
        btn.default_text = text

        if width is not None:
            btn.configure(width=width)

        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.palette["button_active"]))
        btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.palette["button_bg"]))
        self.custom_buttons.append(btn)
        return btn

    def _build_ui(self):
        self.configure(bg=self.palette["bg"])

        self.root_frame = tk.Frame(self, bg=self.palette["bg"])
        self.root_frame.pack(fill="both", expand=True, padx=14, pady=14)
        self.root_frame.grid_columnconfigure(0, weight=3)
        self.root_frame.grid_columnconfigure(1, weight=2)
        self.root_frame.grid_rowconfigure(1, weight=1)
        self.root_frame.grid_rowconfigure(2, weight=2)

        self._build_header()
        self._build_left_panel()
        self._build_right_panel()
        self._build_bottom_panel()

    def _build_header(self):
        self.header = tk.Frame(self.root_frame, bg=self.palette["bg"])
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self.header.grid_columnconfigure(0, weight=1)

        title_wrap = tk.Frame(self.header, bg=self.palette["bg"])
        title_wrap.grid(row=0, column=0, sticky="w")

        self.title_label = tk.Label(
            title_wrap,
            text="WishPilot",
            font=("Helvetica", 28, "bold"),
            bg=self.palette["bg"],
            fg=self.palette["text"],
        )
        self.title_label.pack(side="left")

        self.subtitle_label = tk.Label(
            title_wrap,
            text="Never forget a birthday again 🎂",
            font=("Helvetica", 13),
            bg=self.palette["bg"],
            fg=self.palette["muted"],
        )
        self.subtitle_label.pack(side="left", padx=14, pady=(8, 0))

        actions = tk.Frame(self.header, bg=self.palette["bg"])
        actions.grid(row=0, column=1, sticky="e")

        self.theme_btn = self.make_button(actions, "🌗 Toggle Theme", self.toggle_theme)
        self.theme_btn.pack(side="left", padx=6)

        self.music_btn = self.make_button(actions, "🎵 Music", self.toggle_music)
        self.music_btn.pack(side="left", padx=6)

        self.check_btn = self.make_button(actions, "📨 Check & Send", self.check_and_send_birthdays)
        self.check_btn.pack(side="left", padx=6)

    def _build_left_panel(self):
        self.left_panel = tk.Frame(self.root_frame, bg=self.palette["panel"], highlightthickness=1)
        self.left_panel.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        self.left_panel.grid_rowconfigure(3, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        top_stats = tk.Frame(self.left_panel, bg=self.palette["panel"])
        top_stats.grid(row=0, column=0, sticky="ew", padx=14, pady=14)
        for i in range(3):
            top_stats.grid_columnconfigure(i, weight=1)

        self.today_card = self.create_stat_card(top_stats, "Today's Birthdays", "0", 0)
        self.upcoming_card = self.create_stat_card(top_stats, "Upcoming", "0", 1)
        self.total_card = self.create_stat_card(top_stats, "Total Contacts", "0", 2)

        filter_row = tk.Frame(self.left_panel, bg=self.palette["panel"])
        filter_row.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

        self.all_btn = self.make_button(filter_row, "All", lambda: self.change_view("all"), width=8)
        self.all_btn.pack(side="left", padx=(0, 6))

        self.today_btn = self.make_button(filter_row, "Today", lambda: self.change_view("today"), width=8)
        self.today_btn.pack(side="left", padx=6)

        self.upcoming_btn = self.make_button(filter_row, "Upcoming", lambda: self.change_view("upcoming"), width=10)
        self.upcoming_btn.pack(side="left", padx=6)

        self.refresh_btn = self.make_button(filter_row, "Refresh", self.refresh_dashboard, width=8)
        self.refresh_btn.pack(side="right")

        self.celebration_canvas = tk.Canvas(self.left_panel, height=120, bd=0, highlightthickness=0)
        self.celebration_canvas.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))

        table_wrap = tk.Frame(self.left_panel, bg=self.palette["panel"])
        table_wrap.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 14))
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        columns = ("name", "email", "birth_date", "age", "status")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=18)

        for col, width in [
            ("name", 180),
            ("email", 220),
            ("birth_date", 120),
            ("age", 60),
            ("status", 120),
        ]:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=width, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select_contact)

        scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

    def _build_right_panel(self):
        self.right_panel = tk.Frame(self.root_frame, bg=self.palette["bg"])
        self.right_panel.grid(row=1, column=1, sticky="nsew")
        self.right_panel.grid_rowconfigure(2, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.form_panel = tk.LabelFrame(self.right_panel, text="➕ Add / Edit Birthday", padx=12, pady=12)
        self.form_panel.grid(row=0, column=0, sticky="ew")
        self.form_panel.grid_columnconfigure(1, weight=1)

        self.make_form_row(self.form_panel, "Name", self.name_var, 0)
        self.make_form_row(self.form_panel, "Email", self.email_var, 1)
        self.make_form_row(self.form_panel, "Birth Date (YYYY-MM-DD)", self.birth_date_var, 2)
        self.make_form_row(self.form_panel, "Email Subject", self.subject_var, 3)

        self.active_check = tk.Checkbutton(self.form_panel, text="Active", variable=self.active_var)
        self.active_check.grid(row=4, column=1, sticky="w", pady=4)

        tk.Label(
            self.form_panel,
            text="Email Body Template\nUse {name}, {email}, {birth_date}, {age}, {sender_name}",
            justify="left",
        ).grid(row=5, column=0, sticky="nw", pady=4)

        self.body_text = tk.Text(self.form_panel, height=8, wrap="word")
        self.body_text.grid(row=5, column=1, sticky="ew", pady=4)
        self.body_text.insert("1.0", DEFAULT_BODY)

        form_actions = tk.Frame(self.form_panel)
        form_actions.grid(row=6, column=1, sticky="w", pady=(8, 0))
        self.new_btn = self.make_button(form_actions, "New", self.clear_form, width=8)
        self.new_btn.pack(side="left", padx=(0, 6))
        self.save_btn = self.make_button(form_actions, "Save", self.save_contact, width=8)
        self.save_btn.pack(side="left", padx=6)
        self.delete_btn = self.make_button(form_actions, "Delete", self.delete_contact, width=8)
        self.delete_btn.pack(side="left", padx=6)

        self.settings_panel = tk.LabelFrame(self.right_panel, text="⚙ SMTP, Theme & Scheduler", padx=12, pady=12)
        self.settings_panel.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        for i in range(4):
            self.settings_panel.grid_columnconfigure(i, weight=1)

        self.make_settings_row("SMTP Host", self.smtp_host_var, 0, 0)
        self.make_settings_row("Port", self.smtp_port_var, 0, 2)
        self.make_settings_row("Sender Email", self.sender_email_var, 1, 0)
        self.make_settings_row("Sender Name", self.sender_name_var, 1, 2)
        self.make_settings_row("Password / App Password", self.password_var, 2, 0, show="*")
        self.make_settings_row("Check Hour", self.check_hour_var, 3, 0)
        self.make_settings_row("Check Minute", self.check_minute_var, 3, 2)
        self.make_settings_row("Upcoming Days", self.days_ahead_var, 4, 0)
        self.make_settings_row("Music File", self.music_file_var, 4, 2)

        toggles = tk.Frame(self.settings_panel)
        toggles.grid(row=5, column=0, columnspan=4, sticky="w", pady=(6, 6))

        self.tls_check = tk.Checkbutton(toggles, text="Use TLS", variable=self.use_tls_var)
        self.tls_check.pack(side="left", padx=(0, 10))

        self.scheduler_check = tk.Checkbutton(toggles, text="Enable Scheduler", variable=self.scheduler_enabled_var)
        self.scheduler_check.pack(side="left", padx=10)

        self.music_check = tk.Checkbutton(toggles, text="Enable Music", variable=self.enable_music_var)
        self.music_check.pack(side="left", padx=10)

        settings_actions = tk.Frame(self.settings_panel)
        settings_actions.grid(row=6, column=0, columnspan=4, sticky="w")
        self.save_settings_btn = self.make_button(settings_actions, "Save Settings", self.save_settings)
        self.save_settings_btn.pack(side="left", padx=(0, 6))
        self.test_email_btn = self.make_button(settings_actions, "Send Test Email", self.send_test_email)
        self.test_email_btn.pack(side="left", padx=6)

        self.preview_panel = tk.LabelFrame(self.right_panel, text="🎂 Today's Preview", padx=12, pady=12)
        self.preview_panel.grid(row=2, column=0, sticky="nsew")
        self.preview_panel.grid_rowconfigure(0, weight=1)
        self.preview_panel.grid_columnconfigure(0, weight=1)

        self.preview_list = tk.Text(self.preview_panel, height=10, wrap="word")
        self.preview_list.grid(row=0, column=0, sticky="nsew")

    def _build_bottom_panel(self):
        self.log_panel = tk.LabelFrame(self.root_frame, text="📜 Activity Log", padx=12, pady=12)
        self.log_panel.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.log_panel.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(self.log_panel, height=8, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="ew")

    def create_stat_card(self, parent, title, value, col):
        card = tk.Frame(parent, bg=self.palette["panel_2"], padx=12, pady=12)
        card.grid(row=0, column=col, sticky="ew", padx=5)

        title_label = tk.Label(card, text=title, font=("Helvetica", 11, "bold"))
        title_label.pack(anchor="w")

        value_label = tk.Label(card, text=value, font=("Helvetica", 22, "bold"))
        value_label.pack(anchor="w", pady=(8, 0))
        return value_label

    def make_form_row(self, parent, label, variable, row):
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        entry = tk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=4)
        return entry

    def make_settings_row(self, label, variable, row, col, show=None):
        tk.Label(self.settings_panel, text=label).grid(row=row, column=col, sticky="w", pady=4, padx=(0, 6))
        entry = tk.Entry(self.settings_panel, textvariable=variable, show=show)
        entry.grid(row=row, column=col + 1, sticky="ew", pady=4, padx=(0, 8))
        return entry

    def _collect_children(self, widget):
        nodes = []
        for child in widget.winfo_children():
            nodes.append(child)
            nodes.extend(self._collect_children(child))
        return nodes

    def apply_theme(self):
        self.palette = DARK if self.theme_name == "dark" else LIGHT
        self.configure(bg=self.palette["bg"])

        self.style.configure(
            "Treeview",
            background=self.palette["entry"],
            fieldbackground=self.palette["entry"],
            foreground=self.palette["text"],
            rowheight=30,
        )
        self.style.map(
            "Treeview",
            background=[("selected", "#5f85a8")],
            foreground=[("selected", "#ffffff")],
        )
        self.style.configure(
            "Treeview.Heading",
            background=self.palette["panel_2"],
            foreground=self.palette["text"],
            relief="flat",
        )

        all_widgets = [self.title_label, self.subtitle_label, self.body_text, self.preview_list, self.log_text, self.celebration_canvas]
        for child in self.winfo_children():
            all_widgets.extend(self._collect_children(child))

        seen = set()
        for widget in all_widgets:
            if id(widget) in seen:
                continue
            seen.add(id(widget))

            cls = widget.winfo_class()

            if cls == "Label":
                if widget in self.custom_buttons:
                    widget.configure(
                        bg=self.palette["button_bg"],
                        fg=self.palette["button_fg"],
                        activebackground=self.palette["button_active"],
                        activeforeground=self.palette["button_fg"],
                    )
                elif widget.master in [self.today_card.master, self.upcoming_card.master, self.total_card.master]:
                    widget.configure(bg=self.palette["panel_2"], fg=self.palette["text"])
                else:
                    widget.configure(bg=self.palette["bg"], fg=self.palette["text"])

            elif cls == "Frame":
                if widget in [self.left_panel]:
                    widget.configure(bg=self.palette["panel"])
                elif widget.master in [self.left_panel]:
                    widget.configure(bg=self.palette["panel"])
                else:
                    widget.configure(bg=self.palette["bg"])

            elif cls == "Labelframe":
                widget.configure(bg=self.palette["bg"], fg=self.palette["text"], highlightbackground=self.palette["entry_border"])

            elif cls == "Checkbutton":
                widget.configure(
                    bg=self.palette["bg"],
                    fg=self.palette["text"],
                    selectcolor=self.palette["panel_2"],
                    activebackground=self.palette["bg"],
                    activeforeground=self.palette["text"],
                )

            elif cls == "Text":
                widget.configure(
                    bg=self.palette["entry"],
                    fg=self.palette["text"],
                    insertbackground=self.palette["text"],
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=self.palette["entry_border"],
                    highlightcolor=self.palette["accent"],
                )

            elif cls == "Entry":
                widget.configure(
                    bg=self.palette["entry"],
                    fg=self.palette["text"],
                    insertbackground=self.palette["text"],
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=self.palette["entry_border"],
                    highlightcolor=self.palette["accent"],
                    bd=6,
                )

            elif cls == "Canvas":
                widget.configure(bg=self.palette["canvas"])

        self.left_panel.configure(bg=self.palette["panel"], highlightbackground=self.palette["entry_border"])
        self.title_label.configure(bg=self.palette["bg"], fg=self.palette["text"])
        self.subtitle_label.configure(bg=self.palette["bg"], fg=self.palette["muted"])

        for stat in [self.today_card, self.upcoming_card, self.total_card]:
            stat.configure(bg=self.palette["panel_2"], fg=self.palette["text"])
            stat.master.configure(bg=self.palette["panel_2"])

        self.settings["theme"] = self.theme_name

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.apply_theme()
        self.save_settings(silent=True)
        self.log(f"Theme changed to {self.theme_name} mode.")

    def log(self, message):
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert("end", f"[{stamp}] {message}\n")
        self.log_text.see("end")

    def _parse_int(self, value, default, minimum=None, maximum=None):
        try:
            parsed = int(str(value).strip())
        except Exception:
            parsed = default
        if minimum is not None:
            parsed = max(minimum, parsed)
        if maximum is not None:
            parsed = min(maximum, parsed)
        return parsed

    def save_settings(self, silent=False):
        try:
            data = {
                "smtp_host": self.smtp_host_var.get().strip(),
                "smtp_port": self._parse_int(self.smtp_port_var.get(), 587, 1, 65535),
                "sender_email": self.sender_email_var.get().strip(),
                "sender_name": self.sender_name_var.get().strip() or "WishPilot",
                "password": self.password_var.get(),
                "use_tls": self.use_tls_var.get(),
                "music_enabled": self.enable_music_var.get(),
                "scheduler_enabled": self.scheduler_enabled_var.get(),
                "check_hour": self._parse_int(self.check_hour_var.get(), 9, 0, 23),
                "check_minute": self._parse_int(self.check_minute_var.get(), 0, 0, 59),
                "upcoming_days": self._parse_int(self.days_ahead_var.get(), 30, 1, 365),
                "theme": self.theme_name,
                "music_file": self.music_file_var.get().strip(),
                "last_auto_run": self.settings.get("last_auto_run", ""),
            }
            self.settings = self.storage.save_settings(data)
            if not silent:
                self.log("Settings saved.")
                messagebox.showinfo("Settings", "Settings saved successfully.")
        except Exception as exc:
            self.log(f"Settings save failed: {exc}")
            if not silent:
                messagebox.showerror("Settings Error", str(exc))

    def clear_form(self):
        self.selected_contact_id = None
        self.name_var.set("")
        self.email_var.set("")
        self.birth_date_var.set("")
        self.subject_var.set(DEFAULT_SUBJECT)
        self.active_var.set(True)
        self.body_text.delete("1.0", "end")
        self.body_text.insert("1.0", DEFAULT_BODY)

    def save_contact(self):
        try:
            name = self.name_var.get().strip()
            email = self.email_var.get().strip()
            birth_date = self.birth_date_var.get().strip()

            if not name or not email or not birth_date:
                raise ValueError("Name, email, and birth date are required.")

            datetime.strptime(birth_date, "%Y-%m-%d")

            payload = {
                "name": name,
                "email": email,
                "birth_date": birth_date,
                "subject_template": self.subject_var.get().strip() or DEFAULT_SUBJECT,
                "body_template": self.body_text.get("1.0", "end").strip() or DEFAULT_BODY,
                "active": self.active_var.get(),
            }

            if self.selected_contact_id is not None:
                self.storage.update_contact(self.selected_contact_id, payload)
                self.log(f"Updated birthday for {name}.")
            else:
                self.storage.add_contact(payload)
                self.log(f"Added birthday for {name}.")

            self.clear_form()
            self.refresh_dashboard()
        except Exception as exc:
            self.log(f"Save failed: {exc}")
            messagebox.showerror("Save Failed", str(exc))

    def delete_contact(self):
        if self.selected_contact_id is None:
            messagebox.showinfo("Delete", "Select a contact first.")
            return

        if messagebox.askyesno("Delete Contact", "Delete this contact?"):
            self.storage.delete_contact(self.selected_contact_id)
            self.log("Selected contact deleted.")
            self.clear_form()
            self.refresh_dashboard()

    def on_select_contact(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return

        contact_id = int(selection[0])
        row = self.storage.get_contact(contact_id)
        if not row:
            return

        self.selected_contact_id = contact_id
        self.name_var.set(row.get("name", ""))
        self.email_var.set(row.get("email", ""))
        self.birth_date_var.set(row.get("birth_date", ""))
        self.subject_var.set(row.get("subject_template", DEFAULT_SUBJECT))
        self.active_var.set(bool(row.get("active", True)))

        self.body_text.delete("1.0", "end")
        self.body_text.insert("1.0", row.get("body_template", DEFAULT_BODY))

    def get_today_birthdays(self):
        today = date.today()
        results = []
        for row in self.storage.list_contacts():
            if not row.get("active", True):
                continue
            try:
                dob = datetime.strptime(row["birth_date"], "%Y-%m-%d").date()
                if dob.month == today.month and dob.day == today.day:
                    results.append(row)
            except Exception:
                self.log(f"Invalid birth date skipped for {row.get('name', 'Unknown')}")
        return results

    def get_upcoming_birthdays(self, days_ahead=30):
        today = date.today()
        items = []

        for row in self.storage.list_contacts():
            if not row.get("active", True):
                continue

            try:
                dob = datetime.strptime(row["birth_date"], "%Y-%m-%d").date()
                next_bday = date(today.year, dob.month, dob.day)
                if next_bday < today:
                    next_bday = date(today.year + 1, dob.month, dob.day)

                delta = (next_bday - today).days
                if 0 <= delta <= days_ahead:
                    copy_row = dict(row)
                    copy_row["days_left"] = delta
                    copy_row["age"] = next_bday.year - dob.year
                    items.append(copy_row)
            except Exception:
                continue

        items.sort(key=lambda x: x["days_left"])
        return items

    def render_template(self, template, row):
        try:
            dob = datetime.strptime(row["birth_date"], "%Y-%m-%d").date()
            age = str(date.today().year - dob.year)
        except Exception:
            age = ""

        return template.format(
            name=row.get("name", "Friend"),
            email=row.get("email", ""),
            birth_date=row.get("birth_date", ""),
            age=age,
            sender_name=self.sender_name_var.get().strip() or "WishPilot",
        )

    def send_test_email(self):
        try:
            self.save_settings(silent=True)
            send_email(
                self.settings,
                self.settings["sender_email"],
                "WishPilot Test Email 🎂",
                "This is a test email from WishPilot. SMTP settings are working.",
            )
            self.log("Test email sent successfully.")
            messagebox.showinfo("Test Email", "Test email sent successfully.")
        except Exception as exc:
            self.log(f"Test email failed: {exc}")
            messagebox.showerror("Test Email Failed", str(exc))

    def check_and_send_birthdays(self):
        try:
            self.save_settings(silent=True)
            today = date.today()
            due_contacts = [
                row for row in self.get_today_birthdays()
                if row.get("last_sent_year") != today.year
            ]

            sent_count = 0
            for row in due_contacts:
                subject = self.render_template(row.get("subject_template", DEFAULT_SUBJECT), row)
                body = self.render_template(row.get("body_template", DEFAULT_BODY), row)
                send_email(self.settings, row["email"], subject, body)
                self.storage.mark_sent(row["id"], today.year)
                sent_count += 1
                self.log(f"Birthday email sent to {row['name']} ({row['email']}).")

            if sent_count > 0:
                self.launch_celebration(sent_count)
            else:
                self.log("No birthdays due today.")

            self.refresh_dashboard()
            messagebox.showinfo("Birthday Check", f"Completed. Sent {sent_count} email(s).")
        except Exception as exc:
            self.log(f"Birthday send failed: {exc}")
            messagebox.showerror("Birthday Check Failed", str(exc))

    def refresh_dashboard(self):
        contacts = self.storage.list_contacts()
        today_items = self.get_today_birthdays()
        days_ahead = self._parse_int(self.days_ahead_var.get(), 30, 1, 365)
        upcoming_items = self.get_upcoming_birthdays(days_ahead)

        self.today_card.configure(text=str(len(today_items)))
        self.upcoming_card.configure(text=str(len(upcoming_items)))
        self.total_card.configure(text=str(len(contacts)))

        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.current_view == "today":
            rows = today_items
        elif self.current_view == "upcoming":
            rows = upcoming_items
        else:
            rows = contacts

        today_ids = {row["id"] for row in today_items}
        upcoming_map = {row["id"]: row for row in upcoming_items}
        current_year = date.today().year

        for row in rows:
            try:
                dob = datetime.strptime(row["birth_date"], "%Y-%m-%d").date()
                age = current_year - dob.year
            except Exception:
                age = "-"

            if row["id"] in today_ids:
                status = "Today"
            elif row["id"] in upcoming_map:
                status = f"In {upcoming_map[row['id']]['days_left']} days"
            else:
                status = "Saved"

            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row.get("name", ""),
                    row.get("email", ""),
                    row.get("birth_date", ""),
                    age,
                    status,
                ),
            )

        self.preview_list.delete("1.0", "end")
        if today_items:
            self.preview_list.insert("end", "Today's birthdays:\n\n")
            for row in today_items:
                self.preview_list.insert("end", f"🎉 {row['name']} — {row['email']} — {row['birth_date']}\n")
        else:
            self.preview_list.insert("end", "No birthdays today.\n")

        if upcoming_items:
            self.preview_list.insert("end", "\nUpcoming:\n")
            for row in upcoming_items[:10]:
                self.preview_list.insert("end", f"• {row['name']} in {row['days_left']} day(s)\n")

    def change_view(self, view_name):
        self.current_view = view_name
        self.refresh_dashboard()
        self.log(f"Switched to {view_name} view.")

    def start_scheduler_loop(self):
        try:
            if self.scheduler_enabled_var.get():
                now = datetime.now()
                check_hour = self._parse_int(self.check_hour_var.get(), 9, 0, 23)
                check_minute = self._parse_int(self.check_minute_var.get(), 0, 0, 59)

                if now.hour == check_hour and now.minute == check_minute:
                    today_key = now.strftime("%Y-%m-%d")
                    last_run = self.settings.get("last_auto_run", "")

                    if last_run != today_key:
                        self.log("Automatic birthday check triggered.")
                        self.check_and_send_birthdays()
                        self.settings["last_auto_run"] = today_key
                        self.storage.save_settings(self.settings)
        except Exception as exc:
            self.log(f"Scheduler issue: {exc}")

        self.after(SCHEDULER_INTERVAL_MS, self.start_scheduler_loop)

    def toggle_music(self):
        self.save_settings(silent=True)

        if self.music.is_playing:
            self.music.stop()
            self.music_btn.configure(text="🎵 Music")
            self.log("Music stopped.")
            return

        if not self.enable_music_var.get():
            self.enable_music_var.set(True)

        path = self.music_file_var.get().strip()
        if not path:
            messagebox.showinfo("Music", "Add a music file path in the Music File setting first.")
            self.log("Music file path is empty.")
            return

        try:
            self.music.play(path)
            self.music_btn.configure(text="⏹ Stop Music")
        except Exception as exc:
            self.log(f"Music error: {exc}")
            messagebox.showerror("Music Error", str(exc))

    def launch_celebration(self, count):
        self.animate_confetti()
        self.animate_balloons()

        if self.enable_music_var.get() and self.music_file_var.get().strip():
            try:
                self.music.play(self.music_file_var.get().strip())
                self.music_btn.configure(text="⏹ Stop Music")
            except Exception as exc:
                self.log(f"Music error: {exc}")

        self.log(f"Celebration launched for {count} birthday email(s).")

    def animate_confetti(self):
        self.celebration_canvas.delete("all")
        width = max(self.celebration_canvas.winfo_width(), 900)
        height = max(self.celebration_canvas.winfo_height(), 120)
        colors = ["#ff4d6d", "#ffd166", "#06d6a0", "#118ab2", "#8338ec", "#ff9f1c"]

        self.confetti_items = []
        for _ in range(70):
            x = random.randint(0, width)
            y = random.randint(-height, 0)
            size = random.randint(6, 10)
            color = random.choice(colors)
            speed = random.uniform(2, 5)
            drift = random.uniform(-1.2, 1.2)
            item = self.celebration_canvas.create_rectangle(x, y, x + size, y + size, fill=color, outline="")
            self.confetti_items.append([item, speed, drift])

        self._step_confetti(0)

    def _step_confetti(self, frame):
        if frame > CONFETTI_STEPS:
            return

        height = max(self.celebration_canvas.winfo_height(), 120)
        width = max(self.celebration_canvas.winfo_width(), 900)

        for item, speed, drift in self.confetti_items:
            self.celebration_canvas.move(item, drift, speed)
            x1, y1, x2, y2 = self.celebration_canvas.coords(item)
            if y1 > height:
                new_x = random.randint(0, width)
                self.celebration_canvas.coords(item, new_x, -10, new_x + (x2 - x1), 0)

        self.after(25, lambda: self._step_confetti(frame + 1))

    def animate_balloons(self):
        self.balloon_generation += 1
        gen = self.balloon_generation
        height = max(self.celebration_canvas.winfo_height(), 120)
        width = max(self.celebration_canvas.winfo_width(), 900)
        colors = ["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#5f27cd"]

        for _ in range(8):
            x = random.randint(40, width - 40)
            y = height + random.randint(20, 80)
            oval = self.celebration_canvas.create_oval(
                x - 16, y - 22, x + 16, y + 22, fill=random.choice(colors), outline=""
            )
            line = self.celebration_canvas.create_line(x, y + 22, x, y + 55, fill="#d1d5db", width=2)
            self.balloon_items.append((oval, line, random.uniform(1.2, 2.5), random.uniform(-0.5, 0.5), gen))

        self._step_balloons(gen, 0)

    def _step_balloons(self, gen, frame):
        if frame > BALLOON_STEPS:
            for oval, line, _, _, g in list(self.balloon_items):
                if g == gen:
                    self.celebration_canvas.delete(oval)
                    self.celebration_canvas.delete(line)
            self.balloon_items = [item for item in self.balloon_items if item[4] != gen]
            return

        for oval, line, speed, sway, g in list(self.balloon_items):
            if g != gen:
                continue
            dx = math.sin(frame / 8) * sway
            dy = -speed
            self.celebration_canvas.move(oval, dx, dy)
            self.celebration_canvas.move(line, dx, dy)

        self.after(30, lambda: self._step_balloons(gen, frame + 1))


if __name__ == "__main__":
    app = WishPilotApp()
    app.mainloop()

