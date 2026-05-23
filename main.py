import time
import re

from wxauto import WeChat

from llm.openai_compatible import (
    classify_reply_timing,
    chat_once,
    load_config,
    summarize_long_term_memory,
    update_core_profile,
)
from services.context_store import append_exchange, get_history
from services.long_term_memory import (
    archive_overflow_messages,
    clear_pending_messages,
    format_pending_messages,
    format_core_profile,
    get_memory_status,
    load_core_profile,
    load_long_term_memory,
    load_memory_context,
    load_pending_messages,
    save_core_profile,
    save_long_term_memory,
)


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
    for chunk in re.split(r"[\\$]+|\r?\n+", text):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)

    return parts[:max_parts]


def should_update_core_profile(text, mode="smart"):
    if not text:
        return False

    mode = str(mode or "smart").lower()
    if mode in ("off", "false", "disabled"):
        return False
    if mode in ("always", "all"):
        return True

    profile_signal_words = [
        "我叫",
        "我是",
        "叫我",
        "喊我",
        "称呼",
        "我的名字",
        "我的昵称",
        "我的",
        "我在",
        "我有",
        "我家",
        "喜欢",
        "最爱",
        "超爱",
        "爱吃",
        "爱喝",
        "迷上",
        "上头",
        "离不开",
        "真香",
        "能连",
        "讨厌",
        "不喜欢",
        "不爱",
        "反感",
        "受不了",
        "吃不了",
        "喝不了",
        "不吃",
        "不喝",
        "过敏",
        "雷点",
        "害怕",
        "怕",
        "记住",
        "记一下",
        "记得",
        "以后",
        "不要",
        "别",
        "别再",
        "千万别",
        "下次",
        "一般",
        "通常",
        "经常",
        "每天",
        "总是",
        "习惯",
        "长期",
    ]
    return any(word in text for word in profile_signal_words)


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


def drain_startup_messages(wx, wechat_config):
    if not wechat_config.get("drain_startup_messages", True):
        return

    quiet_seconds = float(wechat_config.get("drain_startup_quiet_seconds", 2))
    max_seconds = float(wechat_config.get("drain_startup_max_seconds", 12))
    end_at = time.time() + max_seconds
    quiet_since = time.time()
    drained_count = 0

    while time.time() < end_at:
        try:
            messages_by_chat = wx.GetListenMessage()
            batch_count = sum(len(msg_list) for msg_list in messages_by_chat.values())
            if batch_count:
                drained_count += batch_count
                quiet_since = time.time()
        except Exception as error:
            print(f"清空启动缓存消息时出错：{error}")
            break

        if time.time() - quiet_since >= quiet_seconds:
            break

        time.sleep(0.2)

    if drained_count:
        print(f"已忽略启动时缓存消息 {drained_count} 条")
    else:
        print("启动时没有发现缓存消息")


def enqueue_message(message_queues, who, sender, content, prompt_file):
    queue_item = message_queues.setdefault(
        who,
        {
            "messages": [],
            "sender": sender,
            "prompt_file": prompt_file,
            "last_message_at": time.time(),
        },
    )
    queue_item["messages"].append(content)
    queue_item["sender"] = sender
    queue_item["prompt_file"] = prompt_file
    queue_item["last_message_at"] = time.time()


def process_ready_queues(
    wx,
    message_queues,
    memory_config,
    wechat_config,
    max_history_messages,
    recent_sent,
):
    queue_wait_seconds = float(wechat_config.get("queue_wait_seconds", 6))
    now = time.time()

    ready_names = [
        who
        for who, queue_item in message_queues.items()
        if now - queue_item["last_message_at"] >= queue_wait_seconds
    ]

    for who in ready_names:
        queue_item = message_queues.pop(who)
        messages = queue_item["messages"]
        prompt_file = queue_item.get("prompt_file")
        merged_content = "\n".join(messages)
        summary_job = None
        profile_job = None

        print("------ 合并处理消息 ------")
        print("聊天对象：", who)
        print("消息条数：", len(messages))
        print("合并内容：", merged_content)

        try:
            received_at = queue_item["last_message_at"]
            history = get_history(who, max_history_messages)
            long_term_memory = ""
            if memory_config.get("enable_long_term_memory", True):
                long_term_memory = load_memory_context(
                    who,
                    max_pending_messages=int(
                        memory_config.get("max_pending_messages_for_reply", 20)
                    ),
                )
                memory_status = get_memory_status(who)
                profile_label = "有" if memory_status["has_profile"] else "无"
                summary_label = "有" if memory_status["has_summary"] else "无"
                print(
                    "记忆状态："
                    f"近期 {len(history)} 条，"
                    f"核心资料 {profile_label}，"
                    f"长期总结 {summary_label}，"
                    f"待总结 {memory_status['pending_count']} 条"
                )

            timing = classify_reply_timing(merged_content, history=history)
            print(
                "回复时机："
                f"{timing['profile']}，目标等待 "
                f"{timing['delay_seconds']:.1f} 秒，原因：{timing['reason']}"
            )
            reply = chat_once(
                merged_content,
                prompt_file=prompt_file,
                history=history,
                long_term_memory=long_term_memory,
            )
            overflow_messages = append_exchange(
                who,
                merged_content,
                reply,
                max_history_messages,
            )
            if memory_config.get("enable_long_term_memory", True):
                archived_count = archive_overflow_messages(who, overflow_messages)
                if archived_count:
                    print(f"已加入长期记忆待总结区 {archived_count} 条")

                pending_messages = load_pending_messages(who)
                summarize_after = int(
                    memory_config.get("summarize_overflow_after_messages", 8)
                )
                if len(pending_messages) >= summarize_after:
                    pending_text = format_pending_messages(pending_messages)
                    current_memory = load_long_term_memory(who)
                    summary_job = {
                        "who": who,
                        "current_memory": current_memory,
                        "pending_text": pending_text,
                    }

                profile_enabled = memory_config.get("enable_core_profile", True)
                profile_update_mode = memory_config.get(
                    "core_profile_update_mode",
                    "smart",
                )
                if profile_enabled and should_update_core_profile(
                    merged_content,
                    mode=profile_update_mode,
                ):
                    profile_job = {
                        "who": who,
                        "user_message": merged_content,
                        "assistant_message": reply,
                        "history": history,
                    }
        except Exception as error:
            print(f"AI 调用失败：{error}")
            timing = {"delay_seconds": 0}
            reply = "我这边刚刚有点卡住了\\你再和我说一遍好不好"
            received_at = queue_item["last_message_at"]

        elapsed_seconds = time.time() - received_at
        remaining_delay = max(0, timing["delay_seconds"] - elapsed_seconds)
        send_reply(
            wx,
            who,
            reply,
            wechat_config,
            recent_sent,
            initial_delay_seconds=remaining_delay,
        )

        if summary_job:
            try:
                updated_memory = summarize_long_term_memory(
                    summary_job["current_memory"],
                    summary_job["pending_text"],
                )
                save_long_term_memory(summary_job["who"], updated_memory)
                clear_pending_messages(summary_job["who"])
                print(f"已更新 {summary_job['who']} 的长期记忆")
            except Exception as error:
                print(f"长期记忆总结失败：{error}")

        if profile_job:
            try:
                current_profile = load_core_profile(profile_job["who"])
                profile_result = update_core_profile(
                    current_profile,
                    profile_job["user_message"],
                    profile_job["assistant_message"],
                    history=profile_job["history"],
                )
                if profile_result.get("should_update"):
                    updated_profile = profile_result.get("profile", {})
                    old_text = format_core_profile(current_profile)
                    new_text = format_core_profile(updated_profile)

                    if new_text and new_text != old_text:
                        save_core_profile(profile_job["who"], updated_profile)
                        reason = profile_result.get("reason", "")
                        print(f"已更新 {profile_job['who']} 的核心资料：{reason}")
                    else:
                        print(f"核心资料无变化：{profile_job['who']}")
            except Exception as error:
                print(f"核心资料更新失败：{error}")


def send_reply(
    wx,
    who,
    reply,
    wechat_config,
    recent_sent,
    initial_delay_seconds=0,
):
    part_base_delay = float(wechat_config.get("part_base_delay_seconds", 0.8))
    typing_seconds_per_char = float(wechat_config.get("typing_seconds_per_char", 0.08))
    max_parts = int(wechat_config.get("max_reply_parts", 6))

    parts = split_reply(reply, max_parts=max_parts)
    if not parts:
        print("AI 返回了空回复，已跳过发送。")
        return

    initial_delay_seconds = max(0, float(initial_delay_seconds))
    if initial_delay_seconds > 0:
        print(f"等待 {initial_delay_seconds:.1f} 秒后回复 {who}")
        time.sleep(initial_delay_seconds)

    for index, part in enumerate(parts, start=1):
        print(f"发送回复 {index}/{len(parts)} -> {who}: {part}")
        wx.SendMsg(msg=part, who=who)
        recent_sent.append((part, time.time()))

        if index < len(parts):
            typing_delay = len(parts[index]) * typing_seconds_per_char
            part_delay = part_base_delay + typing_delay
            print(f"等待 {part_delay:.1f} 秒后发送下一段")
            time.sleep(part_delay)


def main():
    config = load_config()
    bot_config = config.get("bot", {})
    memory_config = config.get("memory", {})
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

    drain_startup_messages(wx, wechat_config)

    print("自动回复已启动。你现在可以在微信里发消息。")
    print("按 Ctrl + C 退出。")

    recent_sent = []
    message_queues = {}

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

                    enqueue_message(message_queues, who, sender, content, prompt_file)
                    print(f"已加入消息队列：{who} <- {content}")

            process_ready_queues(
                wx,
                message_queues,
                memory_config,
                wechat_config,
                max_history_messages,
                recent_sent,
            )

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("已退出自动回复。")
            break
        except Exception as error:
            print(f"主循环出错：{error}")
            time.sleep(2)


if __name__ == "__main__":
    main()
