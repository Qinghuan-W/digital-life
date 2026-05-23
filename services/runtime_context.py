from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
FIXED_TIMEZONES = {
    "Asia/Shanghai": timezone(timedelta(hours=8), name="Asia/Shanghai"),
    "China": timezone(timedelta(hours=8), name="Asia/Shanghai"),
    "UTC": timezone.utc,
}


def get_configured_now(timezone_name="local"):
    timezone_name = str(timezone_name or "local").strip()
    if not timezone_name or timezone_name.lower() == "local":
        return datetime.now().astimezone(), "local"

    try:
        return datetime.now(ZoneInfo(timezone_name)), timezone_name
    except ZoneInfoNotFoundError:
        fixed_timezone = FIXED_TIMEZONES.get(timezone_name)
        if fixed_timezone:
            return datetime.now(fixed_timezone), timezone_name

        fallback_note = f"local（配置的时区 {timezone_name} 无效，已回退）"
        return datetime.now().astimezone(), fallback_note


def format_utc_offset(now):
    offset = now.strftime("%z")
    if not offset:
        return "未知"

    return f"{offset[:3]}:{offset[3:]}"


def build_runtime_context(timezone_name="local"):
    now, resolved_timezone = get_configured_now(timezone_name)
    weekday = WEEKDAYS[now.weekday()]

    return "\n".join(
        [
            f"当前时区：{resolved_timezone}",
            f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"当前星期：{weekday}",
            f"UTC 偏移：{format_utc_offset(now)}",
            "回答现在几点、今天、明天、昨天、周几等时间相关问题时，必须以这里为准。",
        ]
    )
