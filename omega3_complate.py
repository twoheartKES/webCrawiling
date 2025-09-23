import requests
import json
import pandas as pd
import time
import re
from urllib.parse import quote

def get_omega3_products_from_api(api_key, service_id, product_name="오메가3", start_idx=1, end_idx=10, data_type="json"):
    """
    식품의약품안전처 OpenAPI를 사용하여 건강기능식품 정보 조회
    
    Args:
        api_key (str): OpenAPI 인증키
        service_id (str): OpenAPI 서비스 ID
        product_name (str): 검색할 제품명 (기본값: "오메가3")
        start_idx (int): 요청 시작 위치 (기본값: 1)
        end_idx (int): 요청 종료 위치 (기본값: 10)
        data_type (str): 응답 데이터 타입 ("json" 또는 "xml", 기본값: "json")
    
    Returns:
        dict: API 응답 데이터
    """
    
    # 파라미터로 받은 service_id 사용
    
    # API 기본 URL
    base_url = "http://openapi.foodsafetykorea.go.kr/api"
    
    # URL 구성
    api_url = f"{base_url}/{api_key}/{service_id}/{data_type}/{start_idx}/{end_idx}"
    
    # 추가 검색 조건이 있을 경우 (제품명으로 검색)
    if product_name:
        # URL 인코딩
        encoded_product_name = quote(product_name)
        api_url += f"/PRDLST_NM={encoded_product_name}"
    
    print(f"API 요청 URL: {api_url}")
    
    try:
        # API 요청
        response = requests.get(api_url, timeout=30)
        
        print(f"응답 상태 코드: {response.status_code}")
        
        print(f"응답 내용 (처음 500자): {response.text[:500]}")
        
        if response.status_code == 200:
            if data_type.lower() == "json":
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 오류: {e}")
                    print(f"응답 전체 내용: {response.text}")
                    return None
            else:
                return response.text
        else:
            print(f"API 요청 실패: HTTP {response.status_code}")
            print(f"응답 내용: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return None

def parse_api_response(api_response):
    """
    API 응답 데이터를 파싱하여 제품 정보 리스트로 변환
    
    Args:
        api_response (dict): API 응답 데이터
    
    Returns:
        list: 제품 정보 딕셔너리 리스트
    """
    
    if not api_response:
        print("API 응답이 없습니다.")
        return []
    
    try:
        # 응답 구조 확인
        print(f"API 응답 키: {list(api_response.keys())}")
        
        # 일반적인 식약처 API 응답 구조 (서비스 ID에 따라 다름)
        service_key = None
        for key in api_response.keys():
            if key.startswith('I') or key.startswith('C'):
                service_key = key
                break
        
        if service_key and service_key in api_response:
            result_data = api_response[service_key]
            
            # 헤더 정보 확인
            if 'RESULT' in result_data:
                result_info = result_data['RESULT']
                print(f"결과 코드: {result_info.get('CODE')}")
                print(f"결과 메시지: {result_info.get('MSG')}")
                
                if result_info.get('CODE') != 'INFO-000':
                    print(f"API 오류: {result_info.get('MSG')}")
                    return []
            
            # 실제 데이터 추출
            if 'row' in result_data:
                products = result_data['row']
                print(f"총 {len(products)}개의 제품 정보를 찾았습니다.")
                return products
            else:
                print("제품 데이터를 찾을 수 없습니다.")
                return []
        
        else:
            print("예상치 못한 API 응답 구조입니다.")
            print(f"응답 내용: {json.dumps(api_response, indent=2, ensure_ascii=False)}")
            return []
            
    except Exception as e:
        print(f"API 응답 파싱 중 오류 발생: {e}")
        return []

def extract_rancidity_from_standards(standards_text):
    """
    기준규격 텍스트에서 산패도 정보 추출
    
    Args:
        standards_text (str): 기준규격 텍스트
    
    Returns:
        dict: 산패도 정보 (산가, 과산화물가, 아니시딘가, 총산화가)
    """
    if not standards_text:
        return None
    
    rancidity_info = {
        "산가": None,
        "과산화물가": None,
        "아니시딘가": None,
        "총산화가": None
    }
    
    # 산가 추출
    acid_patterns = [
        r"산가\s*[:：]\s*([0-9.]+)\s*이하",
        r"산가\s*([0-9.]+)\s*이하",
        r"ㆍ산가\s*[:：]\s*([0-9.]+)\s*이하"
    ]
    for pattern in acid_patterns:
        match = re.search(pattern, standards_text, re.IGNORECASE)
        if match:
            rancidity_info["산가"] = float(match.group(1))
            break
    
    # 과산화물가 추출
    peroxide_patterns = [
        r"과산화물가\s*[:：]\s*([0-9.]+)\s*이하",
        r"과산화물가\s*([0-9.]+)\s*이하",
        r"ㆍ과산화물가\s*[:：]\s*([0-9.]+)\s*이하"
    ]
    for pattern in peroxide_patterns:
        match = re.search(pattern, standards_text, re.IGNORECASE)
        if match:
            rancidity_info["과산화물가"] = float(match.group(1))
            break
    
    # 아니시딘가 추출
    anisidine_patterns = [
        r"아니시딘가\s*[:：]\s*([0-9.]+)\s*이하",
        r"아니시딘가\s*([0-9.]+)\s*이하",
        r"ㆍ아니시딘가\s*[:：]\s*([0-9.]+)\s*이하",
        r"애니시딘가\s*[:：]\s*([0-9.]+)\s*이하"
    ]
    for pattern in anisidine_patterns:
        match = re.search(pattern, standards_text, re.IGNORECASE)
        if match:
            rancidity_info["아니시딘가"] = float(match.group(1))
            break
    
    # 총산화가 추출
    totox_patterns = [
        r"총산화가\s*[:：]\s*([0-9.]+)\s*이하",
        r"총산화가\s*([0-9.]+)\s*이하",
        r"ㆍ총산화가\s*[:：]\s*([0-9.]+)\s*이하",
        r"총\s*옥시가\s*[:：]\s*([0-9.]+)\s*이하",
        r"totox\s*[:：]\s*([0-9.]+)\s*이하"
    ]
    for pattern in totox_patterns:
        match = re.search(pattern, standards_text, re.IGNORECASE)
        if match:
            rancidity_info["총산화가"] = float(match.group(1))
            break
    
    return rancidity_info

def check_filtering_criteria(product):
    """
    3가지 기준으로 제품 필터링
    
    Args:
        product (dict): 제품 정보
    
    Returns:
        tuple: (통과여부, 필터링사유)
    """
    # 1. 기타원재료 체크 (빈값 또는 공백이어야 함)
    etc_materials = product.get("ETC_RAWMTRL_NM", "")
    if etc_materials and etc_materials.strip():
        return False, "기타원재료가 존재함"
    
    # 2. 주된기능성에서 비타민 E 체크 (없어야 함)
    primary_function = product.get("PRIMARY_FNCLTY", "")
    if "비타민" in primary_function and "E" in primary_function:
        return False, "비타민 E 포함"
    
    # 3. 산패도 기준 체크
    standards_text = product.get("STDR_STND", "")
    rancidity_info = extract_rancidity_from_standards(standards_text)
    
    if not rancidity_info:
        return False, "산패도 정보 없음"
    
    # 산패도 기준 체크
    criteria = {
        "산가": 3.0,
        "과산화물가": 5.0,
        "아니시딘가": 20.0,
        "총산화가": 26.0
    }
    
    for key, max_value in criteria.items():
        if rancidity_info.get(key) is not None:
            if rancidity_info[key] > max_value:
                return False, f"{key} 기준 초과 ({rancidity_info[key]} > {max_value})"
    
    # 모든 기준 통과
    return True, "모든 기준 통과"

def collect_filtered_omega3_products(api_key, service_id, total_count=1400, batch_size=100):
    """
    분할 요청으로 오메가3 제품을 수집하고 기준에 맞는 제품만 필터링
    
    Args:
        api_key (str): API 키
        service_id (str): 서비스 ID
        total_count (int): 총 수집할 제품 수
        batch_size (int): 배치당 요청 제품 수
    
    Returns:
        list: 필터링된 제품 리스트
    """
    print(f"🔍 오메가3 제품 {total_count}개 분할 수집 시작 (배치 크기: {batch_size})")
    print("=" * 80)
    
    all_filtered_products = []
    total_processed = 0
    total_passed = 0
    
    # 배치 개수 계산
    total_batches = (total_count + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size + 1
        end_idx = min(start_idx + batch_size - 1, total_count)
        
        print(f"\n📦 배치 {batch_num + 1}/{total_batches}: {start_idx}~{end_idx} ({end_idx - start_idx + 1}개)")
        
        try:
            # API 요청
            api_response = get_omega3_products_from_api(
                api_key=api_key,
                service_id=service_id,
                product_name="오메가3",
                start_idx=start_idx,
                end_idx=end_idx,
                data_type="json"
            )
            
            # 응답 파싱
            products = parse_api_response(api_response)
            
            if not products:
                print(f"❌ 배치 {batch_num + 1}: 데이터 없음")
                continue
            
            print(f"✅ 배치 {batch_num + 1}: {len(products)}개 제품 수집")
            
            # 필터링 수행
            batch_filtered = []
            for i, product in enumerate(products):
                total_processed += 1
                
                # 필터링 기준 적용
                passed, reason = check_filtering_criteria(product)
                
                if passed:
                    batch_filtered.append(product)
                    total_passed += 1
                    print(f"  ✅ [{i+1:2d}] {product.get('PRDLST_NM', 'Unknown')[:30]:<30} → 통과")
                else:
                    print(f"  ❌ [{i+1:2d}] {product.get('PRDLST_NM', 'Unknown')[:30]:<30} → {reason}")
            
            all_filtered_products.extend(batch_filtered)
            
            print(f"📊 배치 {batch_num + 1} 결과: {len(batch_filtered)}/{len(products)}개 통과")
            print(f"📊 전체 누적: {total_passed}/{total_processed}개 통과 ({total_passed/total_processed*100:.1f}%)")
            
            # 배치 간 대기 (서버 부하 방지)
            if batch_num < total_batches - 1:
                print("⏱️  다음 배치를 위해 2초 대기...")
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ 배치 {batch_num + 1} 처리 중 오류: {e}")
            continue
    
    print("\n" + "=" * 80)
    print(f"🎉 수집 완료!")
    print(f"📊 최종 결과: {total_passed}/{total_processed}개 제품이 기준을 통과했습니다 ({total_passed/total_processed*100:.1f}%)")
    
    return all_filtered_products

def save_to_csv(products_data, filename="omega3_products.csv"):
    """
    제품 정보를 CSV 파일로 저장
    
    Args:
        products_data (list): 제품 정보 리스트
        filename (str): 저장할 CSV 파일명
    """
    
    if not products_data:
        print("저장할 데이터가 없습니다.")
        return
    
    try:
        # DataFrame 생성
        df = pd.DataFrame(products_data)
        
        print(f"데이터프레임 생성 완료: {len(df)}행 x {len(df.columns)}열")
        print(f"컬럼 목록: {list(df.columns)}")
        
        # CSV 파일로 저장 (UTF-8 BOM 포함하여 한글 깨짐 방지)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"✅ 데이터가 '{filename}' 파일로 저장되었습니다.")
        
        # 저장된 데이터 요약 정보 출력
        print("\n📊 저장된 데이터 요약:")
        print(f"- 총 제품 수: {len(df)}")
        print(f"- 총 컬럼 수: {len(df.columns)}")
        
        # 주요 컬럼 샘플 데이터 출력
        if 'PRDLST_NM' in df.columns:
            print(f"- 제품명 샘플: {df['PRDLST_NM'].head(3).tolist()}")
        if 'BSSH_NM' in df.columns:
            print(f"- 업소명 샘플: {df['BSSH_NM'].head(3).tolist()}")
            
    except Exception as e:
        print(f"CSV 저장 중 오류 발생: {e}")

def save_filtered_products_to_csv(products, filename="omega3_filtered_products.csv"):
    """
    필터링된 제품을 한글 컬럼명으로 CSV 저장
    
    Args:
        products (list): 필터링된 제품 리스트
        filename (str): 저장할 파일명
    """
    if not products:
        print("저장할 제품이 없습니다.")
        return
    
    # 컬럼명 매핑 (영문 -> 한글)
    column_mapping = {
        "LCNS_NO": "인허가번호",
        "BSSH_NM": "업소명", 
        "PRDLST_REPORT_NO": "품목제조번호",
        "PRDLST_NM": "품목명",
        "PRMS_DT": "허가일자",
        "POG_DAYCNT": "소비기한일수",
        "DISPOS": "제품형태",
        "NTK_MTHD": "섭취방법",
        "PRIMARY_FNCLTY": "주된기능성",
        "IFTKN_ATNT_MATR_CN": "섭취시주의사항",
        "CSTDY_MTHD": "보관방법",
        "PRDLST_CDNM": "유형",
        "STDR_STND": "기준규격",
        "HIENG_LNTRT_DVS_NM": "고열량저영양여부",
        "PRODUCTION": "생산종료여부",
        "CHILD_CRTFC_YN": "어린이기호식품품질인증여부",
        "PRDT_SHAP_CD_NM": "제품형태코드명",
        "FRMLC_MTRQLT": "포장재질",
        "RAWMTRL_NM": "품목유형",
        "INDUTY_CD_NM": "업종",
        "LAST_UPDT_DTM": "최종수정일자",
        "INDIV_RAWMTRL_NM": "기능성원재료",
        "ETC_RAWMTRL_NM": "기타원재료",
        "CAP_RAWMTRL_NM": "캡슐원재료",
        "FRMLC_MTHD": "포장방법"
    }
    
    try:
        # DataFrame 생성
        df = pd.DataFrame(products)
        
        # 컬럼명을 한글로 변경
        df = df.rename(columns=column_mapping)
        
        # CSV 저장 (UTF-8 BOM 포함)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 필터링된 {len(products)}개 제품이 '{filename}' 파일로 저장되었습니다.")
        
        # 저장된 데이터 요약
        print(f"📊 저장된 데이터: {len(df)}행 x {len(df.columns)}열")
        
        # 샘플 제품 정보
        if len(products) > 0:
            print(f"\n📋 저장된 제품 샘플:")
            for i, product in enumerate(products[:3]):
                print(f"  {i+1}. {product.get('PRDLST_NM', 'Unknown')}")
                print(f"     업소: {product.get('BSSH_NM', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ CSV 저장 중 오류: {e}")

def get_multiple_pages(api_key, product_name="오메가3", page_size=100, max_pages=10):
    """
    여러 페이지의 데이터를 순차적으로 가져오기
    
    Args:
        api_key (str): OpenAPI 인증키
        product_name (str): 검색할 제품명
        page_size (int): 페이지당 데이터 개수
        max_pages (int): 최대 페이지 수
    
    Returns:
        list: 모든 페이지의 제품 정보 리스트
    """
    
    all_products = []
    
    for page in range(max_pages):
        start_idx = page * page_size + 1
        end_idx = start_idx + page_size - 1
        
        print(f"\n📄 페이지 {page + 1} 데이터 요청 중... ({start_idx}~{end_idx})")
        
        # API 요청
        api_response = get_omega3_products_from_api(
            api_key=api_key,
            product_name=product_name,
            start_idx=start_idx,
            end_idx=end_idx,
            data_type="json"
        )
        
        # 응답 데이터 파싱
        products = parse_api_response(api_response)
        
        if not products:
            print(f"페이지 {page + 1}에서 데이터를 가져올 수 없습니다. 수집을 종료합니다.")
            break
        
        all_products.extend(products)
        print(f"페이지 {page + 1}에서 {len(products)}개 제품 수집 (총 누적: {len(all_products)}개)")
        
        # 마지막 페이지인지 확인 (받은 데이터가 page_size보다 적으면 마지막 페이지)
        if len(products) < page_size:
            print("마지막 페이지에 도달했습니다.")
            break
        
        # API 호출 제한을 위한 대기 시간
        time.sleep(1)
    
    return all_products

def main():
    """
    메인 실행 함수 - 필터링된 오메가3 제품 수집
    """
    print("🧬 오메가3 제품 필터링 수집기")
    print("=" * 80)
    
    # API 설정
    API_KEY = "ffeaa23428844ae99418"
    SERVICE_ID = "I0030"
    TOTAL_COUNT = 1400  # 수집할 총 제품 수
    BATCH_SIZE = 100    # 배치당 제품 수
    
    print(f"📋 수집 설정:")
    print(f"- 총 제품 수: {TOTAL_COUNT}개")
    print(f"- 배치 크기: {BATCH_SIZE}개")
    print(f"- 예상 배치 수: {(TOTAL_COUNT + BATCH_SIZE - 1) // BATCH_SIZE}개")
    
    print(f"\n🎯 필터링 기준:")
    print(f"1. 기타원재료: 빈값 또는 공백")
    print(f"2. 주된기능성: 비타민 E 미포함")
    print(f"3. 산패도 기준:")
    print(f"   - 산가: 3.0 이하")
    print(f"   - 과산화물가: 5.0 이하") 
    print(f"   - 아니시딘가: 20.0 이하")
    print(f"   - 총산화가: 26.0 이하")
    
    # 필터링된 제품 수집
    filtered_products = collect_filtered_omega3_products(
        api_key=API_KEY,
        service_id=SERVICE_ID,
        total_count=TOTAL_COUNT,
        batch_size=BATCH_SIZE
    )
    
    if filtered_products:
        # CSV 파일로 저장
        save_filtered_products_to_csv(
            filtered_products, 
            "omega3_filtered_high_quality.csv"
        )
    else:
        print("❌ 기준을 통과한 제품이 없습니다.")
    
    print("\n🎉 모든 작업이 완료되었습니다!")

if __name__ == "__main__":
    main()