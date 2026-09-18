# poem-of-the-day

Downloads the current [Poetry Foundation "Poem of the Day"](https://www.poetryfoundation.org/poems/poem-of-the-day) and saves it as a plain text file.

No external dependencies — uses only the Python standard library.

## Usage

```bash
python3 fetch_poem_of_the_day.py
```

Each run fetches the latest poem from the Poetry Foundation RSS feed and saves it to:

```
~/poems/poem-of-the-day/YYYY-MM-DD_poem-title-slug.txt
```

Each file contains the title, a link to the poem, the publish date, and the poem text.

Running the script more than once on the same day is safe — if a file for today already exists, it's left alone and the script exits without overwriting it.

To save poems somewhere else, edit `OUTPUT_DIR` at the top of the script.

## Displaying the poem on demand

`show_poem.sh` prints today's saved poem to your terminal, exactly as it was
saved (no reformatting or re-wrapping). If today's poem hasn't been fetched
yet — for example if you run it before the 7 AM timer — it fetches it on the
spot (safe to do; `fetch_poem_of_the_day.py` is idempotent per day) and falls
back to showing the most recent poem on file if that isn't possible (e.g. no
internet access).

To install it as a `poem` command:

```bash
chmod +x show_poem.sh
ln -s "$(pwd)/show_poem.sh" ~/.local/bin/poem
```

(`~/.local/bin` is already on `PATH` by default on most systems; adjust the
symlink target if you keep the repo somewhere other than where you ran this
from.)

Then just run:

```bash
poem
```

## Requirements

- Python 3
- Internet access (to reach `poetryfoundation.org`)
- Bash and standard coreutils (`ls`/`sort`/`cat`/`timeout`) if you also want
  to use `show_poem.sh` to display poems on demand

## Running it automatically every day

### Option 1: cron

1. Open your crontab for editing:

   ```bash
   crontab -e
   ```

2. Add a line to run the script once a day (this example runs it at 7:00 AM):

   ```cron
   0 7 * * * /usr/bin/python3 /home/phil/dev/poem-of-the-day/fetch_poem_of_the_day.py >> /home/phil/poems/poem-of-the-day/fetch.log 2>&1
   ```

   Use the full path to `python3` (check with `which python3`) and to the script, since cron doesn't run with your normal shell environment.

3. Save and exit. Confirm the job is scheduled with:

   ```bash
   crontab -l
   ```

### Option 2: systemd user timer

This is a good option if you'd rather manage the schedule with `systemctl`/`journalctl` than a crontab.

1. Create `~/.config/systemd/user/poem-of-the-day.service`:

   ```ini
   [Unit]
   Description=Fetch Poetry Foundation poem of the day

   [Service]
   Type=oneshot
   ExecStart=/usr/bin/python3 /home/phil/dev/poem-of-the-day/fetch_poem_of_the_day.py
   ```

2. Create `~/.config/systemd/user/poem-of-the-day.timer`:

   ```ini
   [Unit]
   Description=Run poem-of-the-day daily

   [Timer]
   OnCalendar=*-*-* 07:00:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

   `Persistent=true` means if your machine is asleep or off at 7:00 AM, the job runs as soon as it's next on.

3. Enable and start the timer:

   ```bash
   systemctl --user enable --now poem-of-the-day.timer
   ```

4. Check it's scheduled and see recent runs:

   ```bash
   systemctl --user list-timers poem-of-the-day.timer
   journalctl --user -u poem-of-the-day.service
   ```

   Note: for the timer to fire when you're not logged in, enable lingering for your user once: `loginctl enable-linger $USER`.
