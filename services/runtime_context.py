from datetime import datetime


WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def format_utc_offset(now):
    offset = now.strftime("%z")
    if not offset:
        return "未知"

    return f"{offset[:3]}:{offset[3:]}"


def build_runtime_context():
    now = datetime.now().astimezone()
    weekday = WEEKDAYS[now.weekday()]

    return "\n".join(
        [
            f"当前本地时间：{now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"当前星期：{weekday}",
            f"UTC 偏移：{format_utc_offset(now)}",
            "回答现在几点、今天、明天、昨天、周几等时间相关问题时，必须以这里为准。",
        ]
    )
