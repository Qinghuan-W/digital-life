import time

from wxauto import WeChat

from llm.openai_compatible import chat_once, load_config
from services.context_store import append_exchange, get_history


def get_enabled_contacts(wechat_config):
    contacts = wechat_config.get("contacts")

    if contacts:
        enabled_contacts = []
        for contact in contacts:
            if contact.get("enabled", True):
                enabled_contacts.append(contact)
        return enabled_contacts

    listen_names = wechat_config.get("listen_names", ["文件传输助手"])
    return [
        {
            "name": listen_name,
            "enabled": True,
            "prompt_file": None,
        }
        for listen_name in listen_names
    ]


def split_reply(text, max_parts):
    if not text:
        return []

    parts = []
    for chunk in text.replace("$", "\\").split("\\"):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)

    return parts[:max_parts]


def add_listen_chat(wx, listen_name, wechat_config):
    open_timeout = float(wechat_config.get("chat_open_timeout_seconds", 5))
    setup_delay = float(wechat_config.get("listen_setup_delay_seconds", 2.5))
    retries = int(wechat_config.get("listen_setup_retries", 3))

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            print(f"正在切换到聊天：{listen_name}（第 {attempt}/{retries} 次）")
            matched_name = wx.ChatWith(listen_name, timeout=open_timeout)
            if matched_name and matched_name != listen_name:
                print(f"微信实际打开的聊天名：{matched_name}")

            time.sleep(setup_delay)

            print(f"开始监听：{listen_name}")
            wx.AddListenChat(who=listen_name)
            return True
        except Exception as error:
            last_error = error
            print(f"监听 {listen_name} 失败：{error}")
            if attempt < retries:
                print("稍等一下再重试...")
                time.sleep(1.5)

    print("")
    print(f"无法监听：{listen_name}")
    print("请检查：")
    print("1. config.yaml 里的 name 是否和微信备注/群名完全一致")
    print("2. 电脑版微信是否停留在正常聊天界面，不要停在设置、通讯录或弹窗")
    print("3. 先手动点开这个聊天窗口，再重新运行 python main.py")
    print(f"最后一次错误：{last_error}")
    return False


def should_ignore_message(msg, recent_sent):
    msg_type = getattr(msg, "type", "")
    content = (getattr(msg, "content", "") or "").strip()

    if not content:
        return True

    if msg_type not in ("text", "friend"):
        return True

    now = time.time()
    for sent_content, sent_at in list(recent_sent):
        if now - sent_at > 30:
            recent_sent.remove((sent_content, sent_at))
            continue
        if content == sent_content:
            return True

    return False


def send_reply(wx, who, reply, wechat_config, recent_sent):
    reply_delay = float(wechat_config.get("reply_delay_seconds", 1.2))
    max_parts = int(wechat_config.get("max_reply_parts", 6))

    parts = split_reply(reply, max_parts=max_parts)
    if not parts:
        print("AI 返回了空回复，已跳过发送。")
        return

    for index, part in enumerate(parts, start=1):
        print(f"发送回复 {index}/{len(parts)} -> {who}: {part}")
        wx.SendMsg(msg=part, who=who)
        recent_sent.append((part, time.time()))
        time.sleep(reply_delay)


def main():
    config = load_config()
    bot_config = config.get("bot", {})
    wechat_config = config.get("wechat", {})
    contacts = get_enabled_contacts(wechat_config)
    contact_by_name = {contact["name"]: contact for contact in contacts}
    max_history_messages = int(bot_config.get("max_history_messages", 10))
    poll_interval = float(wechat_config.get("poll_interval_seconds", 1))
    debug_messages = bool(wechat_config.get("debug_messages", False))

    if not contacts:
        print("没有启用的微信监听对象。请在 config.yaml 的 wechat.contacts 里添加联系人。")
        return

    print("正在连接微信...")
    wx = WeChat()
    print("微信连接成功")

    active_contacts = []
    for contact in contacts:
        listen_name = contact["name"]
        if add_listen_chat(wx, listen_name, wechat_config):
            active_contacts.append(contact)

    if not active_contacts:
        print("没有任何监听对象启动成功，程序已停止。")
        return

    contact_by_name = {contact["name"]: contact for contact in active_contacts}

    print("自动回复已启动。你现在可以在微信里发消息。")
    print("按 Ctrl + C 退出。")

    recent_sent = []

    while True:
        try:
            messages_by_chat = wx.GetListenMessage()

            for chat, msg_list in messages_by_chat.items():
                who = chat.who
                contact = contact_by_name.get(who, {})
                prompt_file = contact.get("prompt_file")

                for msg in msg_list:
                    if debug_messages:
                        print(
                            "调试：wxauto 捕获消息 -> "
                            f"聊天对象={who}, "
                            f"发送人={getattr(msg, 'sender', '')}, "
                            f"类型={getattr(msg, 'type', '')}, "
                            f"属性={getattr(msg, 'attr', '')}, "
                            f"内容={(getattr(msg, 'content', '') or '')[:80]}"
                        )

                    if should_ignore_message(msg, recent_sent):
                        continue

                    content = (msg.content or "").strip()
                    sender = getattr(msg, "sender", "")

                    print("------ 收到消息 ------")
                    print("聊天对象：", who)
                    print("发送人：", sender)
                    print("消息内容：", content)

                    try:
                        history = get_history(who, max_history_messages)
                        reply = chat_once(content, prompt_file=prompt_file, history=history)
                        append_exchange(who, content, reply, max_history_messages)
                    except Exception as error:
                        print(f"AI 调用失败：{error}")
                        reply = "我这边刚刚有点卡住了\\你再和我说一遍好不好"

                    send_reply(wx, who, reply, wechat_config, recent_sent)

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("已退出自动回复。")
            break
        except Exception as error:
            print(f"主循环出错：{error}")
            time.sleep(2)


if __name__ == "__main__":
    main()
