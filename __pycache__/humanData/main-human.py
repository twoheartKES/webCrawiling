import requests
import time
import json
from urllib.parse import urlencode

BASE_URL = "https://dportal.kdca.go.kr"
MAIN_URL = f"{BASE_URL}/pot/is/rginEDW.do"

# 실제 확인된 정확한 URL들
SIGNGU_URL = f"{BASE_URL}/pot/is/selectAreaSignguCdListEDWAjax.do"
STATS_URL = f"{BASE_URL}/pot/is/bassAreaStatsContentEDW.do" 
DATA_URL = f"{BASE_URL}/pot/is/selectBassAreaStatsListEDWAjax.do"

def get_realistic_headers(referer=None):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": BASE_URL,
    }
    if referer:
        headers["Referer"] = referer
    return headers

def download_for_region(signgu_cd="075", year="2025"):
    session = requests.Session()
    
    print(f"\n=== {signgu_cd} ({year}) 다운로드 시작 ===")
    
    # 1. 메인 페이지 방문 (쿠키 획득)
    print("1. 메인 페이지...")
    session.get(MAIN_URL, headers=get_realistic_headers(), timeout=10)
    time.sleep(1)
    
    # 2. 시군구 리스트 요청 (경기 선택)
    print("2. 경기 시군구 리스트...")
    signgu_payload = {"areaCtprvnCd": "08"}
    signgu_resp = session.post(
        SIGNGU_URL,
        data=signgu_payload,
        headers=get_realistic_headers(MAIN_URL),
        timeout=10
    )
    print(f"   시군구 응답: {signgu_resp.status_code}")
    time.sleep(0.5)
    
    # 3. 통계 내용 요청 (bassAreaStatsContentEDW.do)
    print("3. 통계 내용 요청...")
    stats_payload = {
        "frmNm": "areaDissMonthWeekFrm",
        "areaCtprvnCdArr": "",
        "areaSignguCdArr": "",
        "icdgrpCdArr": "01,02,03",
        "icdCdArr": "NB0005,NB0006,NB0007",  # 실제 사용된 코드
        "startDt": year,
        "dateType": "week",
        "icdgrpCd": ["01", "02", "03"],
        "icdCd": ["NB0005", "NB0006", "NB0007"],
        "areaCtprvnCd": "08",
        "areaSignguCd": signgu_cd,
        "patntType": "1",  # 실제 사용값
        "areaType": "1"
    }
    stats_resp = session.post(
        STATS_URL,
        data=stats_payload,
        headers=get_realistic_headers(MAIN_URL),
        timeout=10
    )
    print(f"   통계 내용: {stats_resp.status_code}")
    time.sleep(0.5)
    
    # 4. 실제 데이터 요청 (selectBassAreaStatsListEDWAjax.do)
    print("4. 실제 데이터 요청...")
    data_payload = {
        "icdgrpCdArr": "01,02,03",
        "icdCdArr": "NB0005,NB0006,NB0007",
        "frmNm": "areaDissMonthWeekFrm",
        "dateType": "week",
        "areaCtprvnCd": "08",
        "icdgrpCd": "01",
        "patntType": "1",
        "areaSignguCdArr": "",
        "areaType": "1",
        "startDt": year,
        "areaSignguCd": signgu_cd,
        "areaCtprvnCdArr": "",
        "icdCd": "NB0005"
    }
    data_resp = session.post(
        DATA_URL,
        data=data_payload,
        headers=get_realistic_headers(MAIN_URL),
        timeout=10
    )
    print(f"   데이터 응답: {data_resp.status_code}")
    
    if data_resp.status_code == 200:
        try:
            data_json = data_resp.json()
            print(f"   데이터 확인: {len(data_json.get('value', {}).get('data', []))} 행")
            
            # CSV 저장 (JSON → CSV 변환)
            filename = f"kdca_{year}_week_경기_{signgu_cd}.csv"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("통계데이터\n")  # 헤더
                if 'value' in data_json and 'data' in data_json['value']:
                    for row in data_json['value']['data']:
                        f.write(json.dumps(row) + "\n")
            print(f"✅ 저장 완료: {filename}")
            return True
        except:
            print("❌ JSON 파싱 실패")
            return False
    else:
        print(f"❌ 데이터 요청 실패: {data_resp.status_code}")
        return False

if __name__ == "__main__":
    # 2개만 테스트
    TEST_CASES = [
        ("075", "2025"),  # 가평군 2025
        ("076", "2024")   # 고양시 덕양구 2024
    ]
    
    for signgu_cd, year in TEST_CASES:
        success = download_for_region(signgu_cd, year)
        if success:
            print("✅ 성공!")
        else:
            print("❌ 실패")
        time.sleep(5)  # IP 보호
