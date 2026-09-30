import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
STATE_FILE = "last_state.json"

# 📌 [설정 1] 토요일 외에 감지하고 싶은 특정 날짜 (YYYY-MM-DD)
TARGET_DATES = [
    "2026-10-04",
    "2026-10-09",
]

# 📌 [설정 2] 모니터링할 전국 생태탐방원 목록 (필요없는 곳은 주석처리 가능)
ECO_PARKS = {
    "B183001": "변산반도 생태탐방원",
    "B013001": "북한산 생태탐방원",
    "B033001": "설악산 생태탐방원",
    "B043001": "지리산 생태탐방원",
    "B053001": "가야산 생태탐방원",
    "B093001": "내장산 생태탐방원",
    "B113001": "소백산 생태탐방원",
    "B133001": "한려해상 생태탐방원",
    "B193001": "무등산 생태탐방원",
}

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

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
        print(f"상태 저장 오류: {e}")

def check_month_reservation(year, month, dept_id, dept_name):
    target_url = "https://res.knps.or.kr/eco/searchEcoMonthReservation.do"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) BeautifulSoup',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://res.knps.or.kr/eco/searchEcoMonthReservation.do',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    month_str = str(month).zfill(2)
    year_str = str(year)
    
    payload = {
        'deptId': dept_id,
        'ctgType': '01',  # 생활관 기준
        'year': year_str,
        'month': month_str,
        'searchYear': year_str,
        'searchMonth': month_str,
        'searchYearMonth': f"{year_str}{month_str}"
    }
    
    matched_data = {}
    
    try:
        response = requests.post(target_url, headers=headers, data=payload, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_cells = soup.find_all('div', class_=lambda c: c and 'calendar-cell' in c)
        
        for cell in all_cells:
            use_date = cell.get('data-usedt', '')
            if not use_date or not use_date.startswith(f"{year_str}-{month_str}"):
                continue
                
            is_saturday = 'sat' in cell.get('class', [])
            is_target_date = use_date in TARGET_DATES
            
            if is_saturday or is_target_date:
                em_tag = cell.find('em')
                if em_tag:
                    try:
                        count = int(em_tag.text.strip())
                        tag_type = "토요일" if is_saturday else "지정일"
                        
                        if count >= 0:
                            matched_data[use_date] = {
                                "count": count,
                                "type": tag_type
                            }
                    except ValueError:
                        continue
                        
    except Exception as e:
        print(f"[{dept_name}] [{year_str}-{month_str}] 조회 시 오류: {e}")
        
    return matched_data

def run_check():
    now = datetime.now()
    next_month_dt = now + relativedelta(months=1)
    
    target_months = [
        (now.year, now.month),
        (next_month_dt.year, next_month_dt.month)
    ]
    
    current_state = {}
    
    # 등록된 모든 생태탐방원 순회 조회
    for dept_id, dept_name in ECO_PARKS.items():
        park_state = {}
        for year, month in target_months:
            month_data = check_month_reservation(year, month, dept_id, dept_name)
            park_state.update(month_data)
            
        if park_state:
            current_state[dept_name] = park_state
        
        # 서버 과부하 방지를 위한 미세 대기 (0.2초)
        time.sleep(0.2)
        
    last_state = load_last_state()
    
    # 상태 변경 감지 및 알림
    if current_state != last_state:
        if current_state:
            msg_blocks = []
            for park_name, dates in current_state.items():
                date_lines = [f"  - {date} ({info['type']}): {info['count']}개 잔여" for date, info in dates.items()]
                msg_blocks.append(f"🏞️ [{park_name}]\n" + "\n".join(date_lines))
                
            message = (
                f"🎉 [전국 생태탐방원] 예약 가능 객실 변동 알림!\n\n"
                + "\n\n".join(msg_blocks) +
                f"\n\n👉 지금 예약하기:\nhttps://res.knps.or.kr/eco/searchEcoMonthReservation.do"
            )
            send_telegram_msg(message)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔔 전국 탐방원 알림 발송 완료!")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 이전 잔여 방 매진됨.")
            
        save_current_state(current_state)
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 변동 없음 (대기 중...)")

if __name__ == "__main__":
    # 5시간(300분) 동안 1분 간격으로 연속 모니터링
    MONITOR_MINUTES = 300
    print(f"🚀 전국 생태탐방원 {MONITOR_MINUTES}분(5시간) 연속 모니터링 시작!")
    
    start_time = time.time()
    
    while time.time() - start_time < MONITOR_MINUTES * 60:
        try:
            run_check()
        except Exception as e:
            print(f"실행 중 예외 발생: {e}")
            
        time.sleep(60)  # 1분 대기
        
    print("5시간 모니터링이 완료되어 종료합니다.")
