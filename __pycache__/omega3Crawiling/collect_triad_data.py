import pandas as pd
from omega3_api import get_omega3_products_from_api, parse_api_response, save_to_excel_with_sheets

def main():
    """
    트리어드 제품 데이터를 수집하고 기존 오메가3 데이터와 함께 Excel 파일로 저장
    """
    print("🔍 트리어드 제품 데이터 수집 및 통합 저장")
    print("=" * 70)
    
    # API 설정
    API_KEY = "ffeaa23428844ae99418"  # 제공받은 인증키
    SERVICE_ID = "I0030"
    
    # 1. 트리어드 제품 데이터 수집
    print("\n🚀 트리어드 제품 API 요청 시작...")
    triad_response = get_omega3_products_from_api(
        api_key=API_KEY,
        service_id=SERVICE_ID,
        product_name="트리어드",
        start_idx=1,
        end_idx=10,
        data_type="json"
    )
    
    # 트리어드 응답 데이터 파싱
    print("\n📊 트리어드 응답 데이터 파싱...")
    triad_products = parse_api_response(triad_response)
    
    if not triad_products:
        print("❌ 트리어드 제품 데이터를 가져올 수 없습니다.")
        return
    
    print(f"✅ 트리어드 제품 {len(triad_products)}개 수집 완료!")
    
    # 2. 기존 오메가3 CSV 파일 읽기
    print("\n📂 기존 오메가3 CSV 파일 읽기...")
    try:
        omega3_df = pd.read_csv("omega3_products_1_10.csv", encoding='utf-8-sig')
        omega3_products = omega3_df.to_dict('records')
        print(f"✅ 기존 오메가3 제품 {len(omega3_products)}개 로드 완료!")
    except FileNotFoundError:
        print("❌ 기존 오메가3 CSV 파일을 찾을 수 없습니다.")
        print("오메가3 데이터 없이 트리어드 데이터만 저장합니다.")
        omega3_products = []
    except Exception as e:
        print(f"❌ CSV 파일 읽기 오류: {e}")
        omega3_products = []
    
    # 3. 데이터를 시트별로 구성
    data_dict = {}
    
    if omega3_products:
        data_dict["오메가3"] = omega3_products
        
    if triad_products:
        data_dict["트리어드"] = triad_products
    
    # 4. Excel 파일로 저장
    print("\n💾 Excel 파일로 통합 저장...")
    save_to_excel_with_sheets(data_dict, "건강기능식품_통합데이터.xlsx")
    
    # 5. 결과 요약
    print("\n" + "=" * 70)
    print("📊 수집 결과 요약:")
    if omega3_products:
        print(f"- 오메가3 제품: {len(omega3_products)}개")
    if triad_products:
        print(f"- 트리어드 제품: {len(triad_products)}개")
        
        # 트리어드 제품 샘플 정보 출력
        print(f"\n📋 트리어드 제품 샘플 정보:")
        if len(triad_products) > 0:
            first_product = triad_products[0]
            for key, value in first_product.items():
                print(f"  {key}: {value}")
    
    print("\n✅ 모든 작업이 완료되었습니다!")
    print("📄 결과 파일: 건강기능식품_통합데이터.xlsx")

if __name__ == "__main__":
    main()
