import requests, json, os

# -------------------------------------------------------------------------------------------
# 配置部分
# -------------------------------------------------------------------------------------------
# pushplus秘钥 申请地址 http://www.pushplus.plus
sckey = os.environ.get("PUSHPLUS_TOKEN", "")
# 推送内容初始化
sendContent = ''
# glados账号cookie
cookies = os.environ.get("GLADOS_COOKIE", "").split("&")


def start():
    global sendContent
    if not cookies or cookies[0] == "":
        print('未获取到COOKIE变量')
        return

    url = "https://glados.rocks/api/user/checkin"
    url2 = "https://glados.rocks/api/user/status"
    referer = 'https://glados.rocks/console/checkin'
    origin = "https://glados.rocks"
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    payload = {'token': 'glados.one'}

    for cookie in cookies:
        # 签到请求
        checkin = requests.post(url, headers={'cookie': cookie, 'referer': referer, 'origin': origin,
                                              'user-agent': useragent,
                                              'content-type': 'application/json;charset=UTF-8'},
                                data=json.dumps(payload))
        # 状态查询
        state = requests.get(url2,
                             headers={'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent})

        try:
            state_json = state.json()
            checkin_json = checkin.json()

            time = state_json['data']['leftDays'].split('.')[0]
            email = state_json['data']['email']

            if 'message' in checkin_json:
                mess = checkin_json['message']

                # --- 核心：提取总点数 ---
                # 只有签到成功或返回列表时才能拿到 balance
                try:
                    balance = checkin_json['list'][0]['balance']
                    balance_str = f"----总点数({int(float(balance))})"
                except (KeyError, IndexError):
                    balance_str = "----总点数(今日已查)"

                    # 格式化日志和推送内容
                info = f"{email}----{mess}{balance_str}----剩余({time})天"
                print(info)
                sendContent += info + '\n'
            else:
                msg = f"{email} cookie已失效"
                print(msg)
                sendContent += msg + '\n'
        except Exception as e:
            print(f"解析出错: {e}")

    # 执行推送
    if sckey != "":
        push_url = 'http://www.pushplus.plus/send'
        data = {
            "token": sckey,
            "title": "GLaDOS签到结果",
            "content": sendContent,
            "template": "txt"
        }
        requests.post(push_url, data=json.dumps(data), headers={'Content-Type': 'application/json'})


def main_handler(event, context):
    return start()


if __name__ == '__main__':
    start()
