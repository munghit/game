
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
.stApp{background:#111827;color:#F9FAFB}
header[data-testid="stHeader"]{background:transparent}
h1,h2,h3{color:#F9FAFB!important;font-weight:800!important}
p,label{color:#E5E7EB}
.stButton button{background:#3B82F6;color:white;border:1px solid #3B82F6;border-radius:16px;font-weight:700;min-height:43px;transition:.2s}
.stButton button:hover{background:#2563EB;color:white;border-color:#60A5FA;transform:translateY(-1px)}
.stTextInput input,.stDateInput input{background:#1F2937;color:#F9FAFB;border:1px solid #475569;border-radius:14px;min-height:42px}
.stSelectbox div[data-baseweb="select"]{background:#1F2937;color:#F9FAFB;border-radius:14px}
div[data-testid="stMetric"]{background:#1F2937;border:1px solid #374151;border-left:4px solid #3B82F6;border-radius:20px;padding:18px}
div[data-testid="stMetricLabel"]{color:#9CA3AF}
div[data-testid="stMetricValue"]{color:#F9FAFB}
div[data-testid="stExpander"]{background:#1F2937;border:1px solid #374151;border-radius:18px}
div[data-testid="stFileUploader"]{background:#1F2937;border:1px dashed #64748B;border-radius:18px;padding:12px}
div[data-testid="stForm"]{background:#1F2937;border:1px solid #374151;border-radius:18px;padding:17px}
hr{border-color:#374151}
.top-banner{background:linear-gradient(120deg,#172554,#1E3A8A,#1F2937);border:1px solid #334155;border-radius:24px;padding:25px 28px;margin-bottom:22px}
.top-banner h1{color:white!important;margin:0}
.top-banner p{color:#BFDBFE;margin:7px 0 0}
.game-title{font-size:22px;font-weight:800;color:#F9FAFB;margin:12px 0}
.status-available{display:inline-block;background:#14532D;color:#86EFAC;padding:7px 13px;border-radius:20px;font-size:13px;font-weight:800}
.status-rented{display:inline-block;background:#78350F;color:#FDE68A;padding:7px 13px;border-radius:20px;font-size:13px;font-weight:800}
.section-label{font-size:13px;font-weight:800;color:#94A3B8;letter-spacing:1px}
.stTabs [data-baseweb="tab-list"]{gap:9px}
.stTabs [data-baseweb="tab"]{background:#1F2937;border-radius:15px;color:#D1D5DB;padding:11px 17px}
.stTabs [aria-selected="true"]{background:#1D4ED8!important;color:white!important}
[data-testid="stMarkdownContainer"]{color:#E5E7EB}
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:22px!important;border-color:#374151!important;background:#1F2937}
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

def update_rental(game_id,borrower,status,rental_date,return_date):
    with connect() as conn:
        conn.execute("""
        UPDATE games
        SET borrower=?,status=?,rental_date=?,return_date=?
        WHERE id=?
        """,(borrower,status,rental_date,return_date,game_id))

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
    st.caption("보드게임을 선택해 대여하거나 반납할 수 있습니다.")

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
        st.info("등록된 보드게임이 없거나 검색 결과가 없어요. 🎲")
    else:
        for i in range(0,len(filtered),2):
            cols=st.columns(2)
            for j in range(2):
                if i+j>=len(filtered):
                    break

                g=filtered[i+j]
                game_id,name,image,borrower,status,rental_date,return_date=g

                with cols[j]:
                    with st.container(border=True):
                        if valid_image(image):
                            st.image(image,use_container_width=True)
                        else:
                            st.markdown("### 🎲 사진이 아직 없어요")

                        st.markdown(f'<div class="game-title">{name}</div>',unsafe_allow_html=True)

                        if status=="대여 중":
                            st.markdown('<span class="status-rented">● 대여 중</span>',unsafe_allow_html=True)
                            st.write(f"👤 **대여자:** {borrower or '미입력'}")
                            st.write(f"📅 **대여일:** {rental_date or '-'}")
                            st.write(f"🏁 **반납 예정일:** {return_date or '-'}")

                            if st.button("↩️ 반납 처리",key=f"return_{game_id}",use_container_width=True):
                                update_rental(game_id,"","대여 가능",None,None)
                                st.success("반납 처리가 완료되었어요!")
                                st.rerun()

                        else:
                            st.markdown('<span class="status-available">● 대여 가능</span>',unsafe_allow_html=True)

                            with st.expander("🎉 대여하기"):
                                with st.form(f"rental_form_{game_id}"):
                                    new_borrower=st.text_input("👤 대여자 이름",placeholder="대여하는 사람의 이름")
                                    new_rental=st.date_input("📅 대여일",value=date.today())
                                    new_return=st.date_input("🏁 반납 예정일",value=date.today())

                                    submitted=st.form_submit_button("대여 정보 저장하기",use_container_width=True)

                                    if submitted:
                                        if not new_borrower.strip():
                                            st.error("대여자 이름을 입력해 주세요.")
                                        elif new_return<new_rental:
                                            st.error("반납 예정일은 대여일보다 빠를 수 없어요.")
                                        else:
                                            update_rental(
                                                game_id,
                                                new_borrower.strip(),
                                                "대여 중",
                                                new_rental.isoformat(),
                                                new_return.isoformat()
                                            )
                                            st.success("대여 처리가 완료되었어요!")
                                            st.rerun()

                        with st.expander("🗑️ 보드게임 삭제"):
                            st.warning("삭제하면 해당 보드게임과 대여 정보가 함께 삭제됩니다.")
                            if st.button("이 보드게임 삭제하기",key=f"delete_{game_id}",use_container_width=True):
                                delete_game(game_id)
                                st.success("삭제되었어요.")
                                st.rerun()

with tab2:
    st.subheader("🎁 새로운 보드게임 등록")
    st.write("새로운 보드게임을 발견했다면 여기에 등록해 주세요!")

    with st.form("add_game_form",clear_on_submit=True):
        name=st.text_input("🎲 보드게임 이름",placeholder="예: 루미큐브")
        image_file=st.file_uploader("📸 보드게임 사진 업로드",type=["jpg","jpeg","png","webp"])
        submitted=st.form_submit_button("💖 보드게임 등록하기",use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("보드게임 이름을 입력해 주세요.")
            else:
                image=save_image(image_file) if image_file else None
                if image_file and not image:
                    st.error("사진을 다시 확인해 주세요.")
                else:
                    add_game(name.strip(),image)
                    st.success(f"🎉 {name} 등록 완료!")
                    st.rerun()

st.divider()

st.markdown("""
<div style="text-align:center;color:#94A3B8;padding:15px;font-size:13px">
BOARD GAME MANAGER · 신나는 보드게임, 체계적인 관리 🎲
</div>
""",unsafe_allow_html=True)
