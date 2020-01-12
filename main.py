import datetime
import json
from danmu.bili_danmu import WsDanmuClient
import asyncio
from urllib import request
import sys

loop = asyncio.get_event_loop()
if len(sys.argv) is 1:
    room_id = 21669084
else:
    room_id = int(sys.argv[1])


class MessageLogger:
    def __init__(self):
        self.logger = None
        self.file = None
        self.filename = None

    def new_log_file(self, room_id_, live_status):
        time_now = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        live_status_text = '直播' if live_status == 1 else '下播'
        self.filename = '%s_%s_%s' % (room_id_, time_now, live_status_text)
        pass

    def write(self, data):
        with open(self.filename, 'a+', encoding='utf-8')as f:
            f.write(data)


class MonitorForQuestionMark(WsDanmuClient):
    def __init__(self, room_id_: int):
        super().__init__(room_id_)
        self.live_status = self.get_live_status()
        self.logger = MessageLogger()
        self.logger.new_log_file(self.room_id, self.live_status)

    @staticmethod
    def get_live_status():
        req = request.Request('https://api.live.bilibili.com/room/v1/Room/get_info?room_id=%s' % room_id)
        req.add_header('User-Agent',
                       'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                       ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36')
        r = request.urlopen(req)
        if r.status is 200:
            data = r.read().decode()
            data = json.loads(data)
            live_status = data['data']['live_status']
            if live_status is 1:
                print('正在直播')
            # elif live_status is 2:
            #     print('轮播中')
            else:
                print('准备中')
            return live_status

    def handle_danmu(self, data: dict) -> bool:
        cmd = data['cmd']
        # print(data)
        if cmd == 'DANMU_MSG':
            # print(data)
            message_info = data['info']
            # 0普通消息1节奏风暴2抽奖
            is_normal_message = True if message_info[0][9] is 0 else False
            if is_normal_message:
                message_time = message_info[0][4]
                message_text = message_info[1]
                message_username = message_info[2][1]
                message_user_id = message_info[2][0]
                save_body = {'time': message_time, 'text': message_text, 'username': message_username,
                             'user_id': message_user_id}
                save_str = json.dumps(save_body, ensure_ascii=False) + ','
                print(save_str)
                self.logger.write(save_str)
        elif cmd == 'SUPER_CHAT_MESSAGE':
            superchat_data = data['data']
            message_time = superchat_data['ts'] * 1000
            superchat_price = superchat_data['price']
            message_text = superchat_data['message']
            message_username = superchat_data['user_info']['uname']
            message_user_id = superchat_data['uid']
            save_body = {'time': message_time, 'text': message_text, 'username': message_username,
                         'user_id': message_user_id, 'superchat_price': superchat_price}
            save_str = json.dumps(save_body, ensure_ascii=False) + ','
            print(save_str)
            self.logger.write(save_str)
        elif cmd == 'LIVE':
            self.live_status = 1
            self.logger.new_log_file(self.room_id, self.live_status)
            print('开播了')
        elif cmd == 'PREPARING':
            self.live_status = 0
            self.logger.new_log_file(self.room_id, self.live_status)
            print('准备中')
        return True


# 程序开始
monitor = MonitorForQuestionMark(room_id)
task = [monitor.run()]
loop.run_until_complete(asyncio.wait(task))
# loop.run_forever()
