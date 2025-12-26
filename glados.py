import requests, json, os

# -------------------------------------------------------------------------------------------
# 配置部分
# -------------------------------------------------------------------------------------------
sckey = os.environ.get("PUSHPLUS_TOKEN", "")
sendContent = ''
cookies = os.environ.get("GLADOS_COOKIE", "").split("&")

def start():
    global sendContent
    if not cookies or cookies[0] == "":
        print('未获取到COOKIE变量')
        return

    # 用于存储标题的变量
    push_title = "GLaDOS签到通知"
    all_get_points = [] # 记录所有账号获得的点数

    url = "https://glados.rocks/api/user/checkin"
    url2 = "https://glados.rocks/api/user/status"
    referer = 'https://glados.rocks/console/checkin'
    origin = "https://glados.rocks"
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    payload = {'token': 'glados.one'}

    for cookie in cookies:
        checkin = requests.post(url, headers={'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent, 'content-type': 'application/json;charset=UTF-8'}, data=json.dumps(payload))
        state = requests.get(url2, headers={'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent})
        
        try:
            state_json = state.json()
            checkin_json = checkin.json()
            email = state_json['data']['email']
            time = state_json['data']['leftDays'].split('.')[0]
            
            if 'message' in checkin_json:
                mess = checkin_json['message']
                
                # --- 1. 获取本次获得的点数 (用于标题) ---
                # 逻辑：从 "Get 1 Points" 这种字符串中提取数字
                import re
                current_get = re.findall(r"Get (\d+) Points", mess)
                if current_get:
                    all_get_points.append(f"{current_get[0]}点")
                else:
                    all_get_points.append("0点")

                # --- 2. 获取总点数 (用于正文) ---
                try:
                    balance = str(checkin_json['list'][0]['balance']).split('.')[0]
                    balance_str = f"----总点数({balance})"
                except:
                    balance_str = "----总点数(已签到)"
                
                info = f"{email}----{mess}{balance_str}----剩余({time})天"
                print(info)
                sendContent += info + '\n'
            else:
                sendContent += f"{email} cookie已失效\n"
        except Exception as e:
            print(f"解析出错: {e}")

    # --- 3. 动态构造标题 ---
    if all_get_points:
        # 如果有多个账号，标题会显示如：签到成功获得[1点, 1点]
        push_title = f"签到获得: {', '.join(all_get_points)}"

    # 执行推送
    if sckey != "":
        push_url = 'http://www.pushplus.plus/send'
        data = {
            "token": sckey,
            "title": push_title,  # 这里使用了动态标题
            "content": sendContent,
            "template": "txt"
        }
        requests.post(push_url, data=json.dumps(data), headers={'Content-Type':'application/json'})

if __name__ == '__main__':
    start()
