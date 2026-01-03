import requests, json, os, re

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

    push_title = "GLaDOS签到通知"
    all_get_points = [] 

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
                
                # --- 优化：从 list 列表中提取今日真实点数 ---
                point_get = "0"
                try:
                    # 获取列表第一条记录（最近的一次变动）
                    change = checkin_json['list'][0]['change']
                    # 转换成数字（去除正号或小数点）
                    point_get = str(int(float(change)))
                    all_get_points.append(f"{point_get}点")
                except:
                    # 如果拿不到 list，再尝试从文字匹配（保底方案）
                    current_get = re.findall(r"Get (\d+) Points", mess)
                    point_get = current_get[0] if current_get else "0"
                    all_get_points.append(f"{point_get}点")

                # --- 获取总余额 ---
                try:
                    balance = str(checkin_json['list'][0]['balance']).split('.')[0]
                    balance_str = f"----总点数({balance})"
                except:
                    balance_str = "----总点数(已签到)"
                
                info = f"{email}----{mess}----本次获得:{point_get}点{balance_str}----剩余({time})天"
                print(info)
                sendContent += info + '\n'
            else:
                sendContent += f"{email} cookie已失效\n"
        except Exception as e:
            print(f"解析出错: {e}")

    # 动态构造标题
    if all_get_points:
        push_title = f"签到获得: {', '.join(all_get_points)}"

    if sckey != "":
        push_url = 'http://www.pushplus.plus/send'
        data = {"token": sckey, "title": push_title, "content": sendContent, "template": "txt"}
        requests.post(push_url, data=json.dumps(data), headers={'Content-Type':'application/json'})

if __name__ == '__main__':
    start()
