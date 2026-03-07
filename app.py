import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os

# --- 1. 설정 및 구글 연결 ---
# [수정됨] page_icon에 로고 파일 경로를 넣어 브라우저 탭 아이콘을 변경합니다.
current_dir = os.path.dirname(__file__)
logo_path = os.path.join(current_dir, "logo.png")

st.set_page_config(
    page_title="심인고등학교 자습실 예약 시스템", 
    page_icon=logo_path if os.path.exists(logo_path) else "🏫", 
    layout="centered"
)

ADMIN_PASSWORD = "admin1234" 

def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("secrets.json", scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("자습실 좌석 예약")
        return spreadsheet.get_worksheet(0)
    except Exception as e:
        st.error(f"연결 실패: {e}")
        return None

sheet = connect_to_sheet()

# --- 2. 데이터 처리 함수 ---
def fetch_data():
    if sheet:
        return pd.DataFrame(sheet.get_all_records())
    return pd.DataFrame()

def update_seat(seat_id, status, sid="", name=""):
    cell = sheet.find(str(seat_id))
    sheet.update_cell(cell.row, 2, status)
    sheet.update_cell(cell.row, 3, sid)
    sheet.update_cell(cell.row, 4, name)

# --- 3. 세션 상태 및 화면 관리 ---
if 'view' not in st.session_state:
    st.session_state.view = "MAIN"
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'sel_id' not in st.session_state:
    st.session_state.sel_id = None

def go_to(page):
    st.session_state.view = page
    st.rerun()

def check_admin():
    if st.session_state.pw_field == ADMIN_PASSWORD:
        st.session_state.is_admin = True
        st.toast("관리자 인증 성공!")
    elif st.session_state.pw_field != "":
        st.session_state.is_admin = False
        st.sidebar.error("비밀번호가 틀립니다.")

def logout():
    st.session_state.is_admin = False
    st.session_state.view = "MAIN" 
    if "pw_field" in st.session_state:
        st.session_state.pw_field = ""
    st.rerun()

# --- 4. UI 구성 ---
if sheet:
    df = fetch_data()

    # == 사이드바: 관리자 설정 ==
    with st.sidebar:
        st.title("관리자 설정")
        if not st.session_state.is_admin:
            st.text_input("비밀번호 입력", type="password", key="pw_field", on_change=check_admin)
            if st.button("🔓 관리자 인증하기", use_container_width=True):
                check_admin()
                st.rerun()
        else:
            st.success("관리자 모드 활성")
            if st.button("🔒 관리자 모드 해제", use_container_width=True):
                logout()

    # ======= [화면 1] 메인 좌석 목록 =======
    if st.session_state.view == "MAIN":
        col_logo, col_title = st.columns([0.12, 0.88])
        with col_logo:
            if os.path.exists(logo_path):
                st.markdown('<div style="margin-top: 18px;">', unsafe_allow_html=True)
                st.image(logo_path, width=65)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("<h1 style='font-size:40px; margin:15px 0 0 0;'>⬢</h1>", unsafe_allow_html=True)

        with col_title:
            st.markdown("""
                <div style="margin-left: -15px; padding-top: 15px;">
                    <p style='font-size:16px; color:#1e3a8a; font-weight:700; margin-bottom: -12px; letter-spacing:-0.5px;'>심인고등학교</p>
                    <h1 style='font-size:36px; font-weight:900; color:#111827; letter-spacing:-1.5px; margin-top: 0; line-height: 1.1;'>자습실 예약 시스템</h1>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style="background-color: #fff9db; padding: 15px; border-left: 5px solid #fcc419; border-radius: 4px; margin: 15px 0 25px 0;">
                <span style="font-weight: bold; color: #856404;"> 이용 수칙:</span> 
                <span style="color: #856404;">반드시 본인의 좌석을 예약한 후 이용해 주세요.</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("좌석 선택")
        st.divider()

        for i in range(0, 14, 2):
            c1, c2 = st.columns(2)
            for idx, col in enumerate([c1, c2]):
                curr = i + idx
                if curr < len(df):
                    row = df.iloc[curr]
                    sid_id = str(row['좌석'])
                    status = str(row['상태'])
                    
                    if status == "이용 중":
                        label = f"🔴 {sid_id}번 [{row['학번']} {row['이름']}]" if st.session_state.is_admin else f"🔴 {sid_id}번 (이용 중)"
                        b_type = "primary"
                    else:
                        label = f"🟢 {sid_id}번 (이용 가능)"
                        b_type = "secondary"

                    if col.button(label, key=f"btn_{sid_id}", use_container_width=True, type=b_type):
                        st.session_state.sel_id = sid_id
                        go_to("DETAILS")

    # ======= [화면 2] 예약 및 퇴실 상세 =======
    elif st.session_state.view == "DETAILS":
        if st.session_state.sel_id is None:
            go_to("MAIN")
        
        target_id = st.session_state.sel_id
        df_target = df[df['좌석'].astype(str) == str(target_id)]
        
        if df_target.empty:
            go_to("MAIN")
        else:
            target_row = df_target.iloc[0]
            st.title(f" {target_id}번 좌석 상세")
            if st.button("⬅️ 돌아가기"):
                go_to("MAIN")
            st.write("---")

            if target_row['상태'] != "이용 중":
                st.subheader("입실 신청")
                with st.form("in_form"):
                    new_sid = st.text_input("학번 (예: 10101)")
                    new_name = st.text_input("이름")
                    if st.form_submit_button("좌석 예약 확정", use_container_width=True):
                        if new_sid and new_name:
                            update_seat(target_id, "이용 중", new_sid, new_name)
                            st.toast("예약 완료!")
                            go_to("MAIN")
                        else:
                            st.warning("정보를 입력하세요.")
            else:
                st.subheader("퇴실 안내")
                st.error("주의: 타인의 좌석을 무단으로 퇴실 처리하지 마세요.")
                
                if st.session_state.is_admin:
                    st.info(f"현재 이용자: **{target_row['학번']} {target_row['이름']}**")
                else:
                    name = str(target_row['이름'])
                    masked_name = name[0] + "*" + name[-1] if len(name) >= 3 else name[0] + "*" if len(name) == 2 else name
                    st.info(f"현재 이용자: **{masked_name}** 학생 (이용 중)")
                
                if st.button("퇴실하기", type="primary", use_container_width=True):
                    update_seat(target_id, "이용 가능", "", "")
                    st.toast("퇴실 완료!")
                    go_to("MAIN")

st.markdown("<br><br><center style='color:gray; font-size:12px;'>심인고등학교 자습실 관리 시스템</center>", unsafe_allow_html=True)