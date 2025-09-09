
import os
import requests
from datetime import datetime, timedelta, timezone

# ---- KST 타임존 ----
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


def _to_yymmdd(yyyymmdd: str) -> str:
    """'YYYYMMDD' -> 'YYMMDD'"""
    return yyyymmdd[2:]


def _prev_business_day(yyyymmdd: str) -> str:
    """하루씩 이전 날짜로 내려가며 토/일은 건너뛰어 'YYYYMMDD' 반환"""
    d = datetime.strptime(yyyymmdd, "%Y%m%d")
    while True:
        d -= timedelta(days=1)
        if d.weekday() < 5:  # 월(0)~금(4)
            return d.strftime("%Y%m%d")


def download_hana_market_daily(asof: str | None = None,
                               save_dir: str = ".",
                               try_back_n: int = 5,
                               timeout: int = 15) -> tuple[str, str]:
    """
    하나은행 'Hana Market Daily' PDF 자동 다운로드
    """
    os.makedirs(save_dir, exist_ok=True)

    # 1) 기준일(영업일) 산출
    ymd = get_last_business_day(asof)

    # 2) 뒤로 try_back_n일 범위에서 탐색
    for _ in range(try_back_n + 1):
        ymd_try = ymd
        yymmdd = _to_yymmdd(ymd_try)

        # URL 후보 리스트
        url_candidates = [
            f"https://biz.kebhana.com/cont/hanafx/file/marketdaily{yymmdd}.pdf",
            f"https://biz.kebhana.com/cont/hanafx/file/Daily{yymmdd}.pdf",
        ]

        filename = f"hana_market_daily_{ymd_try}.pdf"
        save_path = os.path.join(save_dir, filename)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Referer": "https://biz.kebhana.com/",
        }

        # 각 URL을 순차적으로 시도
        for url in url_candidates:
            try:
                resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
                if resp.status_code == 200 and int(resp.headers.get("Content-Length", "1")) > 0:
                    with open(save_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=1024 * 64):
                            if chunk:
                                f.write(chunk)
                    print(f"✅ 다운로드 완료: {filename} ({url})")
                    return save_path, filename
                else:
                    print(f"❌ 없음({resp.status_code}): {url}")
            except requests.RequestException as e:
                print(f"⚠️ 요청 실패: {url}  -> {e}")

        # 다음 시도: 전 영업일
        ymd = _prev_business_day(ymd)

    raise FileNotFoundError(
        f"최근 {try_back_n}일 내에서 하나은행 Market Daily 파일을 찾지 못했습니다."
    )



# def download_hana_market_daily(asof: str | None = None,
#                                save_dir: str = ".",
#                                try_back_n: int = 5,
#                                timeout: int = 15) -> tuple[str, str]:
#     """
#     하나은행 'Hana Market Daily' PDF 자동 다운로드
#
#     Parameters
#     ----------
#     asof : str | None
#         기준일 'YYYYMMDD' (None이면 오늘 기준 최근 영업일)
#     save_dir : str
#         저장 폴더
#     try_back_n : int
#         기준일에서 최대 며칠 이전까지(영업일 단위 아님, 캘린더 일수) 거슬러 가며 시도
#     timeout : int
#         요청 타임아웃(초)
#
#     Returns
#     -------
#     (save_path, filename)
#         파일 저장 전체 경로와 파일명
#
#     Raises
#     ------
#     FileNotFoundError
#         지정된 기간 내에서 파일을 찾지 못한 경우
#     """
#     os.makedirs(save_dir, exist_ok=True)
#
#     # 1) 기준일(영업일) 산출
#     ymd = get_last_business_day(asof)
#
#     # 2) 뒤로 try_back_n일 범위에서 탐색
#     for _ in range(try_back_n + 1):
#         ymd_try = ymd
#         yymmdd = _to_yymmdd(ymd_try)
#
#         url = f"https://biz.kebhana.com/cont/hanafx/file/marketdaily{yymmdd}.pdf"
#         # url = f"biz.kebhana.com/cont/hanafx/file/Daily{yymmdd}.pdf"
#
#         filename = f"hana_market_daily_{ymd_try}.pdf"
#         save_path = os.path.join(save_dir, filename)
#
#         headers = {
#             "User-Agent": (
#                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                 "AppleWebKit/537.36 (KHTML, like Gecko) "
#                 "Chrome/124.0 Safari/537.36"
#             ),
#             "Referer": "https://biz.kebhana.com/",
#         }
#
#         try:
#             resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
#             if resp.status_code == 200 and int(resp.headers.get("Content-Length", "1")) > 0:
#                 with open(save_path, "wb") as f:
#                     for chunk in resp.iter_content(chunk_size=1024 * 64):
#                         if chunk:
#                             f.write(chunk)
#                 print(f"✅ 다운로드 완료: {filename} ({url})")
#                 return save_path, filename
#             else:
#                 print(f"❌ 없음({resp.status_code}): {url}")
#         except requests.RequestException as e:
#             print(f"⚠️ 요청 실패: {url}  -> {e}")
#
#         # 다음 시도: 전 영업일
#         ymd = _prev_business_day(ymd)
#
#     raise FileNotFoundError(
#         f"최근 {try_back_n}일 내에서 하나은행 Market Daily 파일을 찾지 못했습니다."
#     )


# # ---------------- 사용 예시 ----------------
# if __name__ == "__main__":
#     # asof=None 이면 "오늘 기준 최근 영업일"부터 탐색
#     # 필요하면 asof="20250908" 처럼 특정 기준일을 직접 넣어도 됩니다.
#     path, fname = download_hana_market_daily(asof=None, save_dir="./reports", try_back_n=7)
#     print("저장 경로:", path)
