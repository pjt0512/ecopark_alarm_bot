import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://res.knps.or.kr/eco/searchEcoMonthReservation.do',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    month_str = str(month).zfill(2)
    year_str = str(year)
    
    # 서버 백엔드 파라미터 인식 패턴을 모두 지원하도록 작성
    payload = {
        'deptId': dept_id,
        'ctgType': '01',
        'year': year_str,
        'month': month_str,
        'searchYear': year_str,
        'searchMonth': month_str,
        'searchYearMonth': f"{year_str}{month_str}"
    }
    
    saturday_results = []
    
    try:
        response = requests.post(target_url, headers=headers, data=payload)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # class에 'calendar-cell'과 'sat'이 들어간 토요일 셀만 탐색
        saturday_cells = soup.find_all('div', class_=lambda c: c and 'calendar-cell' in c and 'sat' in c)
        
        for cell in saturday_cells:
            use_date = cell.get('data-usedt', '')
            
            # 해당 월의 날짜인지 검증 (예: 10월 조회 시 10월 날짜만 파싱)
            if not use_date or not use_date.startswith(f"{year_str}-{month_str}"):
                continue
                
            em_tag = cell.find('em')
            if em_tag:
                try:
                    count = int(em_tag.text.strip())
                    print(f"[{dept_name}] {use_date} (토): {count}개")
                    
                    # 💡 테스트 시: count >= 0
                    # 💡 실제 가동 시: count >= 1 로 복구
                    if count >= 0:
                        saturday_results.append(f"- {use_date}: {count}개 잔여")
                except ValueError:
                    continue
                    
    except Exception as e:
        print(f"[{year_str}-{month_str}] 조회 중 오류 발생: {e}")
        
    return saturday_results

def main():
    dept_id = "B183001"
    dept_name = "변산반도 생태탐방원(생활관)"
    
    # 📅 현재 날짜 기준으로 이번 달과 다음 달 자동 계산
    now = datetime.now()
    next_month_dt = now + relativedelta(months=1)
    
    target_months = [
        (now.year, now.month),
        (next_month_dt.year, next_month_dt.month)
    ]
    
    all_available = []
    
    for year, month in target_months:
        results = check_month_reservation(year, month, dept_id, dept_name)
        if results:
            all_available.extend(results)
            
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
