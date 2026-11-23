
import streamlit as st
import sqlite3
import os
import uuid
from datetime import date

st.set_page_config(page_title="보드게임 대여 관리",page_icon="🎲",layout="wide")

DB="boardgames.db"
IMAGE_DIR="images"
os.makedirs(IMAGE_DIR,exist_ok=True)

st.markdown("""
<style>
.stApp{background:#F4F6FA;color:#202B3C}
header[data-testid="stHeader"]{background:transparent}
h1,h2,h3,p,label,span,div{font-family:"Malgun Gothic","Apple SD Gothic Neo",sans-serif}
h1{color:#172B4D!important;font-size:2.25rem!important;font-weight:800!important}
h2,h3{color:#203858!important;font-weight:750!important}
p,label{color:#26364A}
small{color:#526174}
.stButton button{background:#2563EB;color:white;border:0;border-radius:9px;font-weight:700;min-height:40px;transition:.2s}
.stButton button:hover{background:#1D4ED8;color:white;transform:translateY(-1px)}
.stTextInput input,.stDateInput input{border:1px solid #CBD5E1;border-radius:8px;background:white;color:#172B4D}
.stSelectbox div[data-baseweb="select"]{background:white;border-radius:8px}
div[data-testid="stMetric"]{background:white;border:1px solid #E2E8F0;border-left:5px solid #2563EB;border-radius:12px;padding:17px;box-shadow:0 2px 7px #172b4d0d}
div[data-testid="stMetricLabel"]{color:#526174;font-weight:700}
div[data-testid="stMetricValue"]{color:#172B4D;font-weight:800}
div[data-testid="stExpander"]{background:white;border:1px solid #DCE3ED;border-radius:10px}
div[data-testid="stFileUploader"]{background:white;border:1px dashed #94A3B8;border-radius:10px;padding:10px}
hr{border-color:#DCE3ED}
.game-card{background:white;border:1px solid #DCE3ED;border-radius:12px;padding:15px;margin-bottom:10px;box-shadow:0 3px 9px #172b4d0b}
.game-title{font-size:21px;font-weight:800;color:#172B4D;margin:9px 0}
.status-available{display:inline-block;background:#DCFCE7;color:#166534;padding:5px 11px;border-radius:6px;font-size:13px;font-weight:800}
.status-rented{display:inline-block;background:#FFEDD5;color:#9A3412;padding:5px 11px;border-radius:6px;font-size:13px;font-weight:800}
.top-banner{background:#172B4D;border-radius:13px;padding:22px 25px;color:white;margin-bottom:20px}
.top-banner h1{color:white!important;margin:0}
.top-banner p{color:#DCE8F8;margin:6px 0 0}
.section-label{font-size:13px;font-weight:800;color:#64748B;letter-spacing:1px}
</style>
""",unsafe_allow_html=True)

def connect():
    return sqlite3.connect(DB)

def init_db():
    with connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS games(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT,
            borrower TEXT DEFAULT '',
            status TEXT DEFAULT '대여 가능',
            rental_date TEXT,
            return_date TEXT
        )
        """)

def get_games():
    with connect() as conn:
        return conn.execute("SELECT * FROM games ORDER BY id DESC").fetchall()

def add_game(name,image):
    with connect() as conn:
        conn.execute("INSERT INTO games(name,image) VALUES(?,?)",(name,image))

def update_game(game_id,name,image,borrower,status,rental_date,return_date):
    with connect() as conn:
        conn.execute("""
        UPDATE games SET name=?,image=?,borrower=?,status=?,rental_date=?,return_date=?
        WHERE id=?
        """,(name,image,borrower,status,rental_date,return_date,game_id))

def delete_game(game_id):
    with connect() as conn:
        row=conn.execute("SELECT image FROM games WHERE id=?",(game_id,)).fetchone()
        conn.execute("DELETE FROM games WHERE id=?",(game_id,))
    if row and row[0] and os.path.isfile(row[0]):
        os.remove(row[0])

def save_image(uploaded_file):
    if uploaded_file is None:
        return None
    ext=os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in [".jpg",".jpeg",".png",".webp"]:
        st.error("JPG, PNG, WEBP 형식의 사진만 업로드할 수 있어요.")
        return None
    filename=f"{uuid.uuid4().hex}{ext}"
    path=os.path.join(IMAGE_DIR,filename)
    with open(path,"wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def valid_image(path):
    return bool(path and os.path.isfile(path))

init_db()

st.markdown("""
<div class="top-banner">
<h1>🎲 BOARD GAME MANAGER</h1>
<p>우리 학교 보드게임 대여 현황을 한눈에 관리하세요.</p>
</div>
""",unsafe_allow_html=True)

games=get_games()
total=len(games)
rented=sum(1 for g in games if g[4]=="대여 중")
available=total-rented

m1,m2,m3=st.columns(3)
m1.metric("🎲 전체 보드게임",f"{total}개")
m2.metric("🟠 대여 중",f"{rented}개")
m3.metric("🟢 대여 가능",f"{available}개")

st.divider()

tab1,tab2=st.tabs(["📋 보드게임 관리","➕ 보드게임 등록"])

with tab1:
    st.subheader("보드게임 목록")
    st.caption("등록된 보드게임의 정보와 대여 현황을 관리할 수 있습니다.")
    c1,c2=st.columns([2,1])
    with c1:
        search=st.text_input("🔎 보드게임 검색",placeholder="게임 이름을 입력하세요")
    with c2:
        filter_status=st.selectbox("대여 상태",["전체","대여 가능","대여 중"])

    filtered=[]
    for g in games:
        if search.lower() not in g[1].lower():
            continue
        if filter_status!="전체" and g[4]!=filter_status:
            continue
        filtered.append(g)

    st.markdown(f'<p class="section-label">검색 결과 {len(filtered)}개</p>',unsafe_allow_html=True)

    if not filtered:
        st.info("등록된 보드게임이 없습니다. 새 보드게임을 등록해 주세요.")
    else:
        for i in range(0,len(filtered),2):
            cols=st.columns(2)
            for j in range(2):
                if i+j>=len(filtered):
                    break
                g=filtered[i+j]
                game_id,name,image,borrower,status,rental_date,return_date=g
                with cols[j]:
                    st.markdown('<div class="game-card">',unsafe_allow_html=True)
                    if valid_image(image):
                        st.image(image,use_container_width=True)
                    else:
                        st.markdown("### 🎲")
                        st.caption("등록된 사진이 없습니다.")
                    st.markdown(f'<div class="game-title">{name}</div>',unsafe_allow_html=True)
                    if status=="대여 중":
                        st.markdown('<span class="status-rented">● 대여 중</span>',unsafe_allow_html=True)
                        st.write(f"**대여자:** {borrower or '미입력'}")
                        st.write(f"**대여일:** {rental_date or '-'}")
                        st.write(f"**반납 예정일:** {return_date or '-'}")
                    else:
                        st.markdown('<span class="status-available">● 대여 가능</span>',unsafe_allow_html=True)
                    st.markdown('</div>',unsafe_allow_html=True)

                    with st.expander("✏️ 게임 정보 수정"):
                        new_name=st.text_input("보드게임 이름",value=name,key=f"name_{game_id}")
                        new_image_file=st.file_uploader("사진 변경",type=["jpg","jpeg","png","webp"],key=f"image_{game_id}")
                        new_status=st.selectbox("대여 상태",["대여 가능","대여 중"],index=0 if status=="대여 가능" else 1,key=f"status_{game_id}")
                        new_borrower=""
                        new_rental=None
                        new_return=None
                        if new_status=="대여 중":
                            new_borrower=st.text_input("대여자 이름",value=borrower or "",key=f"borrower_{game_id}")
                            try:
                                old_rental=date.fromisoformat(rental_date) if rental_date else date.today()
                            except ValueError:
                                old_rental=date.today()
                            try:
                                old_return=date.fromisoformat(return_date) if return_date else date.today()
                            except ValueError:
                                old_return=date.today()
                            new_rental=st.date_input("대여일",value=old_rental,key=f"rental_{game_id}")
                            new_return=st.date_input("반납 예정일",value=old_return,key=f"return_{game_id}")

                        if st.button("💾 수정 내용 저장",key=f"save_{game_id}",use_container_width=True):
                            if not new_name.strip():
                                st.error("게임 이름을 입력해 주세요.")
                            elif new_status=="대여 중" and not new_borrower.strip():
                                st.error("대여자 이름을 입력해 주세요.")
                            elif new_status=="대여 중" and new_return<new_rental:
                                st.error("반납 예정일은 대여일보다 빠를 수 없습니다.")
                            else:
                                new_image=image
                                if new_image_file:
                                    saved=save_image(new_image_file)
                                    if saved:
                                        new_image=saved
                                        if valid_image(image):
                                            os.remove(image)
                                    else:
                                        st.stop()
                                update_game(game_id,new_name.strip(),new_image,new_borrower.strip() if new_status=="대여 중" else "",new_status,new_rental.isoformat() if new_rental else None,new_return.isoformat() if new_return else None,game_id)
                                st.success("수정 내용이 저장되었습니다.")
                                st.rerun()

                    with st.expander("🗑️ 보드게임 삭제"):
                        st.warning("삭제하면 해당 보드게임의 정보와 사진이 함께 삭제됩니다.")
                        if st.button("이 보드게임 삭제하기",key=f"delete_{game_id}",use_container_width=True):
                            delete_game(game_id)
                            st.success("삭제되었습니다.")
                            st.rerun()

with tab2:
    st.subheader("새 보드게임 등록")
    st.caption("새롭게 발견한 보드게임을 관리 목록에 추가하세요.")
    with st.form("add_game_form",clear_on_submit=True):
        name=st.text_input("🎲 보드게임 이름",placeholder="예: 루미큐브")
        image_file=st.file_uploader("📸 보드게임 사진 업로드",type=["jpg","jpeg","png","webp"])
        submitted=st.form_submit_button("➕ 보드게임 등록하기",use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("보드게임 이름을 입력해 주세요.")
            else:
                image=save_image(image_file) if image_file else None
                if image_file and not image:
                    st.error("사진을 다시 확인해 주세요.")
                else:
                    add_game(name.strip(),image)
                    st.success(f"{name} 등록 완료!")
                    st.rerun()

st.divider()
st.markdown("""
<div style="text-align:center;color:#64748B;padding:12px;font-size:13px">
BOARD GAME MANAGER · 신나는 보드게임, 체계적인 관리 🎲
</div>
""",unsafe_allow_html=True)
