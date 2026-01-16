import requests,json,os
# -------------------------------------------------------------------------------------------
# github workflows
# -------------------------------------------------------------------------------------------
if __name__ == '__main__':
# pushplus秘钥 申请地址 http://www.pushplus.plus
    sckey = os.environ.get("PUSHPLUS_TOKEN", "")
# 推送内容
    sendContent = ''
# glados账号cookie 直接使用数组 如果使用环境变量需要字符串分割一下
    cookies_raw = os.environ.get("GLADOS_COOKIE", "")
    cookies = []
    for cookie in cookies_raw.split("&"):
        cookie = cookie.replace("\r", "").replace("\n", "").strip()
        if cookie:
            cookies.append(cookie)
    if not cookies:
        print('未获取到COOKIE变量') 
        cookies = []
        exit(0)
    url= "https://glados.rocks/api/user/checkin"
    url2= "https://glados.rocks/api/user/status"
    exchange_url = "https://glados.rocks/api/user/points/exchange"
    referer = 'https://glados.rocks/console/checkin'
    origin = "https://glados.rocks"
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    payload={
        'token': 'glados.one'
    }
    auto_exchange_200 = os.environ.get("AUTO_EXCHANGE_200", "1").lower() not in ("0", "false", "no")
    for cookie in cookies:
        checkin = requests.post(url,headers={'cookie': cookie ,'referer': referer,'origin':origin,'user-agent':useragent,'content-type':'application/json;charset=UTF-8'},data=json.dumps(payload))
        state =  requests.get(url2,headers={'cookie': cookie ,'referer': referer,'origin':origin,'user-agent':useragent})
    #--------------------------------------------------------------------------------------------------------#  
        try:
            state_json = state.json()
        except Exception:
            print('状态接口返回异常(非JSON)，可能是cookie无效或被拦截')
            if sckey != "":
                requests.get('http://www.pushplus.plus/send?token=' + sckey + '&content=' + '状态接口返回非JSON，可能cookie无效')
            continue

        data = state_json.get('data') or {}
        email = data.get('email') or 'unknown'
        left_days = data.get('leftDays')
        points = data.get('points')
        if points is None:
            points = data.get('point') or data.get('score') or data.get('balance')
        if not left_days:
            msg = state_json.get('message') or state_json.get('msg') or str(state_json)
            print(email + '----状态获取失败--' + msg)
            if sckey != "":
                requests.get('http://www.pushplus.plus/send?token=' + sckey + '&content=' + email + '状态获取失败，可能cookie已失效')
            continue

        time = str(left_days).split('.')[0]

        mess = None
        try:
            checkin_json = checkin.json()
            mess = checkin_json.get('message') or checkin_json.get('msg')
        except Exception:
            mess = None

        if mess:
            print(email+'----结果--'+mess+'----剩余('+time+')天')  # 日志输出
            sendContent += email+'----'+mess+'----剩余('+time+')天\n'
        else:
            requests.get('http://www.pushplus.plus/send?token=' + sckey + '&content='+email+'cookie已失效')
            print(email + '----cookie已失效')  # 日志输出

        points_value = None
        try:
            if points is not None:
                points_value = int(float(points))
        except Exception:
            points_value = None

        if auto_exchange_200 and points_value is not None and points_value >= 200:
            exchange_payload = {'points': 200}
            exchange = requests.post(exchange_url,headers={'cookie': cookie ,'referer': referer,'origin':origin,'user-agent':useragent,'content-type':'application/json;charset=UTF-8'},data=json.dumps(exchange_payload))
            exchange_msg = None
            try:
                exchange_json = exchange.json()
                exchange_msg = exchange_json.get('message') or exchange_json.get('msg') or str(exchange_json)
            except Exception:
                exchange_msg = exchange.text or 'exchange failed'
            print(email+'----exchange 200->30 days--'+exchange_msg)
            sendContent += email+'----exchange 200->30 days--'+exchange_msg+'\n'
     #--------------------------------------------------------------------------------------------------------#   
    if sckey != "":
         requests.get('http://www.pushplus.plus/send?token=' + sckey + '&title='+email+'签到成功'+'&content='+sendContent)


