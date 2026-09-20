import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
STATE_FILE = "last_state.json"

# 📌 [설정] 알림을 받고 싶은 특정 날짜들을 추가하세요 (YYYY-MM-DD 형식)
TARGET_DATES = [
    "2026-10-04",  # 예시: 일요일
    "2026-10-09",  # 예시: 한글날(공휴일)
]

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=data)

def load_last_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_current_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"상태 저장 중 오류: {e}")

def check_month_reservation(year, month, dept_id, dept_name):
    target_url = "https://res.knps.or.kr/eco/searchEcoMonthReservation.do"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://res.knps.or.kr/eco/searchEcoMonthReservation.do',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    month_str = str(month).zfill(2)
    year_str = str(year)
    
    payload = {
        'deptId': dept_id,
        'ctgType': '01',
        'year': year_str,
        'month': month_str,
        'searchYear': year_str,
        'searchMonth': month_str,
        'searchYearMonth': f"{year_str}{month_str}"
    }
    
    matched_data = {}
    
    try:
        response = requests.post(target_url, headers=headers, data=payload)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 모든 날짜 셀 탐색
        all_cells = soup.find_all('div', class_=lambda c: c and 'calendar-cell' in c)
        
        for cell in all_cells:
            use_date = cell.get('data-usedt', '')
            
            # 조회 중인 월의 날짜만 판별
            if not use_date or not use_date.startswith(f"{year_str}-{month_str}"):
                continue
                
            # 조건 체크: 1) 토요일이거나 2) 내가 설정한 원하는 날짜(TARGET_DATES)에 해당하는지
            is_saturday = 'sat' in cell.get('class', [])
            is_target_date = use_date in TARGET_DATES
            
            if is_saturday or is_target_date:
                em_tag = cell.find('em')
                if em_tag:
                    try:
                        count = int(em_tag.text.strip())
                        tag_type = "토요일" if is_saturday else "지정일"
                        print(f"[{dept_name}] {use_date} ({tag_type}): {count}개")
                        
                        # 💡 잔여 객실이 1개 이상일 때 기록 (테스트 시 count >= 0 으로 변경)
                        if count >= 0:
                            matched_data[use_date] = {
                                "count": count,
                                "type": tag_type
                            }
                    except ValueError:
                        continue
                        
    except Exception as e:
        print(f"[{year_str}-{month_str}] 조회 중 오류 발생: {e}")
        
    return matched_data

def main():
    dept_id = "B183001"
    dept_name = "변산반도 생태탐방원(생활관)"
    
    now = datetime.now()
    next_month_dt = now + relativedelta(months=1)
    
    target_months = [
        (now.year, now.month),
        (next_month_dt.year, next_month_dt.month)
    ]
    
    current_state = {}
    
    for year, month in target_months:
        month_data = check_month_reservation(year, month, dept_id, dept_name)
        current_state.update(month_data)
        
    last_state = load_last_state()
    
    # 상태 변경 여부 확인
    if current_state != last_state:
        if current_state:
            msg_lines = []
            for date, info in current_state.items():
                msg_lines.append(f"- {date} ({info['type']}): {info['count']}개 잔여")
                
            msg_details = "\n".join(msg_lines)
            message = (
                f"🏞️ [{dept_name}]\n"
                f"🎉 예약 가능 객실 변동 알림!\n\n"
                f"{msg_details}\n\n"
                f"👉 지금 예약하기:\nhttps://res.knps.or.kr/eco/searchEcoMonthReservation.do"
            )
            send_telegram_msg(message)
            print("상태 변경 감지: 텔레그램 알림 발송 완료!")
        else:
            print("이전에 있던 잔여 객실이 모두 매진되었습니다.")
            
        save_current_state(current_state)
    else:
        print("이전 조회 결과와 동일함 (알림 스킵)")

if __name__ == "__main__":
    main()
