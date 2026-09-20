import os
import requests
from bs4 import BeautifulSoup

# GitHub Secrets에서 정보 불러오기
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=data)

def check_reservation():
    target_url = "https://res.knps.or.kr/eco/searchEcoMonthReservation.do"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(target_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TODO: 실제 페이지 HTML 구조에 맞춰 토요일 잔여 객실 수 파싱 로직 작성
        remaining_count = 1 
        
        if remaining_count >= 1:
            msg = f"[국립공원 생태탐방원 알림]\n토요일 잔여 객실이 {remaining_count}개 있습니다!\n{target_url}"
            send_telegram_msg(msg)
        else:
            print("현재 예약 가능한 토요일 객실이 없습니다.")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_reservation()
