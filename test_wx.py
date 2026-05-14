from wxauto import WeChat
import time

print("正在连接微信...")

wx = WeChat()

print("微信连接成功")

time.sleep(2)

wx.SendMsg(
    "Hello",
    "文件传输助手"
)

print("消息发送成功")