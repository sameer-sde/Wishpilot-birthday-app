# WishPilot

WishPilot is a Python desktop app that tracks birthdays, shows today's and upcoming celebrations, and sends personalized birthday emails through SMTP.

It uses Tkinter for the desktop interface, JSON files for local storage, `smtplib` plus `email.message.EmailMessage` for email delivery, and optional Pygame music playback for celebrations.

## Features

- View today's birthdays and upcoming birthdays in separate dashboard views.
- Add, edit, and delete birthday contacts from the desktop app.
- Send personalized birthday emails with placeholders like `{name}` and `{age}`.
- Animated confetti and floating balloons when birthday emails are sent.
- Optional background birthday music through Pygame mixer.
- Dark and light mode theme toggle.
- JSON-based storage for contacts and settings.

## Tech Stack

- Python
- Tkinter
- Pygame
- SMTP via `smtplib`
- `email.message.EmailMessage`
- JSON storage

## Project Structure

```text
wishpilot/
├── app.py
├── storage.py
├── email_service.py
├── music.py
├── birthdays.json
├── settings.json
├── assets/
└── README.md
```

## Requirements

- Python 3.10 or newer
- Pygame installed for music playback
- Internet connection for sending birthday emails
- Valid SMTP credentials

## Setup

1. Install Python 3.10 or newer.
2. Install dependencies:

```bash
pip install pygame
```

3. Run the app:

```bash
python3 app.py
```

## SMTP Configuration

Common SMTP settings:

- Gmail: `smtp.gmail.com`, port `587`, TLS enabled
- Outlook: `smtp.office365.com`, port `587`, TLS enabled
- Yahoo: `smtp.mail.yahoo.com`, port `587`, TLS enabled

If you use Gmail, an App Password is usually required instead of your normal account password.

## Contact Format

Birthdays must be entered as:

```text
YYYY-MM-DD
```

Example:

```text
2002-08-14
```

## Template Placeholders

These placeholders are supported in the subject and body templates:

- `{name}`
- `{email}`
- `{birth_date}`
- `{age}`
- `{sender_name}`

Example subject:

```text
Happy Birthday, {name}! 🎉
```

Example body:

```text
Hi {name},

Wishing you a very Happy Birthday! 🎂🎉
Hope your day is filled with joy, laughter, and cake!

Best wishes,
{sender_name}
```

## Music Support

Add a local `.mp3` or `.wav` file path in the **Music File** setting, then use the music toggle button in the app.

## How Scheduling Works

The app checks time every minute using Tkinter's event loop. When the configured hour and minute match, it sends birthday emails for contacts whose birthdays are today and who have not already received an email in the current year.

## Notes

- Duplicate birthday emails are prevented with `last_sent_year`.
- Contacts and settings are stored locally in JSON files.
- Confetti and balloon effects run on a Tkinter canvas.
- Music playback is optional and depends on Pygame being installed.

## Run

```bash
cd wishpilot
python3 app.py
```