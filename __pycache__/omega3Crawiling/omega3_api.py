import requests
import json
import pandas as pd
import time
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
    메인 실행 함수
    """
    print("🔍 식품의약품안전처 OpenAPI를 사용한 오메가3 제품 정보 수집")
    print("=" * 70)
    
    # API 설정
    API_KEY = "ffeaa23428844ae99418"  # 제공받은 인증키
    SERVICE_ID = "I0030"
    PRODUCT_NAME = "오메가3"
    START_IDX = 1
    END_IDX = 10
    DATA_TYPE = "json"
    
    print(f"📋 검색 조건:")
    print(f"- 인증키: {API_KEY}")
    print(f"- 제품명: {PRODUCT_NAME}")
    print(f"- 시작 위치: {START_IDX}")
    print(f"- 종료 위치: {END_IDX}")
    print(f"- 데이터 타입: {DATA_TYPE}")
    print("-" * 70)
    
    # 단일 페이지 요청
    print("\n🚀 API 요청 시작...")
    api_response = get_omega3_products_from_api(
        api_key=API_KEY,
        service_id=SERVICE_ID,
        product_name=PRODUCT_NAME,
        start_idx=START_IDX,
        end_idx=END_IDX,
        data_type=DATA_TYPE
    )
    
    # 응답 데이터 파싱
    print("\n📊 응답 데이터 파싱...")
    products = parse_api_response(api_response)
    
    if products:
        # CSV 파일로 저장
        print("\n💾 CSV 파일 저장...")
        filename = f"omega3_products_{START_IDX}_{END_IDX}.csv"
        save_to_csv(products, filename)
        
        # 첫 번째 제품 정보 상세 출력 (샘플)
        if len(products) > 0:
            print(f"\n📋 첫 번째 제품 정보 샘플:")
            first_product = products[0]
            for key, value in first_product.items():
                print(f"  {key}: {value}")
                
    else:
        print("❌ 수집된 제품 정보가 없습니다.")
    
    print("\n" + "=" * 70)
    print("✅ 작업 완료!")

if __name__ == "__main__":
    main()
