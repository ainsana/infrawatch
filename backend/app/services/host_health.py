from datetime import UTC, datetime, timedelta


def evaluate_host_status(
    last_seen_at: datetime | None,
    *,
    now: datetime | None = None,
    offline_after: timedelta = timedelta(minutes=5),
) -> str:
    if offline_after <= timedelta(0):
        raise ValueError("Offline threshold must be greater than zero.")

    if last_seen_at is None:
        return "unknown"

    current_time = now or datetime.now(UTC)

    if last_seen_at.tzinfo is None:
        raise ValueError("Last seen timestamp must be timezone-aware.")

    if current_time.tzinfo is None:
        raise ValueError("Current timestamp must be timezone-aware.")

    elapsed = current_time - last_seen_at

    if elapsed <= offline_after:
        return "online"

    return "offline"
