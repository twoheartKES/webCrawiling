import requests
import time
import json
import csv
from urllib.parse import urlencode
import io

BASE_URL = "https://dportal.kdca.go.kr"
MAIN_URL = f"{BASE_URL}/pot/is/rginEDW.do"

# 실제 확인된 정확한 URL들

SIGNGU_URL = f"{BASE_URL}/pot/is/selectAreaSignguCdListEDWAjax.do" # 시군구코드를 가져옴
STATS_URL = f"{BASE_URL}/pot/is/bassAreaStatsContentEDW.do" # 페이징 구성?
DATA_URL = f"{BASE_URL}/pot/is/selectBassAreaStatsListEDWAjax.do" # 실제데이터 가져옴

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

def json_to_csv(data_list, filename):
    """JSON 데이터를 UTF-8 CSV로 변환 (한글 깨짐 완전 해결)"""
    """JSON 데이터를 UTF-8 CSV로 변환 (컬럼 숫자 순서 정렬)"""
    if not data_list:
        print(f"⚠️ 데이터 없음: {filename}")
        return False
    
 # 모든 컬럼명 수집
    all_columns = set()
    for row in data_list:
        all_columns.update(row.keys())
    
    # COLUMN 숫자 순서대로 정렬 (자연 정렬)
    def natural_sort_key(col):
        """COLUMN1, COLUMN2, ..., COLUMN10 순서로 정렬"""
        if col.startswith('COLUMN'):
            try:
                return int(col.replace('COLUMN', ''))
            except:
                return 999999  # 숫자 아닌 경우 맨 뒤
        return 999999
    
    columns = sorted(list(all_columns), key=natural_sort_key)
    
    # UTF-8 BOM 추가 (Excel에서 한글 정상 표시)
    bom = '\ufeff'
    
    with io.open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data_list)
    
    print(f"✅ UTF-8 BOM CSV 저장: {filename} ({len(data_list)}행)")
    return True    
def get_all_signgu_list(session):
    """경기 모든 시군구 리스트 자동 가져오기"""
    print("🔍 경기 시군구 리스트 자동 조회...")
    signgu_payload = {"areaCtprvnCd": "08"}
    signgu_resp = session.post(
        SIGNGU_URL,
        data=signgu_payload,
        headers=get_realistic_headers(MAIN_URL),
        timeout=10
    )
    
    print(f"   시군구 응답코드: {signgu_resp.status_code}")
    print("signgu_resp::::::", signgu_resp.content[:500], "...")  # 처음 500자만
    
    if signgu_resp.status_code == 200:
        try:
            signgu_json = signgu_resp.json()
            signgu_list = signgu_json.get('value', [])
            print(f"✅ 경기 시군구 {len(signgu_list)}개 조회 완료!")
            
            # 코드:이름 딕셔너리 생성
            regions = {}
            for item in signgu_list:
                code = item['areaSignguCd']
                name = item['signguNm'].replace(' ', '_')  # 파일명용 공백 제거
                regions[code] = name
            return regions
        except:
            print("❌ 시군구 JSON 파싱 실패")
            return {}
    return {}

def download_for_region(session, signgu_cd, signgu_name, year="2025"):
    """특정 시군구 데이터 다운로드"""
    print(f"\n📥 {signgu_name} ({signgu_cd}) 다운로드...")
    
    # 3. 통계 내용 요청
    stats_payload = {
        "frmNm": "areaDissMonthWeekFrm",
        "areaCtprvnCdArr": "",
        "areaSignguCdArr": "",
        "icdgrpCdArr": "01,02,03",
        "icdCdArr": "A0013,NB0005,NB0006,NB0007,NB0017,NC0005,NC0006,NC0007,NC0010,NC0014,NC0018,NC0021,NC0025,NC0026",  # 실제 사용된 코드
        "startDt": year,
        "dateType": "week",
        "icdgrpCd": ["01", "02", "03"], #감염병 등급1~3등급급
        "icdCd": ["NB0005","NB0006","NB0007","NB0017","NC0005","NC0006","NC0007", "NC0010", "NC0014", "NC0018","NC0021","NC0025","NC0026"], # 질병코드드
        "areaCtprvnCd": "08", #경기도 시군구코드 서울은 "01"
        "areaSignguCd": signgu_cd,
        "patntType": "1",  # 실제 사용값
        "areaType": "1"
    }
    session.post(STATS_URL, data=stats_payload, headers=get_realistic_headers(MAIN_URL), timeout=10)
    time.sleep(0.7)
    
    # 4. 실제 데이터 요청 (selectBassAreaStatsListEDWAjax.do)
    print("4. 실제 데이터 요청...")
    data_payload = {
        "frmNm": "areaDissMonthWeekFrm",
        "areaCtprvnCdArr": "",
        "areaSignguCdArr": "",
        "icdgrpCdArr": "01,02,03",
        "icdCdArr": "A0013,NB0005,NB0006,NB0007,NB0017,NC0005,NC0006,NC0007,NC0010,NC0014,NC0018,NC0021,NC0025,NC0026",  # 실제 사용된 코드
        "startDt": year,
        "dateType": "week",
        "icdgrpCd": ["01", "02", "03"], #감염병 등급1~3등급급
        "icdCd": ["NB0005","NB0006","NB0007","NB0017","NC0005","NC0006","NC0007", "NC0010", "NC0014", "NC0018","NC0021","NC0025","NC0026"], # 질병코드드
        "areaCtprvnCd": "08", #경기도 시군구코드 서울은 "01"
        "areaSignguCd": signgu_cd,
        "patntType": "1",  # 실제 사용값
        "areaType": "1"
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
            data_list = data_json.get('value', {}).get('data', [])
            
            filename = f"kdca_{year}_week_경기_{signgu_name}_{signgu_cd}.csv"
            if json_to_csv(data_list, filename):
                print(f"✅ 저장: {filename} ({len(data_list)}행)")
                return True
        except Exception as e:
            print(f"❌ 파싱오류: {e}")
    print(f"❌ 실패: {signgu_cd}")
    return False

if __name__ == "__main__":
    session = requests.Session()
    
    # 1. 메인 페이지 방문
    print("🌐 메인 페이지 접속...")
    session.get(MAIN_URL, headers=get_realistic_headers(), timeout=10)
    time.sleep(1)
    
    # 2. 모든 시군구 리스트 자동 조회
    gyenggi_regions = get_all_signgu_list(session)
    
    if not gyenggi_regions:
        print("❌ 시군구 리스트 조회 실패!")
        exit()
    
    # TEST_CASES는 그대로 유지 (수동 테스트용)
    TEST_CASES = [
        ("075", "2025"),  # 가평군 2025
        ("076", "2025")   # 고양시 덕양구 2025
    ]
    
    success_count = 0
    
    # 3. TEST_CASES 먼저 실행
    """ print("\n🎯 TEST_CASES 실행...")
    for signgu_cd, year in TEST_CASES:
        if signgu_cd in gyenggi_regions:
            if download_for_region(session, signgu_cd, gyenggi_regions[signgu_cd], year):
                success_count += 1
        time.sleep(60) #ip보호
    
    print(f"\n✅ TEST 완료: {success_count}/{len(TEST_CASES)} 성공") """
    
    # 4. 전체 자동 실행 원하면 아래 주석 해제
    print("\n🚀 전체 경기 40개 자동 다운로드 시작...")
    for signgu_cd, signgu_name in gyenggi_regions.items():
        download_for_region(session, signgu_cd, signgu_name, "2025")
        time.sleep(60) #ip보호