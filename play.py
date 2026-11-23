
import streamlit as st
import sqlite3
import os
import uuid
from datetime import date

st.set_page_config(page_title="보드게임 놀이터",page_icon="🎲",layout="wide")

DB="boardgames.db"
IMAGE_DIR="images"
os.makedirs(IMAGE_DIR,exist_ok=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
.stApp{background:linear-gradient(135deg,#fff8f0 0%,#fff0f5 55%,#eef8ff 100%);font-family:'Jua',sans-serif}
h1,h2,h3,p,label,span,div{font-family:'Jua',sans-serif}
h1{color:#ec719b!important;font-size:2.6rem!important}
h2,h3{color:#665477!important}
.stButton button{background:#ff91b5;color:white;border:0;border-radius:14px;font-size:16px;transition:.2s}
.stButton button:hover{background:#f36d9b;color:white;transform:translateY(-2px)}
.stTextInput input,.stDateInput input{border-radius:12px}
div[data-testid="stMetric"]{background:white;border:2px solid #ffe0eb;border-radius:18px;padding:16px;box-shadow:0 4px 12px #f4cbd8}
div[data-testid="stExpander"]{background:white;border:2px solid #ffe0eb;border-radius:15px}
div[data-testid="stFileUploader"]{background:#fffafd;border:2px dashed #f5a5c1;border-radius:15px;padding:12px}
hr{border-color:#ffd6e5}
.game-card{background:white;border:2px solid #ffe0eb;border-radius:18px;padding:16px;margin-bottom:12px;box-shadow:0 4px 12px #f4cbd8}
.available{background:#e3f8ed;color:#32976a;padding:5px 12px;border-radius:20px;font-size:14px}
.rented{background:#ffe3ec;color:#dc648b;padding:5px 12px;border-radius:20px;font-size:14px}
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
    return path and os.path.isfile(path)

init_db()

st.markdown("""
# 🎲 보드게임 놀이터
### 🧸 우리 학교 보드게임 대여 관리소
오늘도 신나는 보드게임 시간! ✨
""")
st.divider()

games=get_games()
total=len(games)
rented=sum(1 for g in games if g[4]=="대여 중")
available=total-rented

m1,m2,m3=st.columns(3)
m1.metric("🎲 전체 보드게임",f"{total}개")
m2.metric("💗 대여 중",f"{rented}개")
m3.metric("🌱 대여 가능",f"{available}개")

st.divider()

tab1,tab2=st.tabs(["🎮 보드게임 목록","➕ 보드게임 등록"])

with tab1:
    st.subheader("🌈 우리 보드게임")
    search=st.text_input("🔎 보드게임 이름 검색",placeholder="찾고 싶은 게임 이름을 입력하세요")
    filter_status=st.selectbox("대여 상태 필터",["전체","대여 가능","대여 중"])
    filtered=[]
    for g in games:
        if search.lower() not in g[1].lower():
            continue
        if filter_status!="전체" and g[4]!=filter_status:
            continue
        filtered.append(g)

    if not filtered:
        st.info("아직 등록된 보드게임이 없어요. 새 게임을 등록해 보세요! 🎲")
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
                        st.markdown("### 🎲 사진이 아직 없어요")
                    st.markdown(f"### {name}")
                    if status=="대여 중":
                        st.markdown('<span class="rented">💗 대여 중</span>',unsafe_allow_html=True)
                        st.write(f"👤 대여자: {borrower or '미입력'}")
                        st.write(f"📅 대여일: {rental_date or '-'}")
                        st.write(f"🏁 반납 예정일: {return_date or '-'}")
                    else:
                        st.markdown('<span class="available">🌱 대여 가능</span>',unsafe_allow_html=True)
                    st.markdown('</div>',unsafe_allow_html=True)

                    with st.expander("✏️ 정보 수정"):
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
                                st.error("반납 예정일은 대여일보다 빠를 수 없어요.")
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
                                update_game(game_id,new_name.strip(),new_image,new_borrower.strip() if new_status=="대여 중" else "",new_status,new_rental.isoformat() if new_rental else None,new_return.isoformat() if new_return else None)
                                st.success("수정 내용이 저장되었어요! 🎉")
                                st.rerun()
                    with st.expander("🗑️ 보드게임 삭제"):
                        st.warning("삭제하면 해당 게임의 정보도 함께 사라져요.")
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
st.markdown("<div style='text-align:center;color:#dc8eaa;padding:15px'>🎲 오늘도 즐거운 보드게임 시간! 💗</div>",unsafe_allow_html=True)
