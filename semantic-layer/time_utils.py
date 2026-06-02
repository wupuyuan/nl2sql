from datetime import datetime, timedelta


def parse_time(query: str):
    today = datetime.now().date()

    if "昨天" in query:
        d = today - timedelta(days=1)
        return str(d), str(d)

    if "今天" in query:
        return str(today), str(today)

    if "最近7天" in query:
        return str(today - timedelta(days=7)), str(today)

    return None, None
