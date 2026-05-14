from llm.openai_compatible import chat_once


def main():
    print("AI 测试启动。输入一句话，按回车发送。")
    user_message = input("你：").strip()
    if not user_message:
        user_message = "今天有点累"

    reply = chat_once(user_message)
    print(f"AI：{reply}")


if __name__ == "__main__":
    main()
