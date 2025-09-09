import os

from pathlib import Path
from google import genai

import re

API_KEY = "AIzaSyDLohLYlQSb3IdjQHighO-axW1Ix7grPGo"   # 직접 입력
MODEL_ID = "gemini-2.0-flash"                         # 빠르고 PDF 요약 적합

def summarize_pdf(file_name: str, prompt: str) -> str:
    """
    주어진 PDF 파일을 Gemini 모델로 요약
    :param file_name: PDF 파일명 (예: '250829_Daily.pdf')
    :param prompt: 프롬프트 텍스트 (예: '다음 PDF 문서를 한국어로 2줄로 요약해 주세요.')
    :return: 모델 출력 텍스트 (string)
    """
    pdf_path = Path(file_name)

    # ===== Client 생성 =====
    client = genai.Client(api_key=API_KEY)

    # ===== PDF 확인 =====
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path.resolve()}")

    # ===== 1) PDF 업로드 =====
    uploaded = client.files.upload(
        file=pdf_path,
        config={"mime_type": "application/pdf", "display_name": pdf_path.name},
    )

    # ===== 2) 모델 호출 =====
    resp = client.models.generate_content(
        model=MODEL_ID,
        contents=[uploaded, "\n\n", prompt],
        config={
            "temperature": 0.2,
            "max_output_tokens": 1024,
            # "response_mime_type": "text/plain"
        },
    )

    return resp.text.strip() if getattr(resp, "text", None) else str(resp)


# if __name__ == "__main__":
#     # main에서 input 값 넣기
#     file_name = "250829_Daily.pdf"
#     user_prompt = "다음 PDF 문서를 한국어로 2줄로 요약해 주세요."
#
#     result = summarize_pdf(file_name, user_prompt)
#     print("\n===== 요약 결과 =====\n")
#     print(result)



# def summarize_pdf():
#     # ===== 설정 =====
#     API_KEY = "AIzaSyDLohLYlQSb3IdjQHighO-axW1Ix7grPGo"   # 직접 입력
#     MODEL_ID = "gemini-2.0-flash"             # 빠르고 PDF 요약 적합
#     PDF_PATH = Path("250829_Daily.pdf")              # 같은 폴더에 생성된 PDF
#
#     # ===== Client 생성 =====
#     client = genai.Client(api_key=API_KEY)
#
#     # ===== PDF 확인 =====
#     if not PDF_PATH.exists():
#         raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {PDF_PATH.resolve()}")
#
#     # ===== 1) PDF 업로드 =====
#     uploaded = client.files.upload(
#         file=PDF_PATH,
#         config={"mime_type": "application/pdf", "display_name": PDF_PATH.name},
#     )
#
#     # ===== 2) 프롬프트 =====
#     prompt = (
#         "다음 PDF 문서를 한국어로 2줄로 요약해 주세요.\n"
#     )
#
#     # ===== 3) 모델 호출 =====
#     resp = client.models.generate_content(
#         model=MODEL_ID,
#         contents=[uploaded, "\n\n", prompt],
#         config={
#             "temperature": 0.2,        # 요약은 낮게
#             "max_output_tokens": 1024  # 결과 길이
#         },
#     )
#
#     # ===== 4) 결과 출력 =====
#     print("\n===== 요약 결과 =====\n")
#     print(resp.text.strip() if getattr(resp, "text", None) else resp)




if __name__ == "__main__":
    summarize_pdf()
