#!/usr/bin/env python3
import json, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'data' / 'status.json'
HEADERS = {'User-Agent': 'HokkaidoTripGuide/1.0 (+GitHub Actions)'}

def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode('utf-8'))

def get_text(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode('utf-8', 'replace')

def zh(s):
    if not s: return ''
    pairs = [
      ('石狩、空知、後志地方では、急な強い雨や落雷、濃霧による視程障害に注意してください。','石狩、空知、後志地區請注意突發強降雨、雷擊，以及濃霧造成的能見度障礙。'),
      ('雨のち曇り','雨後多雲'),('雨のち晴れ','雨後轉晴'),('曇り時々雪','多雲時有雪'),('曇り時々雨','多雲時有雨'),
      ('晴れ時々雪','晴時有雪'),('晴れ時々雨','晴時有雨'),('雪のち曇り','雪後多雲'),('雪のち晴れ','雪後轉晴'),
      ('雷を伴う','伴隨雷雨'),('雪を伴う','伴隨降雪'),('暴風雪','暴風雪'),('大雪','大雪'),('吹雪','暴風雪'),
      ('なだれ','雪崩'),('着雪','積雪附著'),('低気圧','低氣壓'),('寒気','冷氣團'),('降水確率','降水機率'),
      ('最高気温','最高氣溫'),('最低気温','最低氣溫'),('強風','強風'),('風雪','風雪'),('波浪','海浪'),
      ('後志地方','後志地區'),('石狩地方','石狩地區'),('空知地方','空知地區'),('渡島地方','渡島地區'),
      ('檜山地方','檜山地區'),('上川地方','上川地區'),('胆振地方','膽振地區'),('日高地方','日高地區'),
      ('急な強い雨','突發強降雨'),('落雷','雷擊'),('視程障害','能見度障礙'),('注意してください','請注意'),
      ('では、','，'),('晴れ','晴天'),('くもり','多雲'),('曇り','多雲'),('雨か雪','雨或雪'),('雪か雨','雪或雨'),
      ('一時','短暫'),('時々','有時'),('所により','局部地區'),('夜遅く','深夜'),('夕方','傍晚'),('昼過ぎ','午後'),
      ('朝晩','早晚'),('やや強く','稍強'),('強い','強烈'),('弱い','較弱'),('北西の風','西北風'),('北東の風','東北風'),
      ('南西の風','西南風'),('南東の風','東南風'),('北の風','北風'),('南の風','南風'),('西の風','西風'),('東の風','東風'),
      ('発表','發布'),('継続','持續'),('解除','解除')]
    for a,b in pairs: s=s.replace(a,b)
    return s

def jma():
    warning = get_json('https://www.jma.go.jp/bosai/warning/data/warning/016000.json')
    regions = [('札幌／石狩','016000'),('函館／渡島','017000'),('旭川／上川','012000'),('登別／膽振','015000')]
    forecasts=[]
    for name,code in regions:
        d=get_json(f'https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json')
        ts=(d[0] if d else {}).get('timeSeries',[])
        main=ts[0] if ts else {}
        area=(main.get('areas') or [{}])[0]
        days=(main.get('timeDefines') or [])[:3]
        weather=(area.get('weathers') or [])[:3]
        forecasts.append({'region':name,'reportDatetime':(d[0] if d else {}).get('reportDatetime'),'days':[{'date':x[:10],'weather':zh(weather[i] if i<len(weather) else '')} for i,x in enumerate(days)]})
    return {'warning':{'reportDatetime':warning.get('reportDatetime'),'headline':zh(warning.get('headlineText',''))},'forecast':forecasts}

def source_probe(name,url,keywords):
    try:
        text=get_text(url)
        plain=re.sub(r'<[^>]+>',' ',text)
        plain=re.sub(r'\s+',' ',plain)
        hits=[k for k in keywords if k.lower() in plain.lower()]
        return {'name':name,'url':url,'status':'reachable','message':'官方頁面可連線；即時狀態請以頁面顯示為準。','matchedKeywords':hits[:8]}
    except Exception as e:
        return {'name':name,'url':url,'status':'unavailable','message':'官方資料暫時無法讀取：'+type(e).__name__}

def main():
    now=datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
    try: weather=jma(); jma_status='ok'
    except Exception as e: weather={'warning':{'headline':'JMA 資料暫時無法取得'},'forecast':[]}; jma_status='unavailable'
    traffic=[
      source_probe('北海道開發局道路通行止め','https://www.hkd.mlit.go.jp/sp/douro_keikaku/e9fjd60000000p9q.html',['通行止め','道路情報']),
      source_probe('北海道廳道路限制','https://www.pref.hokkaido.lg.jp/kn/sbs/dk/doro_iji_04_jizenkisei.html',['通行規制','現在']),
      source_probe('JARTIC 道路交通資訊','https://www.jartic.or.jp/',['北海道','道路交通情報']),
      source_probe('JR 北海道運行資訊','https://www3.jrhokkaido.co.jp/webunkou/index_en.html',['Sapporo area','Cancelled','delayed']),
      source_probe('新千歲機場','https://www.hokkaido-airports.com/en/new-chitose/',['Arriving','Departing','Transportation'])]
    data={'schemaVersion':1,'generatedAt':now,'refreshIntervalMinutes':10,'jmaStatus':jma_status,'weather':weather,'traffic':traffic,'disclaimer':'交通官方網站多為動態頁；本檔只標示來源連線與抓取時間，不會在無法確認時猜測道路或列車狀態。'}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
