import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=data)

def check_reservation():
    target_url = "https://res.knps.or.kr/eco/searchEcoMonthReservation.do"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://res.knps.or.kr/eco/searchEcoMonthReservation.do'
    }
    
    # 변산반도 생태탐방원 (생활관) 조회 파라미터
    # ※ 조회하고 싶은 연월(searchYearMonth)이나 지점(deptId)이 변경되면 이 부분을 수정하세요.
    payload = {
        'searchYearMonth': '202610',  # 예: 2026년 10월
        'deptId': 'B183001',          # 변산반도 생태탐방원
        'ctgType': '01'               # 생활관
    }
    
    try:
        response = requests.post(target_url, headers=headers, data=payload)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # class 이름에 'calendar-cell'과 'sat'이 모두 들어간 토요일 셀 탐색
        saturday_cells = soup.find_all('div', class_=lambda c: c and 'calendar-cell' in c and 'sat' in c)
        
        available_saturdays = []
        
        for cell in saturday_cells:
            use_date = cell.get('data-usedt', '날짜 미상')
            em_tag = cell.find('em')
            
            if em_tag:
                try:
                    count = int(em_tag.text.strip())
                    print(f"조회된 토요일 [{use_date}]: {count}개")
                    
                    if count >= 0:
                        available_saturdays.append(f"- {use_date}: {count}개 잔여")
                except ValueError:
                    continue

        # 잔여 객실이 1개 이상 존재하면 텔레그램 알림 전송
        if available_saturdays:
            msg_details = "\n".join(available_saturdays)
            message = (
                f"[변산반도 생태탐방원 토요일 알림]\n"
                f"🎉 예약 가능한 토요일 객실이 발견되었습니다!\n\n"
                f"{msg_details}\n\n"
                f"👉 바로 예약하기: {target_url}"
            )
            send_telegram_msg(message)
            print("텔레그램 알림 발송 완료!")
        else:
            print("현재 예약 가능한 토요일 객실이 없습니다.")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_reservation()
