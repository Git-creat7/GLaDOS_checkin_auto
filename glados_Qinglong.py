import requests, json, os

# pushplus秘钥
sckey = os.environ.get("PUSHPLUS_TOKEN", "")
sendContent = ''
# glados账号cookie
cookies = os.environ.get("GLADOS_COOKIE", "").split("&")

if not cookies or cookies[0] == "":
    print('未获取到COOKIE变量') 
    exit(0)

def start():    
    global sendContent
    # --- 域名更新为 glados.cloud ---
    url = "https://glados.cloud/api/user/checkin"
    url2 = "https://glados.cloud/api/user/status"
    referer = 'https://glados.cloud/console/checkin'
    origin = "https://glados.cloud"
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    payload = {
        'token': 'glados.one'
    }
    
    for cookie in cookies:
        try:
            checkin = requests.post(url, headers={'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent, 'content-type': 'application/json;charset=UTF-8'}, data=json.dumps(payload))
            state = requests.get(url2, headers={'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent})
            
            # 解析数据
            state_json = state.json()
            time = state_json['data']['leftDays'].split('.')[0]
            email = state_json['data']['email']

            if 'message' in checkin.text:
                mess = checkin.json()['message']
                log_info = email + '----' + mess + '----剩余(' + time + ')天'
                print(log_info)  # 日志输出
                sendContent += log_info + '\n'
            else:
                # 签到失败的情况
                error_msg = email + ' 更新cookie'
                print(error_msg)
                if sckey != "":
                    requests.get('http://www.pushplus.plus/send?token=' + sckey + '&content=' + error_msg)
        except Exception as e:
            print(f"账号处理出错: {e}")
            continue

def main_handler(event, context):
    return start()

if __name__ == '__main__':
    start()
    if sckey != "":
        print("当前使用的 PUSHPLUS_TOKEN:", sckey)
        # 使用你原本的推送逻辑
        res = requests.get('http://www.pushplus.plus/send?token=' + sckey + '&title=GLaDOS签到成功' + '&content=' + sendContent)
        print("PushPlus 推送响应内容:", res.text)
    else:
        print("未设置 PUSHPLUS_TOKEN，不执行推送")
