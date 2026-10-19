# Self-review (optional extra)

A daily job that keeps Quartermaster current. It collects the day's evidence from your Claude Code history: `lesson:` messages, hand model switches above your default, escalations in the routed runs, and drift in the `model:` lines of your installed skills. It writes a short report and, when needed, updates your own routing rows and lessons.

What it costs: nothing on a quiet day, because the runner is a plain script and starts no model. A day with evidence starts one background Claude run on your subscription, one background run, on Sonnet, or on Opus when the day holds a lesson, an escalation or a hand switch of model, with a hard time limit (20 minutes by default). Every other file is checked by hash after the run and restored if the run changed anything it may not.

Install (after the main install.sh):

    bash extras/self-review/install.sh

It copies the scripts and JOB.md to `~/.claude/quartermaster/extras/self-review/`, adds any missing keys from `config.example.json` to `~/.claude/quartermaster/config.json` without overwriting yours, and schedules the job (launchd on macOS, cron elsewhere) at `run_hour`, default 10.

Remove only the job (files, reports and settings stay):

    bash extras/self-review/install.sh --remove

Reports are in `~/.claude/quartermaster/runtime/reports/`. Set `notify_command` in `config.json` if you want a notice when something changed. Test without starting a model: `QUARTERMASTER_DRY_RUN=1 python3 ~/.claude/quartermaster/extras/self-review/run_headless.py`.
