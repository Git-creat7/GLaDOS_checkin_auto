import requests,json,os

def _iter_base_urls():
    env = os.environ.get("GLADOS_BASE_URLS") or os.environ.get("GLADOS_BASE_URL") or ""
    if env:
        parts = [p.strip() for p in env.replace(";", ",").split(",")]
    else:
        parts = ["https://glados.cloud"]
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

def _extract_points(payload):
    def _coerce(val):
        try:
            return int(float(val))
        except Exception:
            return None

    def _walk(obj):
        if isinstance(obj, dict):
            for key in (
                "points",
                "point",
                "score",
                "balance",
                "totalPoints",
                "totalPoint",
                "total_points",
                "total",
                "leftPoints",
                "left_points",
                "remainPoints",
                "remain_points",
                "availablePoints",
                "available_points",
            ):
                if key in obj and obj[key] is not None:
                    return obj[key]
            if "data" in obj:
                val = _walk(obj["data"])
                if val is not None:
                    return val
            for key in ("list", "items", "records"):
                if key in obj:
                    val = _walk(obj[key])
                    if val is not None:
                        return val
        elif isinstance(obj, list):
            for item in obj:
                val = _walk(item)
                if val is not None:
                    return val
        return None

    raw = _walk(payload)
    if raw is None:
        return None
    return _coerce(raw)

def _fetch_points(base_url, headers):
    for path in ("/api/user/points", "/api/user/points/summary", "/api/user/points/balance"):
        try:
            resp = requests.get(f"{base_url}{path}", headers=headers)
        except Exception:
            continue
        try:
            payload = resp.json()
        except Exception:
            continue
        points = _extract_points(payload)
        if points is not None:
            return points
    return None

def _iter_exchange_urls(base_url):
    env = os.environ.get("GLADOS_EXCHANGE_URLS") or os.environ.get("GLADOS_EXCHANGE_URL") or ""
    if env:
        parts = [p.strip() for p in env.replace(";", ",").split(",")]
        for p in parts:
            if not p:
                continue
            if p.startswith("http://") or p.startswith("https://"):
                yield p.rstrip("/")
            else:
                yield f"{base_url}{p if p.startswith('/') else '/' + p}"
        return
    yield f"{base_url}/api/user/points/exchange"
    yield f"{base_url}/api/user/points/convert"
    yield f"{base_url}/api/user/points/redeem"
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
        headers = {'cookie': cookie ,'referer': referer,'origin':origin,'user-agent':useragent}
        checkin = requests.post(url,headers={**headers,'content-type':'application/json;charset=UTF-8'},data=json.dumps(payload))
        state =  requests.get(url2,headers=headers)
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
        if left_days is None:
            msg = state_json.get('message') or state_json.get('msg') or str(state_json)
            print(email + '----状态获取失败--' + msg)
            if sckey != "":
                requests.get('http://www.pushplus.plus/send?token=' + sckey + '&content=' + email + '状态获取失败，可能cookie已失效')
            continue

        time = str(left_days).split('.')[0]
        left_days_value = None
        try:
            left_days_value = int(float(left_days))
        except Exception:
            left_days_value = None

        mess = None
        try:
            checkin_json = checkin.json()
            mess = checkin_json.get('message') or checkin_json.get('msg')
        except Exception:
            mess = None
        if mess and "please checkin via" in mess.lower():
            new_base = _extract_checkin_base_url(mess)
            if new_base and new_base != base_url:
                base_url = new_base
                url= f"{base_url}/api/user/checkin"
                url2= f"{base_url}/api/user/status"
                exchange_url = f"{base_url}/api/user/points/exchange"
                referer = f"{base_url}/console/checkin"
                origin = base_url
                headers = {'cookie': cookie ,'referer': referer,'origin':origin,'user-agent':useragent}
                checkin = requests.post(url,headers={**headers,'content-type':'application/json;charset=UTF-8'},data=json.dumps(payload))
                try:
                    checkin_json = checkin.json()
                    mess = checkin_json.get('message') or checkin_json.get('msg')
                except Exception:
                    pass

        if mess:
            print(email+'----结果--'+mess+'----剩余('+time+')天')  # 日志输出
            sendContent += email+'----'+mess+'----剩余('+time+')天\n'
        else:
            requests.get('http://www.pushplus.plus/send?token=' + sckey + '&content='+email+'cookie已失效')
            print(email + '----cookie已失效')  # 日志输出

        points_value = _extract_points(data)
        if points_value is None:
            points_value = _extract_points(state_json)
        if points_value is None:
            points_value = _fetch_points(base_url, headers)

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
        print(f"{email}----当前总积分: {points_value}----可兑换额度: {exchange_points}")
        if auto_exchange and left_days_value == 1 and exchange_points is not None:
            exchange_payload = {'points': exchange_points}
            exchange_msg = None
            exchange_status = None
            exchange_text = None
            for candidate_url in _iter_exchange_urls(base_url):
                exchange = requests.post(candidate_url,headers={**headers,'content-type':'application/json;charset=UTF-8'},data=json.dumps(exchange_payload))
                exchange_status = exchange.status_code
                try:
                    exchange_json = exchange.json()
                    exchange_msg = exchange_json.get('message') or exchange_json.get('msg') or str(exchange_json)
                except Exception:
                    exchange_text = exchange.text
                    exchange_msg = exchange_text or 'exchange failed'
                if exchange_msg and "not found" in str(exchange_msg).lower():
                    continue
                if exchange_status == 404:
                    continue
                break
            if exchange_msg and "not found" in str(exchange_msg).lower():
                detail = f"status={exchange_status}"
                if exchange_text:
                    detail += f", body={exchange_text[:160]}"
                exchange_msg = f"{exchange_msg} ({detail})"
            print(email+'----exchange '+exchange_label+'--'+exchange_msg)
            sendContent += email+'----exchange '+exchange_label+'--'+exchange_msg+'\n'
     #--------------------------------------------------------------------------------------------------------#   
    if sckey != "":
         requests.get('http://www.pushplus.plus/send?token=' + sckey + '&title='+email+'签到成功'+'&content='+sendContent)


