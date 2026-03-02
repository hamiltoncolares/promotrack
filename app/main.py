from __future__ import annotations

import argparse
import uuid
from datetime import date, timedelta
from pathlib import Path

from app.config import ensure_sites_file, load_yaml
from app.emailer import Emailer
from app.models import Tracker
from app.monitor import MonitorService
from app.storage import JsonStateStore
from app.trackers_config import TrackersConfigStore, parse_entry_dates, tracker_entry_to_dict

ROOT = Path(__file__).resolve().parents[1]
SITES_PATH = ROOT / "config" / "sites.yaml"
TRACKERS_PATH = ROOT / "config" / "trackers.yaml"
STATE_PATH = ROOT / "data" / "state.json"


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def resolve_period(
    start: str | None,
    end: str | None,
    days: int | None,
    current_start: date | None = None,
    current_end: date | None = None,
) -> tuple[date, date]:
    if days is not None:
        start_date = parse_date(start) if start else (current_start or date.today())
        end_date = start_date + timedelta(days=days)
    else:
        if start and end:
            start_date = parse_date(start)
            end_date = parse_date(end)
        elif start and current_end:
            start_date = parse_date(start)
            end_date = current_end
        elif end and current_start:
            start_date = current_start
            end_date = parse_date(end)
        elif current_start and current_end:
            start_date = current_start
            end_date = current_end
        else:
            raise SystemExit("Informe --start e --end (YYYY-MM-DD) ou use --days")

    if end_date < start_date:
        raise SystemExit("Periodo invalido: --end nao pode ser menor que --start")

    return start_date, end_date


def find_tracker_index(trackers: list[Tracker], tracker_id: str) -> int:
    for idx, tracker in enumerate(trackers):
        if tracker.id == tracker_id:
            return idx
    raise SystemExit(f"Tracker '{tracker_id}' nao encontrado")


def find_entry_index(entries: list[dict], tracker_id: str) -> int:
    for idx, entry in enumerate(entries):
        if str(entry.get("id")) == tracker_id:
            return idx
    raise SystemExit(f"Tracker '{tracker_id}' nao encontrado em config/trackers.yaml")


def add_tracker(args: argparse.Namespace) -> None:
    ensure_sites_file(SITES_PATH)
    store = JsonStateStore(STATE_PATH)
    state = store.load()

    start_date, end_date = resolve_period(args.start, args.end, args.days)

    tracker = Tracker(
        id=str(uuid.uuid4())[:8],
        wine_name=args.wine,
        site=args.site,
        start_date=start_date,
        end_date=end_date,
    )
    state.trackers.append(tracker)
    store.save(state)

    print(f"Tracker criado: {tracker.id} | {tracker.wine_name} | {tracker.site} | {start_date} -> {end_date}")


def list_trackers() -> None:
    store = JsonStateStore(STATE_PATH)
    state = store.load()
    if not state.trackers:
        print("Nenhum tracker cadastrado")
        return

    for t in state.trackers:
        print(
            f"{t.id} | {t.wine_name} | {t.site} | {t.start_date} -> {t.end_date} | "
            f"active={t.active} | last_price={t.last_price}"
        )


def remove_tracker(tracker_id: str) -> None:
    store = JsonStateStore(STATE_PATH)
    state = store.load()
    idx = find_tracker_index(state.trackers, tracker_id)
    tracker = state.trackers.pop(idx)
    store.save(state)
    print(f"Tracker removido: {tracker.id} | {tracker.wine_name} | {tracker.site}")


def update_tracker(args: argparse.Namespace) -> None:
    ensure_sites_file(SITES_PATH)
    store = JsonStateStore(STATE_PATH)
    state = store.load()
    idx = find_tracker_index(state.trackers, args.id)
    tracker = state.trackers[idx]
    if args.activate and args.deactivate:
        raise SystemExit("Use apenas uma opcao: --activate ou --deactivate")

    if args.wine:
        tracker.wine_name = args.wine
    if args.site:
        tracker.site = args.site

    if args.start or args.end or args.days is not None:
        start_date, end_date = resolve_period(
            args.start,
            args.end,
            args.days,
            current_start=tracker.start_date,
            current_end=tracker.end_date,
        )
        tracker.start_date = start_date
        tracker.end_date = end_date

    if args.activate:
        tracker.active = True
    if args.deactivate:
        tracker.active = False

    if args.reset_price:
        tracker.last_price = None
    if args.reset_product:
        tracker.product_url = None
        tracker.product_name = None

    store.save(state)
    print(
        f"Tracker atualizado: {tracker.id} | {tracker.wine_name} | {tracker.site} | "
        f"{tracker.start_date} -> {tracker.end_date} | active={tracker.active}"
    )


def cfg_list_trackers() -> None:
    cfg_store = TrackersConfigStore(TRACKERS_PATH)
    entries = cfg_store.load()
    if not entries:
        print("Nenhum tracker em config/trackers.yaml")
        return

    for entry in entries:
        print(
            f"{entry.get('id')} | {entry.get('wine_name')} | {entry.get('site')} | "
            f"{entry.get('start_date')} -> {entry.get('end_date')} | active={entry.get('active', True)}"
        )


def cfg_add_tracker(args: argparse.Namespace) -> None:
    cfg_store = TrackersConfigStore(TRACKERS_PATH)
    entries = cfg_store.load()

    tracker_id = args.id or str(uuid.uuid4())[:8]
    if any(str(item.get("id")) == tracker_id for item in entries):
        raise SystemExit(f"Ja existe tracker com id '{tracker_id}' em config/trackers.yaml")

    days = args.days
    if not args.start and not args.end and days is None:
        days = 30
    start_date, end_date = resolve_period(args.start, args.end, days)
    entry = tracker_entry_to_dict(
        tracker_id=tracker_id,
        wine_name=args.wine,
        site=args.site,
        start_date=start_date,
        end_date=end_date,
        active=not args.deactivate,
    )
    entries.append(entry)
    cfg_store.save(entries)
    print(f"Tracker adicionado em config/trackers.yaml: {tracker_id}")


def cfg_update_tracker(args: argparse.Namespace) -> None:
    cfg_store = TrackersConfigStore(TRACKERS_PATH)
    entries = cfg_store.load()
    idx = find_entry_index(entries, args.id)
    entry = entries[idx]
    if args.activate and args.deactivate:
        raise SystemExit("Use apenas uma opcao: --activate ou --deactivate")

    if args.wine:
        entry["wine_name"] = args.wine
    if args.site:
        entry["site"] = args.site

    current_start, current_end = parse_entry_dates(entry)
    if args.start or args.end or args.days is not None:
        start_date, end_date = resolve_period(
            args.start,
            args.end,
            args.days,
            current_start=current_start,
            current_end=current_end,
        )
        entry["start_date"] = start_date.isoformat()
        entry["end_date"] = end_date.isoformat()

    if args.activate:
        entry["active"] = True
    if args.deactivate:
        entry["active"] = False

    entries[idx] = entry
    cfg_store.save(entries)
    print(f"Tracker atualizado em config/trackers.yaml: {args.id}")


def cfg_remove_tracker(tracker_id: str) -> None:
    cfg_store = TrackersConfigStore(TRACKERS_PATH)
    entries = cfg_store.load()
    idx = find_entry_index(entries, tracker_id)
    removed = entries.pop(idx)
    cfg_store.save(entries)
    print(f"Tracker removido de config/trackers.yaml: {removed.get('id')}")


def sync_trackers() -> None:
    cfg_store = TrackersConfigStore(TRACKERS_PATH)
    entries = cfg_store.load()

    state_store = JsonStateStore(STATE_PATH)
    state = state_store.load()
    current_by_id = {tracker.id: tracker for tracker in state.trackers}

    merged_trackers: list[Tracker] = []
    added = 0
    updated = 0

    seen_ids: set[str] = set()
    for entry in entries:
        tracker_id = str(entry.get("id") or "").strip()
        wine_name = str(entry.get("wine_name") or "").strip()
        site = str(entry.get("site") or "").strip()
        active = bool(entry.get("active", True))

        if not tracker_id:
            raise SystemExit("Tracker invalido em config/trackers.yaml: campo 'id' obrigatorio")
        if tracker_id in seen_ids:
            raise SystemExit(f"Tracker invalido em config/trackers.yaml: id duplicado '{tracker_id}'")
        seen_ids.add(tracker_id)
        if not wine_name:
            raise SystemExit(f"Tracker invalido ({tracker_id}): campo 'wine_name' obrigatorio")
        if not site:
            raise SystemExit(f"Tracker invalido ({tracker_id}): campo 'site' obrigatorio")

        start_date, end_date = parse_entry_dates(entry)
        existing = current_by_id.get(tracker_id)

        if existing is None:
            merged_trackers.append(
                Tracker(
                    id=tracker_id,
                    wine_name=wine_name,
                    site=site,
                    start_date=start_date,
                    end_date=end_date,
                    active=active,
                )
            )
            added += 1
            continue

        wine_or_site_changed = existing.wine_name != wine_name or existing.site != site
        existing.wine_name = wine_name
        existing.site = site
        existing.start_date = start_date
        existing.end_date = end_date
        existing.active = active

        if wine_or_site_changed:
            existing.product_url = None
            existing.product_name = None
            existing.last_price = None

        merged_trackers.append(existing)
        updated += 1

    removed_ids = set(current_by_id.keys()) - {tracker.id for tracker in merged_trackers}
    state.trackers = merged_trackers
    state_store.save(state)

    print(
        "Sync concluido | "
        f"config={len(entries)} | adicionados={added} | atualizados={updated} | removidos={len(removed_ids)}"
    )


def run_check(send_email: bool) -> None:
    ensure_sites_file(SITES_PATH)
    sites_config = load_yaml(SITES_PATH)
    state_store = JsonStateStore(STATE_PATH)
    state = state_store.load()

    service = MonitorService(sites_config)
    alerts = service.check(state)
    state_store.save(state)

    print(f"Check finalizado. Alertas de queda: {len(alerts)}")

    if send_email and alerts:
        emailer = Emailer()
        emailer.send_drop_alerts(alerts)
        print("E-mail enviado")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PromoTrack - monitoramento de preco de vinhos")
    sub = parser.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="Adiciona vinho para monitoramento direto no state.json")
    add.add_argument("--wine", required=True, help="Nome do vinho")
    add.add_argument("--site", required=True, help="Site configurado em config/sites.yaml")
    add.add_argument("--start", help="Data inicial YYYY-MM-DD")
    add.add_argument("--end", help="Data final YYYY-MM-DD")
    add.add_argument("--days", type=int, help="Quantidade de dias a partir de --start (ou hoje)")

    sub.add_parser("list", help="Lista trackers no state.json")

    remove = sub.add_parser("remove", help="Remove tracker pelo ID no state.json")
    remove.add_argument("--id", required=True, help="ID do tracker")

    update = sub.add_parser("update", help="Atualiza tracker pelo ID no state.json")
    update.add_argument("--id", required=True, help="ID do tracker")
    update.add_argument("--wine", help="Novo nome do vinho")
    update.add_argument("--site", help="Novo site configurado em config/sites.yaml")
    update.add_argument("--start", help="Nova data inicial YYYY-MM-DD")
    update.add_argument("--end", help="Nova data final YYYY-MM-DD")
    update.add_argument("--days", type=int, help="Nova quantidade de dias a partir de --start (ou data atual)")
    update.add_argument("--activate", action="store_true", help="Ativa monitoramento do tracker")
    update.add_argument("--deactivate", action="store_true", help="Desativa monitoramento do tracker")
    update.add_argument("--reset-price", action="store_true", help="Limpa ultimo preco salvo")
    update.add_argument("--reset-product", action="store_true", help="Limpa URL/nome do produto para nova busca")

    cfg_add = sub.add_parser("cfg-add", help="Adiciona tracker em config/trackers.yaml")
    cfg_add.add_argument("--id", help="ID do tracker (opcional; gera automatico se omitido)")
    cfg_add.add_argument("--wine", required=True, help="Nome do vinho")
    cfg_add.add_argument("--site", required=True, help="Site configurado em config/sites.yaml")
    cfg_add.add_argument("--start", help="Data inicial YYYY-MM-DD")
    cfg_add.add_argument("--end", help="Data final YYYY-MM-DD")
    cfg_add.add_argument("--days", type=int, help="Quantidade de dias a partir de --start (ou hoje)")
    cfg_add.add_argument("--deactivate", action="store_true", help="Cria tracker desativado")

    cfg_update = sub.add_parser("cfg-update", help="Atualiza tracker em config/trackers.yaml")
    cfg_update.add_argument("--id", required=True, help="ID do tracker")
    cfg_update.add_argument("--wine", help="Novo nome do vinho")
    cfg_update.add_argument("--site", help="Novo site")
    cfg_update.add_argument("--start", help="Nova data inicial YYYY-MM-DD")
    cfg_update.add_argument("--end", help="Nova data final YYYY-MM-DD")
    cfg_update.add_argument("--days", type=int, help="Nova quantidade de dias")
    cfg_update.add_argument("--activate", action="store_true", help="Ativa tracker")
    cfg_update.add_argument("--deactivate", action="store_true", help="Desativa tracker")

    cfg_remove = sub.add_parser("cfg-remove", help="Remove tracker de config/trackers.yaml")
    cfg_remove.add_argument("--id", required=True, help="ID do tracker")

    sub.add_parser("cfg-list", help="Lista trackers de config/trackers.yaml")
    sub.add_parser("sync-trackers", help="Sincroniza config/trackers.yaml para data/state.json")

    check = sub.add_parser("check", help="Executa verificacao de preco")
    check.add_argument("--send-email", action="store_true", help="Envia e-mail se houver queda")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "add":
        add_tracker(args)
    elif args.cmd == "list":
        list_trackers()
    elif args.cmd == "remove":
        remove_tracker(args.id)
    elif args.cmd == "update":
        update_tracker(args)
    elif args.cmd == "cfg-add":
        cfg_add_tracker(args)
    elif args.cmd == "cfg-update":
        cfg_update_tracker(args)
    elif args.cmd == "cfg-remove":
        cfg_remove_tracker(args.id)
    elif args.cmd == "cfg-list":
        cfg_list_trackers()
    elif args.cmd == "sync-trackers":
        sync_trackers()
    elif args.cmd == "check":
        run_check(args.send_email)


if __name__ == "__main__":
    main()
