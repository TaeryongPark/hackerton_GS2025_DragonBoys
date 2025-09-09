import os
import re
import requests
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone

URL = "https://obank.kbstar.com/quics?asfilecode=555555"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Referer": "https://obank.kbstar.com/quics?page=C101426&cc=b115961:b101160",
    "Origin": "https://obank.kbstar.com",
    "Content-Type": "application/x-www-form-urlencoded",
}

COOKIE_STRING = (
    "_LOG_VSTRIDNFIVAL=phlBpV0iRVaW07hwKDlyDA; ...생략...; delfino.recentModule=G3"
)

KST = timezone(timedelta(hours=9))


def get_last_business_day(asof: str = None) -> str:
    """
    오늘 기준 가장 최근 영업일(토/일 제외) 반환
    return: 'YYYYMMDD'
    """
    if asof:
        now_kst = datetime.strptime(asof, "%Y%m%d").replace(tzinfo=KST)
    else:
        now_kst = datetime.now(KST)

    while now_kst.weekday() >= 5:  # 토(5), 일(6) 제외
        now_kst -= timedelta(days=1)

    return now_kst.strftime("%Y%m%d")


def cookies_from_string(s: str):
    jar = requests.cookies.RequestsCookieJar()
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            jar.set(k.strip(), v.strip(), domain=".kbstar.com")
    return jar


def pick_filename(resp, default="download.pdf"):
    cd = resp.headers.get("Content-Disposition", "")
    m = re.search(r'filename\*?=([^;]+)', cd, flags=re.I)
    if m:
        val = m.group(1).strip().strip('"').strip("'")
        val = val.replace("UTF-8''", "")
        return unquote(val)
    return default


def download_kb_file(asof: str = None):
    """
    KB스타뱅킹에서 최신 영업일 PDF 다운로드
    input: asof = 'YYYYMMDD' (옵션, 기본=None → 오늘 기준 최신 영업일 자동계산)
    output: 같은 폴더 내 PDF 저장, 저장된 파일 경로 리턴
    """
    biz_date = get_last_business_day(asof)

    # 파일명 규칙: YYMMDD_Daily.pdf
    file_tag = biz_date[2:]  # '20250901' → '250901'
    file_name = f"{file_tag}_Daily.pdf"

    form_data = {
        "_DOMAIN_CODE": "bbs",
        "_SITE_CODE": "99/1081",
        "_SECURITY_CODE": "Y",
        "_FIXED_CODE": "Y",
        "_FILE_NAME": file_name,
        "_LANG_TYPE": "KOR",
    }

    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(cookies_from_string(COOKIE_STRING))

    with session.post(URL, data=form_data, stream=True) as r:
        r.raise_for_status()
        fname = pick_filename(r, default=file_name)
        if not os.path.splitext(fname)[1]:
            fname += ".pdf"

        with open(fname, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)

    abs_path = os.path.abspath(fname)
    return abs_path, fname


#
# if __name__ == "__main__":
#     saved = download_kb_file()  # 오늘 기준 최신 영업일 자동 계산
#     print("저장 완료:", saved)




#
# import os
# import re
# import requests
# from urllib.parse import unquote
#
#
# # 1) DevTools General 의 Request URL
# url = "https://obank.kbstar.com/quics?asfilecode=555555"
#
# # 2) DevTools Request Headers에서 복사해 채워넣기
# #    - 최소 필요: User-Agent, Referer, Origin, Content-Type
# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
#     "Referer": "https://obank.kbstar.com/quics?page=C101426&cc=b115961:b101160",
#     "Origin": "https://obank.kbstar.com",
#     "Content-Type": "application/x-www-form-urlencoded",
#     # Accept 등은 선택 사항
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
# }
#
# # 3) DevTools Request Headers 의 Cookie 전체 문자열을 그대로 붙여넣기
# #    예) "JSESSIONID=0000...; QSID=22A2...; WMONID=...; ..."
# cookie_string = (
#     "_LOG_VSTRIDNFIVAL=phlBpV0iRVaW07hwKDlyDA; LOG_NEWCONNDSTIC=Y; _xm_webid_1_=518576041; WMONID=zKyzImLgSGW; m_sid=%7C1756448115650; m_s_start=1756448115650; PplrCookies=%uD1B5%uC7A5%uC0AC%uBCF8%2C%uC774%uCCB4%uD655%uC778%uC99D%2C%uAE08%uC735%uAC70%uB798%uD655%uC778%uC11C%2C%uC774%uCCB4%uD55C%uB3C4%2COTP%2C%uACF5%uB3D9%uC778%uC99D%uC11C%2C%uC790%uB3D9%uC774%uCCB4%2C%uC794%uC561%uC99D%uBA85%uC11C%2C%uAD6D%uBBFC%uC8FC%uD0DD%uCC44%uAD8C%2C%uC608%uC57D%uC774%uCCB4; bwCkVal=20250829151515868; _m_uid=656eb213-cd4c-3f46-b0c2-0e9350d48ab4; _m_uidt=S; _m_uid_type=A; _M_CS[T]=1; _ga=GA1.2.1658108464.1756448116; _gid=GA1.2.985286802.1756448116; JSESSIONID=0000rKWhTNmvp62-yVwuxIfYhWI:BANK10502; QSID=15A2&&CkrJy5vtMxua3hiAIPKpEzH; _pk_id.SER0000001.ce94=5a4dd0bc71154997.1756448116.0.1756448685..; _ga_XTXVQQ6FS8=GS2.2.s1756448116$o1$g1$t1756448685$j60$l0$h0; _ga_PWF0L3XHV4=GS2.2.s1756448116$o1$g1$t1756448685$j60$l0$h0; _ga_TC7KKN0QLR=GS2.2.s1756448116$o1$g1$t1756448685$j60$l0$h0; delfino.recentModule=G3"
# )
#
# # 4) DevTools Payload 탭(Form Data)에서 모든 키=값 쌍을 그대로 dict에 채우기
# #    (예시는 자리표시자임. 실제 키/값으로 교체!)
# form_data = {
#     "_DOMAIN_CODE": "bbs",
#     "_SITE_CODE": "99/1081",
#     "_SECURITY_CODE": "Y",
#     "_FIXED_CODE": "Y",
#     "_FILE_NAME": "250828_Daily.pdf",
#     "_LANG_TYPE": "KOR",
# }
#
# # ---- 여기부터는 그대로 사용 ----
# def cookies_from_string(s: str):
#     jar = requests.cookies.RequestsCookieJar()
#     for part in s.split(";"):
#         part = part.strip()
#         if not part:
#             continue
#         if "=" in part:
#             k, v = part.split("=", 1)
#             jar.set(k.strip(), v.strip(), domain=".kbstar.com")
#     return jar
#
# def pick_filename(resp, default="download.pdf"):
#     # Content-Disposition: attachment; filename=250829_Daily.pdf;
#     cd = resp.headers.get("Content-Disposition", "")
#     m = re.search(r'filename\*?=([^;]+)', cd, flags=re.I)
#     if m:
#         val = m.group(1).strip().strip('"').strip("'")
#         # RFC5987 형식이나 URL 인코딩 대비
#         val = val.replace("UTF-8''", "")
#         return unquote(val)
#     return default
#
# session = requests.Session()
# session.headers.update(headers)
# session.cookies.update(cookies_from_string(cookie_string))
#
# # POST로 파일 요청
# with session.post(url, data=form_data, stream=True) as r:
#     r.raise_for_status()
#     fname = pick_filename(r) or "download.pdf"
#     # 혹시 확장자 없으면 기본 .pdf
#     if not os.path.splitext(fname)[1]:
#         fname += ".pdf"
#
#     # 바이너리로 저장 (chunked 응답 대응)
#     with open(fname, "wb") as f:
#         for chunk in r.iter_content(chunk_size=1024 * 64):
#             if chunk:
#                 f.write(chunk)
#
# print("저장 완료:", os.path.abspath(fname))