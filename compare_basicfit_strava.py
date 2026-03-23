#!/usr/bin/env python3
"""
compare_basicfit_strava.py

Compare BasicFit gym sessions (from ICS) with Strava WeightTraining activities (from ICS).
Find untracked sessions and optionally upload them to Strava.

Usage:
    python compare_basicfit_strava.py \\
        --basicfit basicfit.ics \\
        --strava strava.ics \\
        [--margin 30] \\
        [--from 2025-01-01] \\
        [--upload]

Sources can be local file paths or HTTP(S) URLs.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from icalendar import Calendar
from rich.console import Console
from rich.table import Table
from rich import box
from rich.prompt import Confirm

console = Console(width=120)

# ---------------------------------------------------------------------------
# ICS parsing
# ---------------------------------------------------------------------------

def load_ics(source: str) -> Calendar:
    """Load an ICS file from a local path or a URL."""
    if source.startswith("http://") or source.startswith("https://"):
        console.print(f"[dim]Fetching ICS from URL: {source}[/dim]")
        res = requests.get(source, timeout=20)
        res.raise_for_status()
        data = res.content
    else:
        path = Path(source)
        if not path.exists():
            console.print(f"[red]File not found: {source}[/red]")
            sys.exit(1)
        data = path.read_bytes()
    return Calendar.from_ical(data)


def parse_basicfit_events(cal: Calendar, since: datetime | None = None) -> list[dict]:
    """Extract BasicFit sessions from the calendar."""
    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        dtstart = component.get("DTSTART")
        dtend = component.get("DTEND")
        summary = str(component.get("SUMMARY", ""))
        if dtstart is None:
            continue

        start_dt = dtstart.dt
        end_dt = dtend.dt if dtend else None

        # Normalize to UTC-aware datetime
        if isinstance(start_dt, datetime):
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
        else:
            # date-only → treat as midnight UTC
            start_dt = datetime.combine(start_dt, datetime.min.time(), tzinfo=timezone.utc)

        if isinstance(end_dt, datetime):
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
        elif end_dt is not None:
            end_dt = datetime.combine(end_dt, datetime.min.time(), tzinfo=timezone.utc)

        if since and start_dt < since:
            continue

        duration_min = None
        if end_dt:
            duration_min = int((end_dt - start_dt).total_seconds() / 60)

        events.append({
            "start": start_dt,
            "end": end_dt,
            "duration_min": duration_min,
            "summary": summary,
            "location": str(component.get("LOCATION", "")),
        })

    events.sort(key=lambda e: e["start"])
    return events


def parse_strava_weight_training(cal: Calendar, since: datetime | None = None) -> list[dict]:
    """Extract WeightTraining events from the Strava calendar (summary contains 💪 or 'Weight Training')."""
    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        summary = str(component.get("SUMMARY", ""))
        # Filter: must be a weight training activity
        if "Weight Training" not in summary and "💪" not in summary:
            continue
        dtstart = component.get("DTSTART")
        dtend = component.get("DTEND")
        if dtstart is None:
            continue

        start_dt = dtstart.dt
        end_dt = dtend.dt if dtend else None

        if isinstance(start_dt, datetime):
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
        else:
            start_dt = datetime.combine(start_dt, datetime.min.time(), tzinfo=timezone.utc)

        if isinstance(end_dt, datetime):
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
        elif end_dt is not None:
            end_dt = datetime.combine(end_dt, datetime.min.time(), tzinfo=timezone.utc)

        if since and start_dt < since:
            continue

        events.append({
            "start": start_dt,
            "end": end_dt,
            "summary": summary,
        })

    events.sort(key=lambda e: e["start"])
    return events


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------

def find_matching_strava(bf_event: dict, strava_events: list[dict], margin_min: int) -> dict | None:
    """
    Find a Strava event that matches a BasicFit session.

    A match is found when the Strava start time is within:
        [bf_start - margin, bf_start + margin]
    (the user starts Strava a few minutes AFTER arriving → Strava start > BF start usually)
    """
    bf_start = bf_event["start"]
    window_start = bf_start - timedelta(minutes=margin_min)
    window_end = bf_start + timedelta(minutes=margin_min)

    for s in strava_events:
        if window_start <= s["start"] <= window_end:
            return s
    return None


def compare(bf_events: list[dict], strava_events: list[dict], margin_min: int) -> tuple[list, list]:
    """
    Returns:
        matched   : list of (bf_event, strava_event)
        unmatched : list of bf_event (no Strava counterpart)
    """
    matched = []
    unmatched = []
    used_strava = set()

    for bf in bf_events:
        match = None
        bf_start = bf["start"]
        window_start = bf_start - timedelta(minutes=margin_min)
        window_end = bf_start + timedelta(minutes=margin_min)

        for i, s in enumerate(strava_events):
            if i in used_strava:
                continue
            if window_start <= s["start"] <= window_end:
                match = (i, s)
                break

        if match:
            used_strava.add(match[0])
            matched.append((bf, match[1]))
        else:
            unmatched.append(bf)

    return matched, unmatched


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def fmt_dt(dt: datetime) -> str:
    """Format datetime to local-ish display (convert from UTC to +1)."""
    local = dt.astimezone()
    return local.strftime("%Y-%m-%d %H:%M")


def fmt_duration(minutes: int | None) -> str:
    if minutes is None:
        return "?"
    h, m = divmod(minutes, 60)
    return f"{h}h{m:02d}"


def display_results(matched: list, unmatched: list, margin_min: int):
    console.print()
    console.rule("[bold green]✅ Matched BasicFit ↔ Strava[/bold green]")
    if matched:
        table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold cyan", expand=False)
        table.add_column("BasicFit arrivée", style="dim", width=20)
        table.add_column("Durée BF", justify="right", width=10)
        table.add_column("Strava début", style="dim", width=20)
        table.add_column("Strava activité", width=35)
        table.add_column("Écart", justify="right", width=10)

        for bf, s in matched:
            delta = int((s["start"] - bf["start"]).total_seconds() / 60)
            ecart = f"+{delta} min" if delta >= 0 else f"{delta} min"
            table.add_row(
                fmt_dt(bf["start"]),
                fmt_duration(bf["duration_min"]),
                fmt_dt(s["start"]),
                s["summary"],
                ecart,
            )
        console.print(table)
    else:
        console.print("[dim]Aucun match trouvé.[/dim]")

    console.print()
    console.rule(f"[bold red]❌ Sessions BasicFit sans Strava ({len(unmatched)})[/bold red]")
    if unmatched:
        table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold red", expand=False)
        table.add_column("BasicFit arrivée", width=20)
        table.add_column("Départ", width=20)
        table.add_column("Durée", justify="right", width=8)
        table.add_column("Lieu", width=50)

        for bf in unmatched:
            table.add_row(
                fmt_dt(bf["start"]),
                fmt_dt(bf["end"]) if bf["end"] else "?",
                fmt_duration(bf["duration_min"]),
                bf["location"] or bf["summary"],
            )
        console.print(table)
    else:
        console.print("[green]Toutes les sessions BasicFit ont un match Strava 🎉[/green]")

    console.print()
    console.print(f"[dim]Marge utilisée : ±{margin_min} min[/dim]")
    console.print(f"[dim]Total BasicFit : {len(matched) + len(unmatched)} | Matchés : {len(matched)} | Manquants : {len(unmatched)}[/dim]")


# ---------------------------------------------------------------------------
# Strava upload
# ---------------------------------------------------------------------------

def get_strava_access_token() -> str:
    client_id = os.environ.get("STRAVA_CLIENT_ID")
    client_secret = os.environ.get("STRAVA_CLIENT_SECRET")
    refresh_token = os.environ.get("STRAVA_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        console.print("[red]Variables d'environnement manquantes : STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN[/red]")
        sys.exit(1)

    res = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    res.raise_for_status()
    return res.json()["access_token"]


def upload_activity(token: str, bf_event: dict, default_duration_min: int = 90) -> dict:
    """Upload a single BasicFit session to Strava as WeightTraining."""
    duration_sec = (bf_event["duration_min"] or default_duration_min) * 60

    # Strava expects start_date_local in ISO 8601 but we have UTC → convert
    start_utc = bf_event["start"]
    # Use the UTC timestamp directly with the Z suffix (Strava accepts UTC)
    start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "name": "💪 Muscu BasicFit",
        "type": "WeightTraining",
        "start_date_local": start_str,
        "elapsed_time": duration_sec,
        "description": "Importé depuis BasicFit ICS — données de présence en salle.",
    }

    res = requests.post(
        "https://www.strava.com/api/v3/activities",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=15,
    )
    res.raise_for_status()
    return res.json()


def save_preview(unmatched: list, default_duration_min: int, output_path: str = "preview_upload.json"):
    """Save a JSON preview of what would be uploaded."""
    preview = []
    for bf in unmatched:
        duration_sec = (bf["duration_min"] or default_duration_min) * 60
        preview.append({
            "name": "💪 Muscu BasicFit",
            "type": "WeightTraining",
            "start_date_local": bf["start"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "elapsed_time": duration_sec,
            "duration_min": bf["duration_min"] or default_duration_min,
            "basicfit_arrival": fmt_dt(bf["start"]),
            "basicfit_departure": fmt_dt(bf["end"]) if bf["end"] else None,
            "description": "Importé depuis BasicFit ICS — données de présence en salle.",
        })

    Path(output_path).write_text(json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print(f"\n[cyan]📄 Preview sauvegardé dans [bold]{output_path}[/bold][/cyan]")
    return preview


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compare BasicFit ICS sessions avec Strava et uploade les manquants."
    )
    parser.add_argument("--basicfit", required=True, help="Chemin ou URL du fichier ICS BasicFit")
    parser.add_argument("--strava", required=True, help="Chemin ou URL du fichier ICS Strava")
    parser.add_argument(
        "--margin",
        type=int,
        default=30,
        help="Marge de tolérance en minutes entre l'arrivée BasicFit et le début Strava (défaut : 30)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=90,
        help="Durée par défaut (en minutes) pour l'upload si la durée BasicFit n'est pas disponible (défaut : 90)",
    )
    parser.add_argument(
        "--from",
        dest="since",
        default=None,
        help="Ne comparer qu'à partir de cette date (format YYYY-MM-DD)",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Uploader les activités manquantes sur Strava (nécessite les variables d'env Strava)",
    )
    parser.add_argument(
        "--preview",
        default="preview_upload.json",
        help="Fichier JSON de preview (défaut : preview_upload.json)",
    )
    args = parser.parse_args()

    since_dt = None
    if args.since:
        since_dt = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    console.rule("[bold blue]BasicFit ↔ Strava Comparator[/bold blue]")
    console.print(f"[cyan]BasicFit ICS :[/cyan] {args.basicfit}")
    console.print(f"[cyan]Strava ICS   :[/cyan] {args.strava}")
    console.print(f"[cyan]Marge        :[/cyan] ±{args.margin} min")
    if since_dt:
        console.print(f"[cyan]Depuis       :[/cyan] {args.since}")

    # Load & parse
    console.print("\n[dim]Chargement des calendriers...[/dim]")
    bf_cal = load_ics(args.basicfit)
    st_cal = load_ics(args.strava)

    bf_events = parse_basicfit_events(bf_cal, since=since_dt)
    st_events = parse_strava_weight_training(st_cal, since=since_dt)

    console.print(f"[dim]BasicFit : {len(bf_events)} session(s) trouvée(s)[/dim]")
    console.print(f"[dim]Strava   : {len(st_events)} activité(s) WeightTraining trouvée(s)[/dim]")

    # Compare
    matched, unmatched = compare(bf_events, st_events, margin_min=args.margin)

    # Display
    display_results(matched, unmatched, args.margin)

    if not unmatched:
        console.print("\n[green]Rien à uploader.[/green]")
        return

    # Save preview
    save_preview(unmatched, default_duration_min=args.duration, output_path=args.preview)

    if not args.upload:
        console.print("\n[yellow]Mode dry-run. Ajoutez [bold]--upload[/bold] pour envoyer sur Strava.[/yellow]")
        return

    # Confirm & upload
    console.print(f"\n[bold yellow]⚠️  Vous allez uploader {len(unmatched)} activité(s) sur Strava.[/bold yellow]")
    if not Confirm.ask("Confirmer l'upload ?"):
        console.print("[dim]Upload annulé.[/dim]")
        return

    token = get_strava_access_token()
    uploaded = []
    failed = []

    for i, bf in enumerate(unmatched, 1):
        try:
            result = upload_activity(token, bf, default_duration_min=args.duration)
            console.print(f"  [green]✓[/green] [{i}/{len(unmatched)}] {fmt_dt(bf['start'])} → activité #{result.get('id')} créée")
            uploaded.append(result)
        except requests.HTTPError as e:
            console.print(f"  [red]✗[/red] [{i}/{len(unmatched)}] {fmt_dt(bf['start'])} → erreur : {e}")
            failed.append(bf)

    console.print(f"\n[bold]Résumé upload :[/bold] {len(uploaded)} réussi(s), {len(failed)} échoué(s)")

    if uploaded:
        out_path = "uploaded_activities.json"
        Path(out_path).write_text(json.dumps(uploaded, indent=2, ensure_ascii=False), encoding="utf-8")
        console.print(f"[cyan]📄 Détails sauvegardés dans [bold]{out_path}[/bold][/cyan]")


if __name__ == "__main__":
    main()
