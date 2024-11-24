import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from matplotlib import rc
from bs4 import BeautifulSoup
import time
import re
import os
from collections import Counter
import platform
# 운영 체제에 따라 폰트 설정
if platform.system() == 'Windows':
    rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':  # macOS
    rc('font', family='AppleGothic')
else:  # 기타 (예: Linux)
    rc('font', family='NanumGothic')
def crawling_all():
    crawling_hello_mob()
    crawling_eyes()
    crawling_toss()
    crawling_tplus()
    save_all_data()
    preprocessing1()

    merge_csv_files()
    
def crawling_hello_mob():
    browser = webdriver.Chrome()
    company = '헬로모바일'
    telecom_list = ['KT', 'LGU', 'SKT']
    all_data = []
    
    # 각 통신사에 대해 데이터를 크롤링
    for telecom in telecom_list:
        url = f'https://direct.lghellovision.net/rate/rateView.do?pgNum=0301&tabLink=Y&rateGubun=U&telecomGubun={telecom}&menuGubun=LTE'
        browser.get(url)
            
        # 버튼 리스트 저장 (초기화 시 한 번만 실행)
        button_list = browser.find_elements(By.CSS_SELECTOR, 'div#rateCategory > a')
            
        # 버튼 클릭 처리
        for button_index, button in enumerate(button_list):
            button.click()  # 버튼 클릭
            time.sleep(1)   # 클릭 후 대기 (필요 시 페이지 로드 확인)
        
            # BeautifulSoup으로 현재 페이지 정보 파싱
            soup = BeautifulSoup(browser.page_source, "html.parser")
            one_data_list = soup.select("div.list > dl")
        
            for one_data in one_data_list:
                # 정보 추출
                title = one_data.select("p")[0].text
                data = one_data.select("li.data")[0].text
                call = one_data.select("li.call")[0].text
                message = one_data.select("li.message")[0].text
                
                # after_data_speed_element 처리
                after_data_speed_element = one_data.select("div.txt > p > span")
                discount_month = '없음'  # 기본값
                after_data_speed = '없음'  # 기본값
                
                # 값 분리 및 저장
                for element in after_data_speed_element:
                    text = element.text.strip()
                    if '개월' in text:  # 할인 기간 값인지 확인
                        discount_month = re.search(r'\d+개월', text).group()  # 예: "7개월"
                    elif '속도' in text or '최대' in text:  # 데이터 속도 관련 값인지 확인
                        after_data_speed = text
        
                # 데이터 정제 (after_data_speed: "최대 1Mbps 속도로 무제한" → "1Mbps")
                match = re.search(r'(\d+(?:\.\d+)?)(Kbps|Mbps)', after_data_speed)
                if match:
                    after_data_speed = f"{match.group(1)} {match.group(2)}"
                
                # price 값 추출
                price = one_data.select("strong")[0].text
                
                # 결과 저장
                one_list = [company, title, data, call, message, telecom, after_data_speed, discount_month, price]
                all_data.append(one_list)  # 데이터를 리스트에 추가
    
    # 브라우저 종료
    browser.close()
    
    # pandas DataFrame으로 변환
    columns = ['Company','Title', 'Data', 'Call', 'Message', 'Telecom', 'AfterDataSpeed', 'DiscountMonth', 'Price']
    df = pd.DataFrame(all_data, columns=columns)
    
    # CSV로 저장 (컬럼명을 정확히 지정)
    df.to_csv("./data/헬로모바일_data.csv", index=False, encoding="utf-8-sig")  # UTF-8-SIG로 저장하여 한글 깨짐 방지
def crawling_tplus():
    url = 'https://www.tplusmobile.com/main/rate/join'
    company = '티플러스'
    all_data = []
    browser = webdriver.Chrome()
    browser.get(url)
    time.sleep(3)  # 페이지 로딩 시간 충분히 확보
    
    for i in range(7):  # 7번 스크롤
        body = browser.find_elements('css selector', 'body')[0]
        body.send_keys(Keys.END)
        time.sleep(2)  # 스크롤 후 잠시 대기 (조금 더 시간을 늘려봄)
    
    # 페이지 소스 받아오기
    soup = BeautifulSoup(browser.page_source, "html.parser")
    one_data_list = soup.select("ul#result > li")
    
    # 데이터 추출
    for one_data in one_data_list:
        title = one_data.select("div.plan-name > p")[0].text
        data = one_data.select("p.plan-data")[0].text
        call = one_data.select("p.plan-call > span")[0].text
        message = one_data.select("p.plan-message > span")[0].text  # 'span'으로 수정
    
        # telecom 정보 추출
        if one_data.select('span.kt'):
            telecom = "KT"
        elif one_data.select('span.skt'):
            telecom = "SKT"
        elif one_data.select('span.lgu'):
            telecom = "LGU"
        else:
            telecom = "UNKNOWN"  # 기본값 설정
    
        # AfterDataSpeed 처리: "최대" 이후의 속도를 추출
        after_data_speed = "없음"  # 기본값 설정
        data_speed_match = re.search(r"최대\s*(\d+)(Mbps|Kbps)", data)
        if data_speed_match:
            after_data_speed = f"{data_speed_match.group(1)} {data_speed_match.group(2)}"
    
        # DiscountMonth 처리 (숫자 감소)
        discount_month_text = one_data.select("p.plan-af-price.light-gray")[0].text
        match = re.search(r"(\d+)개월", discount_month_text)
        if match:
            discount_month = f"{int(match.group(1)) - 1}개월"
        else:
            discount_month = "정보 없음"
    
        # 가격 정보 추출
        price = one_data.select("span.t-color")[0].text
    
        # 결과 저장
        one_list = [company, title, data, call, message, telecom, after_data_speed, discount_month, price]
        all_data.append(one_list)  # 데이터를 리스트에 추가
    
    # 브라우저 종료
    browser.quit()
    
    # pandas DataFrame으로 변환
    columns = ['Company', 'Title', 'Data', 'Call', 'Message', 'Telecom', 'AfterDataSpeed', 'DiscountMonth', 'Price']
    df = pd.DataFrame(all_data, columns=columns)
    
    # CSV로 저장 (컬럼명을 정확히 지정)
    df.to_csv("./data/티플러스_data.csv", index=False, encoding="utf-8-sig")  # UTF-8-SIG로 저장하여 한글 깨짐 방지ef crawling_eyes():
def crawling_eyes():
        # 브라우저 설정
    company = '아이즈모바일'
    all_data = []
    browser = webdriver.Chrome()
    
    for i in range(500):
        try:
            url = f'https://eyes.co.kr/payplan/info_view/{i}/C01'
            browser.get(url)
            time.sleep(1)  # 페이지 로딩 시간 확보
    
            # 경고창 확인 및 처리
            try:
                alert = Alert(browser)  # 경고창 접근
                alert_text = alert.text  # 경고창 메시지 확인
                if "판매가 중지된 상품입니다." in alert_text:
                    alert.accept()  # 경고창 닫기 (확인 버튼 클릭)
                    continue  # 다음 URL로 이동
                else:
                    alert.accept()  # 경고창 닫기 후 계속 진행
            except:
                pass  # 경고창이 없으면 무시하고 진행
    
            one_list = []
    
            # 페이지 소스 받아오기
            soup = BeautifulSoup(browser.page_source, "html.parser")
            title = soup.select("div.group > div.info-box > div.info > div.tit")[0].text.strip()
            data = soup.select("div.data > strong")[0].text.strip()
            call = soup.select("li.call > span")[0].text.strip()
            message = soup.select("li.sms > span")[0].text.strip()
            telecom = soup.select("button.tag.on")[0].text.strip()
            data_speed_list = soup.select('div.data > span')
            
            # 정규표현식을 사용하여 'Mps'로 시작하는 값 추출
            if len(data_speed_list) >= 1:
                after_data_speed = data_speed_list[0].text
                # 정규표현식으로 "5Mps속도제한 무제한"과 같은 값을 "5Mbps"로 변환
                after_data_speed = re.sub(r'(\d+)Mps.*', r'\1Mbps', after_data_speed)
            else:
                after_data_speed = '없음'
            
            # DiscountMonth 처리
            discount_month_list = soup.select("div.price > div.deco > p")
            if len(discount_month_list) == 0:
                discount_month = "없음"
            else:
                discount_text = discount_month_list[0].text.strip()
                # "첫 X개월"에서 숫자 추출
                match = re.search(r"(\d+)개월", discount_text)
                discount_month = f"{match.group(1)}개월" if match else "없음"
    
            # 가격 정보 추출 및 숫자 처리
            price_text = soup.select("div.price > strong")[0].text.strip()
            # "월 8,500원" → "8,500"
            price = re.sub(r"[^\d,]", "", price_text)
    
            # 데이터 저장
            one_list = [company, title, data, call, message, telecom, after_data_speed, discount_month, price]
            all_data.append(one_list)  # 데이터를 리스트에 추가
    
        except Exception as e:
            continue  # 오류 발생 시 다음 URL로 이동
    
    # 브라우저 종료
    browser.quit()
    
    # pandas DataFrame으로 변환
    columns = ['Company', 'Title', 'Data', 'Call', 'Message', 'Telecom', 'AfterDataSpeed', 'DiscountMonth', 'Price']
    df = pd.DataFrame(all_data, columns=columns)
    
    # CSV로 저장
    df.to_csv("./data/아이즈모바일_data.csv", index=False, encoding="utf-8-sig")  # UTF-8-SIG로 저장하여 한글 깨짐 방지
def crawling_toss():
    browser = webdriver.Chrome()
    company = '토스모바일'
    telecom_list = ['KT', 'LGU', 'SKT']
    all_data = []
    
    # 각 통신사에 대해 데이터를 크롤링
    for telecom in telecom_list:
        url = f'https://tossmobile.co.kr/pricing?carrier={telecom}'
        browser.get(url)
        time.sleep(1)
        
        # BeautifulSoup으로 현재 페이지 정보 파싱
        soup = BeautifulSoup(browser.page_source, "html.parser")
        one_data_list = soup.select("div.plan_item.css-1gruj5b.e1t6ugf32")
        
        for one_data in one_data_list:
            # 정보 추출
            title = one_data.select("span.typography.typography--h4.typography--bold.color--grey800.css-1tsvq0x")[0].text
            data = one_data.select("span.typography.typography--h5.typography--medium.color--grey700")[1].text
            call = one_data.select("span.typography.typography--h5.typography--medium.color--grey700")[2].text
            message = one_data.select("span.typography.typography--h5.typography--medium.color--grey700")[2].text
            
            discount_list = soup.select("div >.plan_item > span.typography.typography--h7.typography--medium.color--grey700")[0].text
            if len(discount_list) >= 1 :
                discount_month = discount_list[0]
                # 할인 개월 수 처리
                if discount_month.isdigit():  # 숫자인 경우
                    discount_month = f"{discount_month}개월"
                elif discount_month == "평":  # "평"인 경우
                    discount_month = "없음"
            else:
                discount_month = '없음'
    
            after_data_speed = "추후 변경"  # 기본값
            # 'Data'에서 속도 값 추출
            if "Mbps" in data:
                after_data_speed = re.search(r'(\d+Mbps)', data)
                if after_data_speed:
                    after_data_speed = after_data_speed.group(1)
            
            # Call과 Message에 값 설정
            if '무제한' in call or '무제한' in message:
                call = '기본제공'
                message = '기본제공'
            else:
                call_match = re.search(r'(\d+분)', call)
                message_match = re.search(r'(\d+건)', message)
                if call_match and message_match:
                    call = call_match.group(1) + '분'
                    message = message_match.group(1) + '건'
            
            # Price 값 추출 (원, 월 등의 문자 제거)
            price_text = one_data.select("span.typography.typography--h4.typography--bold.color--grey800 > span")[0].text
            price = re.sub(r'[^\d]', '', price_text)  # 숫자 이외의 문자 제거
            
            # 결과 저장
            one_list = [company, title, data, call, message, telecom, after_data_speed, discount_month, price]
            all_data.append(one_list)  # 데이터를 리스트에 추가
    
    # 브라우저 종료
    browser.close()
    
    # pandas DataFrame으로 변환
    columns = ['Company','Title', 'Data', 'Call', 'Message', 'Telecom', 'AfterDataSpeed', 'DiscountMonth', 'Price']
    df = pd.DataFrame(all_data, columns=columns)
    
    # CSV로 저장 (컬럼명을 정확히 지정)
    df.to_csv("./data/토스모바일_data.csv", index=False, encoding="utf-8-sig")  # UTF-8-SIG로 저장하여 한글 깨짐 방지
def merge_csv_files():
    existing_file = "알뜰폰_data.csv"
    all_files = [f for f in os.listdir('./data/') if f.endswith('.csv') and f != existing_file]
    combined_df = pd.DataFrame()  # 결과를 저장할 빈 DataFrame 생성
    
    for file in all_files:
        file_path = os.path.join('./data/', file)  # 파일 경로 생성
        df = pd.read_csv(file_path)  # CSV 파일 읽기
        combined_df = pd.concat([combined_df, df], ignore_index=True)  # DataFrame 합치기
    
    return combined_df


directory = './data/'
merged_data = merge_csv_files()
def preprocessing1():
    # 정규표현식으로 숫자와 Mbps만 추출하여 값을 변경
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace(r'(\d+)Mps.*', r'\1Mbps', regex=True)
    # 'Call' 열의 값이 '음성기본제공'이면 '기본제공'으로 변경
    merged_data['Call'] = merged_data['Call'].replace('음성기본제공', '기본제공')
    merged_data['Telecom'] = merged_data['Telecom'].replace('LGU+', 'LGU')
    # 'Call' 열의 값이 '-'이면 '0분'으로 변경
    merged_data['Call'] = merged_data['Call'].replace('-', '0분')
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace({'1 Mbps': '1Mbps', '3 Mbps': '3Mbps', '5 Mbps': '5Mbps'})

    # 'Message' 열의 값이 '-'이면 '0건'으로 변경
    merged_data['Message'] = merged_data['Message'].replace('-', '0건')
    
    # 'AfterDataSpeed' 열의 값이 '3Mbps속도제한'이면 '3 Mbps'으로 변경
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace('3Mbps속도제한', '3Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '1Mbps속도제한'이면 '1 Mbps'으로 변경
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace('1Mbps속도제한', '1Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '5Mbps속도제한'이면 '5 Mbps'으로 변경
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace('5Mbps속도제한', '5Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '400Kbps속도제한'이면 '400Kbps'으로 변경
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace('400Kbps속도제한', '400Kbps')
    
    # 'AfterDataSpeed' 열의 값이 '3Mbps속도제한'이면 '3 Mbps'으로 변경
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace('3Mbps속도제한 무제한', '3Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '1Mbps속도제한'이면 '1 Mbps'으로 변경
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace('1Mbps속도제한 무제한', '1Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '5Mbps속도제한'이면 '5 Mbps'으로 변경
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace('5Mbps속도제한 무제한', '5Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '400Kbps속도제한'이면 '400Kbps'으로 변경
    merged_data['AfterDataSpeed'] = merged_data['AfterDataSpeed'].replace('400Kbps속도제한 무제한', '400Kbps')
def save_all_data():
    # 파일명을 "오늘 날짜 알뜰폰 data"로 지정
    file_name = "./data/알뜰폰_data.csv"
    
    # raw DataFrame을 CSV로 저장
    merged_data.to_csv(file_name, index=False, encoding="utf-8-sig")






def preprocessing(raw):
    # 'Price' 열의 값에서 쉼표(,) 제거 후 숫자로 변환
    raw['Price'] = raw['Price'].str.replace(',', '').astype(float)  # 먼저 float로 변환
    raw = raw.dropna(subset=['Price'])  # 'Price' 열에서 NaN 값이 있는 행 제거
    raw['Price'] = raw['Price'].astype(int)  # 나머지 값들을 int로 변환

    # 'DiscountMonth' 열에서 '정보 없음'을 '없음'으로 변경
    raw['DiscountMonth'] = raw['DiscountMonth'].replace('정보 없음', '없음')
    
    # 'AfterDataSpeed' 열에서 NaN 값을 '없음'으로 변경
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].fillna('없음')
    
    # 'Data' 열에서 숫자와 단위를 분리하여 GB로 변환
    def convert_to_gb(data):
        # 'Data' 값이 비어 있거나 숫자가 없으면 None 반환
        if not data or not isinstance(data, str):
            return 0
        
        # 숫자 추출
        numbers = re.findall(r'\d+', data)
        if not numbers:
            return 0  # 숫자가 없으면 0 반환
        
        num = int(numbers[0])  # 숫자 추출
        if 'MB' in data:
            return num / 1000  # MB -> GB
        elif 'GB' in data:
            return num  # 이미 GB 단위
        return 0  # 값이 없거나 예상되지 않는 형식일 경우 0
    
    raw['Data_GB'] = raw['Data'].apply(convert_to_gb)

    # 'Message' 열에서 '20,000윙'은 제거하고 '100건건'은 '100건'으로 처리
    def clean_message(message):
        # '20,000윙' 제거
        message = message.replace('윙', '').replace(',', '').strip()
        
        # '100건건'을 '100건'으로 변경
        message = re.sub(r'(\d+)건건', r'\1건', message)
        
        # 'Message' 값이 10000 이상이면 None 처리
        if isinstance(message, str) and any(char.isdigit() for char in message):
            num = int(re.search(r'\d+', message).group())
            if num >= 10000:
                return None
        return message

    raw['Message'] = raw['Message'].apply(clean_message)

    # 'Call' 열에서 '윙'을 제거하고 '10000' 이상인 값을 삭제 및 '100분분'을 '100분'으로 수정
    def clean_call(call):
        if isinstance(call, str):
            # '10000' 이상인 값은 None으로 처리
            if call.isdigit() and int(call) >= 10000:
                return None  # 해당 값은 None으로 처리하여 삭제하도록 함

            # '윙'과 ',' 제거
            call = call.replace('윙', '').replace(',', '').strip()

            # '100분분'을 '100분'으로 변경
            call = call.replace('분분', '분')

        return call
    
    raw['Call'] = raw['Call'].apply(clean_call)
    
    # 'Call' 열에서 None 값을 삭제
    raw = raw.dropna(subset=['Call'])
    
    # 'Message' 열에서 None 값을 삭제
    raw = raw.dropna(subset=['Message'])

    # merged_data에서 'AfterDataSpeed' 열의 값 정리
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].replace(r'(\d+)Mps.*', r'\1Mbps', regex=True)
    raw['Call'] = raw['Call'].replace('음성기본제공', '기본제공')
    raw['Call'] = raw['Call'].replace('-', '0분')
    raw['Message'] = raw['Message'].replace('-', '0건')
    
    # 'AfterDataSpeed' 열의 값이 '3Mbps속도제한'이면 '3 Mbps'으로 변경
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].replace('3Mbps속도제한', '3Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '1Mbps속도제한'이면 '1 Mbps'으로 변경
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].replace('1Mbps속도제한', '1Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '5Mbps속도제한'이면 '5 Mbps'으로 변경
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].replace('5Mbps속도제한', '5Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '400Kbps속도제한'이면 '400Kbps'으로 변경
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].replace('400Kbps속도제한', '400Kbps')
    
    # 'AfterDataSpeed' 열의 값이 '3Mbps속도제한 무제한'이면 '3 Mbps'으로 변경
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].replace('3Mbps속도제한 무제한', '3Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '1Mbps속도제한 무제한'이면 '1 Mbps'으로 변경
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].replace('1Mbps속도제한 무제한', '1Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '5Mbps속도제한 무제한'이면 '5 Mbps'으로 변경
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].replace('5Mbps속도제한 무제한', '5Mbps')
    
    # 'AfterDataSpeed' 열의 값이 '400Kbps속도제한 무제한'이면 '400Kbps'으로 변경
    raw['AfterDataSpeed'] = raw['AfterDataSpeed'].replace('400Kbps속도제한 무제한', '400Kbps')

    return raw

def read_data():
    # 데이터 읽기
    raw = pd.read_csv("./data/알뜰폰_data.csv")
    return raw

# 데이터 로드
raw = read_data()
raw = preprocessing(raw)
preprocessing1()
# 크롤링 버튼 추가
if st.sidebar.button('티플러스 크롤링 시작'):
    crawling_tplus()


if st.sidebar.button('토스모바일 크롤링 시작'):
    crawling_toss()

if st.sidebar.button('헬로모바일 크롤링 시작'):
    crawling_hello_mob()

if st.sidebar.button('아이즈모바일 크롤링 시작'):
    crawling_eyes()


if st.sidebar.button('크롤링한 데이터 합치고 저장하기'):
    directory = './data/'
    merged_data = merge_csv_files()
    preprocessing1()
    save_all_data()
    raw = read_data()
    raw = preprocessing(raw)

# 사이드바 구성
st.sidebar.header("요금제 검색 옵션")

# 가격 필터 추가 (슬라이더)
min_price, max_price = st.sidebar.slider(
    "가격 범위를 선택하세요 (원)",
    min_value=int(raw['Price'].min()),
    max_value=int(raw['Price'].max()),
    value=(int(raw['Price'].min()), int(raw['Price'].max()))
)

# 데이터 용량 슬라이더 추가
min_data, max_data = st.sidebar.slider(
    "데이터 용량 범위를 선택하세요 (GB)",
    min_value=int(raw['Data_GB'].min()),
    max_value=int(raw['Data_GB'].max()),
    value=(int(raw['Data_GB'].min()), int(raw['Data_GB'].max()))
)

# 'Call' 열 필터 추가
selected_call = st.sidebar.multiselect(
    "통화 요금 범위를 선택하세요",
    options=raw['Call'].unique(),
    default=raw['Call'].unique()
)

# 필터 옵션 추가
selected_company = st.sidebar.multiselect(
    "회사를 선택하세요",
    options=raw['Company'].unique(),
    default=raw['Company'].unique()
)

selected_message = st.sidebar.multiselect(
    "메시지량을 선택하세요",
    options=raw['Message'].unique(),
    default=raw['Message'].unique()
)

selected_telecom = st.sidebar.multiselect(
    "통신사를 선택하세요",
    options=raw['Telecom'].unique(),
    default=raw['Telecom'].unique()
)

selected_speed = st.sidebar.multiselect(
    "데이터 사용 후 속도를 선택하세요",
    options=raw['AfterDataSpeed'].unique(),
    default=raw['AfterDataSpeed'].unique()
)

selected_discount = st.sidebar.multiselect(
    "할인 기간을 선택하세요",
    options=raw['DiscountMonth'].unique(),
    default=raw['DiscountMonth'].unique()
)


# 필터링
filtered_data = raw[
    (raw['Company'].isin(selected_company)) &
    (raw['Message'].isin(selected_message)) &
    (raw['Telecom'].isin(selected_telecom)) &
    (raw['AfterDataSpeed'].isin(selected_speed)) &
    (raw['DiscountMonth'].isin(selected_discount)) &
    (raw['Price'].between(min_price, max_price)) &
    (raw['Data_GB'].between(min_data, max_data)) &
    (raw['Call'].isin(selected_call))  # 'Call' 열 필터링
]


# 초기 상태 설정
if 'current_page' not in st.session_state:
    st.session_state.current_page = "default" 

if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False

# 페이지 이동 함수
def toggle_admin_mode():
    st.session_state.current_page = "admin_mode"
    st.session_state.admin_mode = True

def toggle_readme():
    st.session_state.current_page = "readme"
    st.session_state.admin_mode = False

# 사이드바 버튼 추가
st.sidebar.button('관리자 모드', on_click=toggle_admin_mode)
st.sidebar.button('프로젝트 소개', on_click=toggle_readme)

# 페이지에 따라 내용 표시
if st.session_state.current_page == "default":
    st.write("### 기본 페이지")
    st.dataframe(filtered_data)

elif st.session_state.current_page == "admin_mode":
    st.write("### 관리자 모드")
    if st.session_state.admin_mode:
       
        st.write("#### 필터링된 데이터프레임")
        st.dataframe(filtered_data)
        
        # 필터링된 데이터를 카운트하여 시각화할 데이터 준비
        def count_filtered_values(column, selected_values):
            return {value: filtered_data[filtered_data[column] == value].shape[0] for value in selected_values}
        
        # 각 필터링된 옵션 값들의 갯수를 계산
        call_count = count_filtered_values('Call', selected_call)
        message_count = count_filtered_values('Message', selected_message)
        company_count = count_filtered_values('Company', selected_company)
        telecom_count = count_filtered_values('Telecom', selected_telecom)
        speed_count = count_filtered_values('AfterDataSpeed', selected_speed)
        discount_count = count_filtered_values('DiscountMonth', selected_discount)

        # 카운트 데이터를 바탕으로 그래프 그리기
        def plot_count(count_data, title):
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(count_data.keys(), count_data.values())
            ax.set_title(title)
            plt.xticks(rotation=45)  # X축 라벨 회전
            st.pyplot(fig)

        plot_count(call_count, "통화 요금별 필터링된 데이터")
        plot_count(message_count, "메시지량별 필터링된 데이터")
        plot_count(company_count, "회사별 필터링된 데이터")
        plot_count(telecom_count, "통신사별 필터링된 데이터")
        plot_count(speed_count, "속도별 필터링된 데이터")
        plot_count(discount_count, "할인기간별 필터링된 데이터")

        # 제목 데이터 분석 - 단어 분리 및 등장 횟수 계산
        title_column = filtered_data['Title']
        all_words = []

        for title in title_column.dropna():
            words = title.split()  # 띄어쓰기 기준으로 단어 분리
            all_words.extend(words)

        word_count = Counter(all_words)  # 단어별 등장 횟수 계산
        word_count_data = pd.DataFrame(word_count.items(), columns=['Word', 'Count']).sort_values(by='Count', ascending=False)

        st.write("### 제목 단어 분석")
        st.dataframe(word_count_data)

    else:
        st.write("#### 관리자 모드 비활성화됨")
        st.write("그래프를 보려면 관리자 모드를 활성화하세요.")

elif st.session_state.current_page == "readme":
    st.write("# 프로젝트 소개")

    # README.md 파일 읽어서 표시
    readme_file = "readme.md"  # README 파일 경로
    if os.path.exists(readme_file):
        with open(readme_file, "r", encoding="utf-8") as file:
            st.markdown(file.read())
    else:
        st.error("README.md 파일을 찾을 수 없습니다.")



