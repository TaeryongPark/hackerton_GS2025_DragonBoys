import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def get_last_business_days(n: int, today: str = None):
    """
    n개 만큼 최근 영업일 반환 (토/일 제외)
    today: 'YYYYMMDD' 형식 문자열 (None이면 현재 한국시간 기준 오늘)
    """
    if today is None:
        now_kst = datetime.now(KST)
    else:
        now_kst = datetime.strptime(today, "%Y%m%d").replace(tzinfo=KST)

    days = []
    current = now_kst
    while len(days) < n:
        if current.weekday() < 5:  # 0~4: 월~금
            days.append(current.strftime("%Y%m%d"))
        current -= timedelta(days=1)
    return days


def fetch_interest_rates(asof: str):
    """
    금리 데이터 조회
    asof: 'YYYYMMDD' 오늘 날짜 기준
    return: DataFrame (index=날짜, columns=[CD, CP, 국고채3년, 국고채5년])
    """
    target_date = get_last_business_days(6, asof)  # 최근 5영업일
    date_ir = target_date[1:]  # 가장 최근 ~ 5일 전

    item_list = ["CD(91일)", "CP(91일)", "국고채(3년)", "국고채(5년)"]
    data_dict = {item: [] for item in item_list}

    for i, item in enumerate(item_list):
        for d in date_ir:
            url = f"https://ecos.bok.or.kr/api/StatisticSearch/0N8X32N1NETE98HDLDMW/json/kr/1/100/817Y002/D/{d}/{d}"
            response = requests.get(url)
            rows = response.json()["StatisticSearch"]["row"]
            value = None
            for r in rows:
                if r.get("ITEM_NAME1") == item:
                    value = r.get("DATA_VALUE")
                    break
            data_dict[item].append(value)

    df_ir = pd.DataFrame(data_dict, index=date_ir)
    return df_ir


def fetch_exchange_rates(asof: str):
    """
    환율 데이터 조회
    asof: 'YYYYMMDD' 오늘 날짜 기준
    return: DataFrame (index=날짜, columns=[USD, CNY, JPY(100), EUR])
    """
    target_date = get_last_business_days(6, asof)  # 최근 6개
    # date_cu = target_date[:-1]  # 최근 5영업일 오늘 포함
    date_cu = target_date[1:]  # 최근 5영업일 오늘 제외

    item_list = ["원/미국달러(매매기준율)", "원/위안(매매기준율)", "원/일본엔(100엔)", "원/유로"]
    data_dict = {item: [] for item in item_list}

    for i, item in enumerate(item_list):
        for d in date_cu:
            url = f"https://ecos.bok.or.kr/api/StatisticSearch/0N8X32N1NETE98HDLDMW/json/kr/1/100/731Y001/D/{d}/{d}"
            response = requests.get(url)
            rows = response.json()["StatisticSearch"]["row"]
            value = None
            for r in rows:
                if r.get("ITEM_NAME1") == item:
                    value = r.get("DATA_VALUE")
                    break
            data_dict[item].append(value)

    df_fx = pd.DataFrame(data_dict, index=date_cu)
    return df_fx
