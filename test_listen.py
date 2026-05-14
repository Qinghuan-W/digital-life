from wxauto import WeChat
import time

print("正在连接微信...")
wx = WeChat()
print("微信连接成功")

listen_name = "文件传输助手"

print(f"正在切换到聊天：{listen_name}")
wx.ChatWith(listen_name)

time.sleep(2)

print(f"开始监听：{listen_name}")
wx.AddListenChat(who=listen_name)

print("现在你可以在微信里给文件传输助手发消息")
print("按 Ctrl + C 退出")

while True:
    msgs = wx.GetListenMessage()

    for chat, msg_list in msgs.items():
        for msg in msg_list:
            print("------ 收到消息 ------")
            print("聊天对象：", chat.who)
            print("发送人：", msg.sender)
            print("消息类型：", msg.type)
            print("消息内容：", msg.content)

    time.sleep(1)