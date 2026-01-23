import requests,json,os

def _iter_base_urls():
    env = os.environ.get("GLADOS_BASE_URLS") or os.environ.get("GLADOS_BASE_URL") or ""
    if env:
        parts = [p.strip() for p in env.replace(";", ",").split(",")]
    else:
        parts = ["https://glados.cloud", "https://glados.rocks"]
    seen = set()
    for p in parts:
        if not p:
            continue
        p = p.rstrip("/")
        if p not in seen:
            seen.add(p)
            yield p

def _resolve_base_url(cookie, useragent):
    for base_url in _iter_base_urls():
        url2 = f"{base_url}/api/user/status"
        referer = f"{base_url}/console/checkin"
        origin = base_url
        try:
            state = requests.get(
                url2,
                headers={
                    'cookie': cookie,
                    'referer': referer,
                    'origin': origin,
                    'user-agent': useragent,
                },
            )
        except Exception:
            continue
        try:
            state_json = state.json()
        except Exception:
            continue
        data = state_json.get('data') or {}
        if data.get('leftDays') is not None:
            return base_url
        msg = (state_json.get('message') or state_json.get('msg') or '').lower()
        if "please checkin via" in msg:
            continue
        return base_url
    return "https://glados.cloud"

def _extract_checkin_base_url(msg):
    if not msg:
        return None
    lower = msg.lower()
    idx = lower.find("http")
    if idx == -1:
        return None
    url = msg[idx:].strip().split()[0]
    url = url.rstrip(" .，,。-–—")
    if url.startswith("http://") or url.startswith("https://"):
        return url.rstrip("/")
    return None

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
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    base_url = _resolve_base_url(cookies[0], useragent)
    url= f"{base_url}/api/user/checkin"
    url2= f"{base_url}/api/user/status"
    exchange_url = f"{base_url}/api/user/points/exchange"
    referer = f"{base_url}/console/checkin"
    origin = base_url
    payload={
        'token': 'glados.cloud'
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
            mess = checkin.json().get('message') or checkin.json().get('msg')
            if mess and "please checkin via" in mess.lower():
                new_base = _extract_checkin_base_url(mess)
                if new_base and new_base != base_url:
                    base_url = new_base
                    url= f"{base_url}/api/user/checkin"
                    url2= f"{base_url}/api/user/status"
                    exchange_url = f"{base_url}/api/user/points/exchange"
                    referer = f"{base_url}/console/checkin"
                    origin = base_url
                    checkin = requests.post(url,headers={'cookie': cookie ,'referer': referer,'origin':origin,'user-agent':useragent,'content-type':'application/json;charset=UTF-8'},data=json.dumps(payload))
                    mess = checkin.json().get('message') or checkin.json().get('msg')
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
