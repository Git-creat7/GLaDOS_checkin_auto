def start():
    global sendContent
    if not cookies or cookies[0] == "":
        print('未获取到COOKIE变量')
        return

    push_title = "GLaDOS签到通知"
    all_get_points = [] 

    # --- 核心修改部分：将 glados.rocks 替换为 glados.cloud ---
    url = "https://glados.cloud/api/user/checkin"
    url2 = "https://glados.cloud/api/user/status"
    referer = 'https://glados.cloud/console/checkin'
    origin = "https://glados.cloud"
    # ---------------------------------------------------

    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    payload = {'token': 'glados.one'}

    for cookie in cookies:
        # 注意：这里的 headers 已经同步更新了 referer 和 origin
        checkin = requests.post(url, headers={'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent, 'content-type': 'application/json;charset=UTF-8'}, data=json.dumps(payload))
        state = requests.get(url2, headers={'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent})
        
        try:
            state_json = state.json()
            checkin_json = checkin.json()
            email = state_json['data']['email']
            time = state_json['data']['leftDays'].split('.')[0]
            
            if 'message' in checkin_json:
                mess = checkin_json['message']
                
                point_get = "0"
                try:
                    change = checkin_json['list'][0]['change']
                    point_get = str(int(float(change)))
                    all_get_points.append(f"{point_get}点")
                except:
                    current_get = re.findall(r"Get (\d+) Points", mess)
                    point_get = current_get[0] if current_get else "0"
                    all_get_points.append(f"{point_get}点")

                try:
                    balance = str(checkin_json['list'][0]['balance']).split('.')[0]
                    balance_str = f"----总点数({balance})"
                except:
                    balance_str = "----总点数(已签到)"
                
                info = f"{email}----{mess}----本次获得:{point_get}点{balance_str}----剩余({time})天"
                print(info)
                sendContent += info + '\n'
            else:
                sendContent += f"{email} cookie已失效或配置错误\n"
        except Exception as e:
            print(f"解析出错: {e}")
            sendContent += f"账号解析出错，请检查Cookie是否为最新\n"
