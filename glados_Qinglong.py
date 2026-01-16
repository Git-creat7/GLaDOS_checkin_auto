import requests,json,os

# pushplus秘钥
sckey = os.environ.get("PUSHPLUS_TOKEN", "")
sendContent = ''
# glados账号cookie
cookies= os.environ.get("GLADOS_COOKIE", []).split("&")
if cookies[0] == "":
    print('未获取到COOKIE变量') 
    cookies = []
    exit(0)


def start():    
    url= "https://glados.rocks/api/user/checkin"
    url2= "https://glados.rocks/api/user/status"
    exchange_url = "https://glados.rocks/api/user/points/exchange"
    referer = 'https://glados.rocks/console/checkin'
    origin = "https://glados.rocks"
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    payload={
        'token': 'glados.one'
    }
    auto_exchange = os.environ.get("AUTO_EXCHANGE", os.environ.get("AUTO_EXCHANGE_200", "1")).lower() not in ("0", "false", "no")
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
        left_days = data.get('leftDays')
        time = str(left_days).split('.')[0] if left_days is not None else ''
        email = data.get('email') or 'unknown'
        points = data.get('points') or data.get('point') or data.get('score') or data.get('balance')
        if 'message' in checkin.text:
            mess = checkin.json()['message']
            print(email+'----'+mess+'----剩余('+time+')天')  # 日志输出
            global sendContent
            sendContent += email+'----'+mess+'----剩余('+time+')天\n'
        else:
            requests.get('http://www.pushplus.plus/send?token=' + sckey + '&content='+email+'更新cookie')

        left_days_value = None
        try:
            if left_days is not None:
                left_days_value = int(float(left_days))
        except Exception:
            left_days_value = None

        points_value = None
        try:
            if points is not None:
                points_value = int(float(points))
        except Exception:
            points_value = None

        exchange_points = None
        exchange_label = None
        if points_value is not None:
            if points_value >= 500:
                exchange_points = 500
                exchange_label = '500->100 days'
            elif points_value >= 200:
                exchange_points = 200
                exchange_label = '200->30 days'
            elif points_value >= 100:
                exchange_points = 100
                exchange_label = '100->10 days'

        if auto_exchange and left_days_value == 1 and exchange_points is not None:
            exchange_payload = {'points': exchange_points}
            exchange = requests.post(exchange_url,headers={'cookie': cookie ,'referer': referer,'origin':origin,'user-agent':useragent,'content-type':'application/json;charset=UTF-8'},data=json.dumps(exchange_payload))
            exchange_msg = None
            try:
                exchange_json = exchange.json()
                exchange_msg = exchange_json.get('message') or exchange_json.get('msg') or str(exchange_json)
            except Exception:
                exchange_msg = exchange.text or 'exchange failed'
            print(email+'----exchange '+exchange_label+'--'+exchange_msg)
            sendContent += email+'----exchange '+exchange_label+'--'+exchange_msg+'\n'
     #--------------------------------------------------------------------------------------------------------#   
    if sckey != "":
        requests.get('http://www.pushplus.plus/send?token=' + sckey + '&title=VPN签到成功'+'&content='+sendContent)


def main_handler(event, context):
  return start()

if __name__ == '__main__':
    start()
