import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=data)

def check_month_reservation(year, month, dept_id, dept_name):
    """특정 연도(year)와 월(month)의 토요일 잔여 객실을 조회하는 함수"""
    target_url = "https://res.knps.or.kr/eco/searchEcoMonthReservation.do"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://res.knps.or.kr/eco/searchEcoMonthReservation.do'
    }
    
    # 서버 요구 규격에 맞춰 파라미터 전달
    payload = {
        'searchYear': str(year),
        'searchMonth': str(month).zfill(2), # '09', '10' 형태로 변환
        'searchYearMonth': f"{year}{str(month).zfill(2)}",
        'deptId': dept_id,                  # B183001: 변산반도
        'ctgType': '01'                     # 01: 생활관
    }
    
    saturday_results = []
    
    try:
        response = requests.post(target_url, headers=headers, data=payload)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 토요일 셀 추출
        saturday_cells = soup.find_all('div', class_=lambda c: c and 'calendar-cell' in c and 'sat' in c)
        
        for cell in saturday_cells:
            use_date = cell.get('data-usedt', '날짜 미상')
            em_tag = cell.find('em')
            
            if em_tag:
                try:
                    count = int(em_tag.text.strip())
                    print(f"[{dept_name}] {use_date} (토): {count}개")
                    
                    # 테스트 시에는 count >= 0 으로 확인하시고, 실 운영 시 count >= 1 로 변경하세요.
                    if count >= 0:
                        saturday_results.append(f"- {use_date}: {count}개 잔여")
                except ValueError:
                    continue
                    
    except Exception as e:
        print(f"[{year}-{month}] 조회 중 오류 발생: {e}")
        
    return saturday_results

def main():
    dept_id = "B183001"
    dept_name = "변산반도 생태탐방원(생활관)"
    
    # 🔍 조회할 (연도, 월) 목록 설정 (9월, 10월)
    target_months = [
        (2026, 9),
        (2026, 10)
    ]
    
    all_available = []
    
    for year, month in target_months:
        results = check_month_reservation(year, month, dept_id, dept_name)
        if results:
            all_available.extend(results)
            
    # 잔여 객실이 발견되면 텔레그램 발송
    if all_available:
        msg_details = "\n".join(all_available)
        message = (
            f"🏞️ [{dept_name}]\n"
            f"🎉 토요일 예약 가능 객실이 있습니다!\n\n"
            f"{msg_details}\n\n"
            f"👉 지금 예약하기:\nhttps://res.knps.or.kr/eco/searchEcoMonthReservation.do"
        )
        send_telegram_msg(message)
        print("텔레그램 알림 발송 완료!")
    else:
        print(f"[{dept_name}] 현재 예약 가능한 토요일 객실이 없습니다.")

if __name__ == "__main__":
    main()
