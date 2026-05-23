from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
FIXED_TIMEZONES = {
    "Asia/Shanghai": timezone(timedelta(hours=8), name="Asia/Shanghai"),
    "China": timezone(timedelta(hours=8), name="Asia/Shanghai"),
    "UTC": timezone.utc,
}
USER_TIMEZONE_HINTS = [
    (
        "Europe/London",
        [
            "英国",
            "英格兰",
            "苏格兰",
            "威尔士",
            "北爱尔兰",
            "伦敦",
            "布里斯托",
            "uk",
            "united kingdom",
            "england",
            "scotland",
            "wales",
            "northern ireland",
            "london",
            "bristol",
        ],
    ),
    (
        "Asia/Shanghai",
        [
            "中国",
            "国内",
            "北京",
            "上海",
            "广州",
            "深圳",
            "杭州",
            "南京",
            "成都",
            "重庆",
            "武汉",
            "西安",
            "china",
        ],
    ),
]


def get_last_sunday(year, month):
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)

    last_day = next_month - timedelta(days=1)
    days_since_sunday = (last_day.weekday() + 1) % 7
    return last_day.day - days_since_sunday


def get_london_timezone():
    utc_now = datetime.now(timezone.utc)
    year = utc_now.year
    dst_start_day = get_last_sunday(year, 3)
    dst_end_day = get_last_sunday(year, 10)
    dst_start = datetime(year, 3, dst_start_day, 1, tzinfo=timezone.utc)
    dst_end = datetime(year, 10, dst_end_day, 1, tzinfo=timezone.utc)
    offset_hours = 1 if dst_start <= utc_now < dst_end else 0
    return timezone(timedelta(hours=offset_hours), name="Europe/London")


DYNAMIC_TIMEZONES = {
    "Europe/London": get_london_timezone,
    "UK": get_london_timezone,
}


def get_configured_now(timezone_name="local"):
    timezone_name = str(timezone_name or "local").strip()
    if not timezone_name or timezone_name.lower() == "local":
        return datetime.now().astimezone(), "local"

    try:
        return datetime.now(ZoneInfo(timezone_name)), timezone_name
    except ZoneInfoNotFoundError:
        dynamic_timezone = DYNAMIC_TIMEZONES.get(timezone_name)
        if dynamic_timezone:
            return datetime.now(dynamic_timezone()), timezone_name

        fixed_timezone = FIXED_TIMEZONES.get(timezone_name)
        if fixed_timezone:
            return datetime.now(fixed_timezone), timezone_name

        fallback_note = f"local（配置的时区 {timezone_name} 无效，已回退）"
        return datetime.now().astimezone(), fallback_note


def infer_user_timezone_from_memory(memory_text):
    normalized_text = str(memory_text or "").lower()
    if not normalized_text:
        return None

    for timezone_name, hints in USER_TIMEZONE_HINTS:
        for hint in hints:
            if hint.lower() in normalized_text:
                return timezone_name

    return None


def format_utc_offset(now):
    offset = now.strftime("%z")
    if not offset:
        return "未知"

    return f"{offset[:3]}:{offset[3:]}"


def build_runtime_context(timezone_name="local", user_memory_text=None):
    now, resolved_timezone = get_configured_now(timezone_name)
    weekday = WEEKDAYS[now.weekday()]
    user_timezone_name = infer_user_timezone_from_memory(user_memory_text)

    lines = [
        f"机器人当前时区：{resolved_timezone}",
        f"机器人当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"机器人当前星期：{weekday}",
        f"机器人 UTC 偏移：{format_utc_offset(now)}",
    ]

    if user_timezone_name:
        user_now, resolved_user_timezone = get_configured_now(user_timezone_name)
        user_weekday = WEEKDAYS[user_now.weekday()]
        lines.extend(
            [
                f"根据记忆推断的用户时区：{resolved_user_timezone}",
                f"根据记忆推断的用户当前时间：{user_now.strftime('%Y-%m-%d %H:%M:%S')}",
                f"根据记忆推断的用户当前星期：{user_weekday}",
                f"用户 UTC 偏移：{format_utc_offset(user_now)}",
            ]
        )

    lines.extend(
        [
            "时间理解规则：",
            "- 机器人时间表示你自己的当前时间，不一定是用户所在地时间。",
            "- 用户所在地、用户那边几点、用户说的“我这边”，要优先参考核心资料、长期记忆和聊天上下文。",
            "- 如果上面已经给出根据记忆推断的用户当前时间，回答用户那边或“我这边”时优先使用它。",
            "- 如果用户问“你那边”“你那里”“你的时间”，通常按机器人当前时间理解。",
            "- 如果用户说出的时间和运行时上下文冲突，要温和纠正，不要硬装作都一样。",
        ]
    )

    return "\n".join(lines)
