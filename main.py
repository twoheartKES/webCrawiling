import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
from urllib.parse import urljoin, parse_qs, urlparse

# 세션 생성 (쿠키 및 상태 유지)
session = requests.Session()

# 더 사실적인 헤더 설정 (봇 차단 방지)
def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

def get_ajax_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.foodsafetykorea.go.kr/portal/healthyfoodlife/searchHomeHF.do',
        'Origin': 'https://www.foodsafetykorea.go.kr',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

BASE_URL = "https://www.foodsafetykorea.go.kr"
AJAX_SEARCH_URL = f"{BASE_URL}/portal/healthyfoodlife/searchHomeHFProc.do"
DETAIL_URL = f"{BASE_URL}/portal/healthyfoodlife/searchHomeHFDetail.do"

def search_omega3_products(page_no=1, search_term="오메가3", show_cnt=50):
    """오메가3 건강기능식품 검색"""
    # 페이지 인덱스 계산 (1부터 시작)
    start_idx = (page_no - 1) * show_cnt + 1
    
    list_params = {
        "menu_no": "2823",
        "menu_grp": "MENU_NEW01", 
        "menuNm": "건강기능식품 검색",
        "copyUrl": "https://www.foodsafetykorea.go.kr:443/portal/healthyfoodlife/searchHomeHF.do?menu_grp=MENU_NEW01&menu_no=2823",
        "mberId": "",
        "mberNo": "",
        "favorListCnt": "0",
        "search_code": "05",  # 05: 제품명 또는 업소명
        "search_word": search_term,
        "show_cnt": str(show_cnt),  # 페이지당 표시 개수
        "start_idx": str(start_idx)  # 시작 인덱스 (1부터 시작!)
    }
    
    try:
        print(f"[페이지 {page_no}] 브라우저 동작 시뮬레이션 시작...")
        
        # 1단계: 메인 페이지 방문 (쿠키 및 세션 설정)
        if page_no == 1:  # 첫 페이지에서만 초기화
            session.get(BASE_URL, headers=get_headers(), timeout=30)
            time.sleep(0.5)
            search_page_url = f"{BASE_URL}/portal/healthyfoodlife/searchHomeHF.do"
            session.get(search_page_url, headers=get_headers(), timeout=30)
            time.sleep(1)
        
        # AJAX 검색 요청
        response = session.post(AJAX_SEARCH_URL, data=list_params, headers=get_ajax_headers(), timeout=30)
        response.encoding = "utf-8"
        
        print(f"[페이지 {page_no}] 응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[페이지 {page_no}] HTTP 오류: {response.status_code}")
            return None
        
        # JSON 파싱 시도
        try:
            json_data = response.json()
            print(f"[페이지 {page_no}] JSON 파싱 성공: {len(json_data)}개 제품")
            return json_data
        except ValueError as json_error:
            print(f"[페이지 {page_no}] JSON 파싱 실패: {json_error}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"[페이지 {page_no}] 요청 시간 초과 (30초)")
        return None
    except Exception as e:
        print(f"[페이지 {page_no}] 예상치 못한 오류: {e}")
        return None

def get_product_detail_rancidity(prdlst_report_no):
    """개별 제품의 상세 정보에서 산패도 정보 조회"""
    detail_params = {
        "prdlst_report_no": prdlst_report_no,
        "menu_grp": "MENU_NEW01", 
        "menu_no": "2672"
    }
    
    try:
        response = session.get(DETAIL_URL, params=detail_params, headers=get_headers(), timeout=30)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 기준 및 규격 찾기
        standard_cell = None
        for th in soup.find_all("th"):
            if "기준" in th.get_text() and "규격" in th.get_text():
                standard_cell = th.find_next("td")
                break
        
        if not standard_cell:
            return None
            
        standard_text = standard_cell.get_text()
        
        # 산패도 관련 정보 추출
        rancidity_info = extract_rancidity_info(standard_text)
        
        return rancidity_info
            
    except Exception as e:
        print(f"    상세 정보 조회 실패 ({prdlst_report_no}): {e}")
        return None

def extract_rancidity_info(standard_text):
    """기준 및 규격 텍스트에서 산패도 정보 추출"""
    rancidity_info = {
        "산가": None,
        "과산화물가": None, 
        "아니시딘가": None,
        "총산화가": None
    }
    
    # 산가 추출 (Acid Value)
    acid_pattern = r"산가[:\s]*([0-9.]+)\s*이하"
    acid_match = re.search(acid_pattern, standard_text, re.IGNORECASE)
    if acid_match:
        rancidity_info["산가"] = float(acid_match.group(1))
    
    # 과산화물가 추출 (Peroxide Value)
    peroxide_pattern = r"과산화물가[:\s]*([0-9.]+)\s*이하"
    peroxide_match = re.search(peroxide_pattern, standard_text, re.IGNORECASE)
    if peroxide_match:
        rancidity_info["과산화물가"] = float(peroxide_match.group(1))
    
    # 아니시딘가 추출 (Anisidine Value)
    anisidine_patterns = [
        r"아니시딘가[:\s]*([0-9.]+)\s*이하",
        r"애니시딘가[:\s]*([0-9.]+)\s*이하"
    ]
    for pattern in anisidine_patterns:
        anisidine_match = re.search(pattern, standard_text, re.IGNORECASE)
        if anisidine_match:
            rancidity_info["아니시딘가"] = float(anisidine_match.group(1))
            break
    
    # 총산화가 추출 (Total Oxidation Value, Totox)
    totox_patterns = [
        r"총\s*산화가[:\s]*([0-9.]+)\s*이하",
        r"총\s*옥시가[:\s]*([0-9.]+)\s*이하",
        r"totox[:\s]*([0-9.]+)\s*이하"
    ]
    for pattern in totox_patterns:
        totox_match = re.search(pattern, standard_text, re.IGNORECASE)
        if totox_match:
            rancidity_info["총산화가"] = float(totox_match.group(1))
            break
    
    # 산패도 정보가 하나라도 있으면 반환
    if any(v is not None for v in rancidity_info.values()):
        return rancidity_info
    
    return None

def check_rancidity_standards(rancidity_info):
    """산패도 기준 통과 여부 확인"""
    standards = {
        "산가": 3.0,
        "과산화물가": 5.0,
        "아니시딘가": 20.0,
        "총산화가": 26.0
    }
    
    results = {}
    for key, standard in standards.items():
        if rancidity_info.get(key) is not None:
            value = rancidity_info[key]
            results[f"{key}_통과"] = value <= standard
            results[f"{key}_값"] = value
            results[f"{key}_기준"] = standard
        else:
            results[f"{key}_통과"] = None
            results[f"{key}_값"] = None
            results[f"{key}_기준"] = standard
    
    return results

def extract_product_info(response_data, include_rancidity=False):
    """검색 결과에서 제품 정보 추출 (산패도 정보 포함)"""
    products = []
    
    if not isinstance(response_data, list):
        print("예상치 못한 응답 형식")
        return products
    
    print(f"JSON 리스트 응답 처리 중... ({len(response_data)}개)")
    
    for i, item in enumerate(response_data, 1):
        try:
            # 기본 제품 정보
            product_info = {
                "번호": item.get("no", ""),
                "제품명": item.get("prdlst_nm", ""),
                "업소명": item.get("bssh_nm", ""),
                "신고번호": item.get("prdlst_report_no", ""),
                "등록일": item.get("prms_dt", ""),
                "prdlstReportNo": item.get("prdlst_report_no", ""),
                "총_개수": item.get("total_count", "")
            }
            
            # 산패도 정보 추출 (필수)
            if include_rancidity and product_info["prdlstReportNo"]:
                print(f"  ({i}/{len(response_data)}) {product_info['제품명']} 상세 정보 수집 중...")
                
                rancidity_info = get_product_detail_rancidity(product_info["prdlstReportNo"])
                
                if rancidity_info:
                    # 산패도 정보 추가
                    product_info.update(rancidity_info)
                    
                    # 기준 통과 여부 확인
                    standards_check = check_rancidity_standards(rancidity_info)
                    product_info.update(standards_check)
                    
                    print(f"    → 산패도 정보 발견!")
                else:
                    print(f"    → 산패도 정보 없음")
                
                # 서버 부하 방지 (매우 중요!)
                time.sleep(1.5)
            
            products.append(product_info)
            
        except Exception as e:
            print(f"제품 정보 추출 오류: {e}")
            continue
    
    print(f"추출된 제품 수: {len(products)}")
    return products

def collect_all_omega3_products(search_term="오메가3", show_cnt=50):
    """모든 오메가3 제품 수집 (산패도 정보 포함)"""
    print(f"'{search_term}' 검색어로 모든 제품 수집을 시작합니다...")
    print("=" * 80)
    
    # 첫 번째 페이지로 전체 개수 확인
    first_page_data = search_omega3_products(1, search_term, show_cnt)
    if not first_page_data or len(first_page_data) == 0:
        print("검색 결과가 없습니다.")
        return []
    
    total_count = int(first_page_data[0].get("total_count", 0))
    print(f"총 {total_count}개 제품 발견!")
    
    # 필요한 페이지 수 계산
    total_pages = (total_count + show_cnt - 1) // show_cnt
    print(f"{show_cnt}개씩 {total_pages}페이지에 걸쳐 수집합니다.")
    print("=" * 80)
    
    all_products = []
    
    for page in range(1, total_pages + 1):
        print(f"\n🔍 [{page}/{total_pages}] 페이지 처리 중...")
        
        if page == 1:
            # 첫 페이지는 이미 가져왔음
            response_data = first_page_data
        else:
            response_data = search_omega3_products(page, search_term, show_cnt)
            if not response_data:
                print(f"❌ {page} 페이지 요청 실패")
                break
        
        # 제품 정보 추출 (산패도 정보 포함)
        products = extract_product_info(response_data, include_rancidity=True)
        if not products:
            print(f"❌ {page} 페이지에서 제품 정보 추출 실패")
            break
        
        all_products.extend(products)
        print(f"✅ {page} 페이지에서 {len(products)}개 제품 처리 완료 (누적: {len(all_products)}개)")
        
        # 페이지 간 서버 부하 방지 (중요!)
        if page < total_pages:
            print("⏱️ 다음 페이지 처리를 위해 3초 대기...")
            time.sleep(3)
    
    print("\n" + "=" * 80)
    print(f"🎉 총 {len(all_products)}개 제품 수집 완료!")
    return all_products

def save_results(results, filename="omega3_rancidity_complete.csv"):
    """결과를 CSV 파일로 저장"""
    if results:
        df = pd.DataFrame(results)
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"\n📄 결과가 {filename} 파일로 저장되었습니다.")
        
        # 산패도 정보가 있는 제품 개수 출력
        rancidity_columns = ['산가', '과산화물가', '아니시딘가', '총산화가']
        rancidity_products = df[df[rancidity_columns].notna().any(axis=1)]
        print(f"📊 총 {len(df)}개 제품 중 {len(rancidity_products)}개 제품에서 산패도 정보 발견")
        
        if len(rancidity_products) > 0:
            # 산패도 정보가 있는 제품들만 별도 저장
            rancidity_filename = "omega3_with_rancidity_complete.csv"
            rancidity_products.to_csv(rancidity_filename, index=False, encoding="utf-8-sig")
            print(f"📄 산패도 정보가 있는 제품이 {rancidity_filename}로 저장되었습니다.")
            
            # 산패도 기준을 모두 통과한 제품 필터링
            rancidity_pass_cols = ['산가_통과', '과산화물가_통과', '아니시딘가_통과', '총산화가_통과']
            passed_products = rancidity_products[rancidity_products[rancidity_pass_cols].all(axis=1, skipna=True)]
            
            if not passed_products.empty:
                print(f"✅ 산패도 기준을 모두 통과한 제품: {len(passed_products)}개")
                passed_filename = "omega3_passed_standards_complete.csv"
                passed_products.to_csv(passed_filename, index=False, encoding="utf-8-sig")
                print(f"📄 기준 통과 제품이 {passed_filename}로 저장되었습니다.")
            else:
                print("⚠️ 산패도 기준을 모두 통과한 제품이 없습니다.")
        
        return df
    else:
        print("❌ 저장할 데이터가 없습니다.")
        return None

def main():
    """메인 실행 함수"""
    print("🧬 오메가3 건강기능식품 완전 데이터 수집을 시작합니다.")
    print("=" * 80)
    
    # 전체 오메가3 제품 수집 (산패도 정보 포함)
    print("🔍 1단계: 모든 오메가3 제품 수집 및 산패도 정보 추출")
    all_products = collect_all_omega3_products(search_term="오메가3", show_cnt=50)
    
    if not all_products:
        print("❌ 수집된 제품이 없습니다.")
        return
    
    print(f"\n🎯 총 {len(all_products)}개의 오메가3 제품 데이터 수집 완료!")
    
    # 결과 저장
    print("\n💾 2단계: 결과 저장")
    df = save_results(all_products)
    
    print("\n🎉 모든 작업이 완료되었습니다!")
    print("=" * 80)

if __name__ == "__main__":
    main()