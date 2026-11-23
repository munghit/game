
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import date
import uuid

st.set_page_config(page_title="보드게임 대여 관리",page_icon="🎲",layout="wide")

BASE_DIR=Path(__file__).parent
DB_PATH=BASE_DIR/"boardgames.db"
IMAGE_DIR=BASE_DIR/"images"
IMAGE_DIR.mkdir(exist_ok=True)

def connect():
    conn=sqlite3.connect(DB_PATH)
    conn.row_factory=sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS games(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_path TEXT,
            borrower TEXT DEFAULT '',
            status TEXT DEFAULT '대여 가능',
            loan_date TEXT,
            return_date TEXT
        )
        """)

def get_games(search=""):
    with connect() as conn:
        if search:
            return conn.execute("SELECT * FROM games WHERE name LIKE ? ORDER BY name",(f"%{search}%",)).fetchall()
        return conn.execute("SELECT * FROM games ORDER BY name").fetchall()

def add_game(name,image):
    image_path=None
    if image:
        ext=Path(image.name).suffix.lower()
        if ext not in [".jpg",".jpeg",".png",".webp"]:
            raise ValueError("JPG, PNG, WEBP 파일만 업로드할 수 있습니다.")
        filename=f"{uuid.uuid4().hex}{ext}"
        image_path=str(IMAGE_DIR/filename)
        Path(image_path).write_bytes(image.getbuffer())
    with connect() as conn:
        conn.execute("INSERT INTO games(name,image_path) VALUES(?,?)",(name.strip(),image_path))

def update_game(game_id,borrower,status,loan_date,return_date):
    if status=="대여 가능":
        borrower=""
        loan_date=None
        return_date=None
    with connect() as conn:
        conn.execute("""
        UPDATE games
        SET borrower=?,status=?,loan_date=?,return_date=?
        WHERE id=?
        """,(borrower.strip(),status,loan_date,return_date,game_id))

def delete_game(game_id):
    with connect() as conn:
        game=conn.execute("SELECT image_path FROM games WHERE id=?",(game_id,)).fetchone()
        conn.execute("DELETE FROM games WHERE id=?",(game_id,))
    if game and game["image_path"]:
        Path(game["image_path"]).unlink(missing_ok=True)

init_db()

st.title("🎲 보드게임 대여 관리")
st.caption("학교 보드게임 대여 및 반납 기록 관리")

games=get_games()
total=len(games)
rented=sum(g["status"]=="대여 중" for g in games)
available=total-rented

c1,c2,c3=st.columns(3)
c1.metric("전체 보드게임",f"{total}개")
c2.metric("대여 중",f"{rented}개")
c3.metric("대여 가능",f"{available}개")

st.divider()

with st.expander("➕ 새 보드게임 등록",expanded=total==0):
    with st.form("add_form",clear_on_submit=True):
        name=st.text_input("보드게임 이름",placeholder="예: 루미큐브")
        image=st.file_uploader("보드게임 사진",type=["jpg","jpeg","png","webp"])
        if st.form_submit_button("보드게임 추가"):
            if not name.strip():
                st.error("보드게임 이름을 입력하세요.")
            else:
                try:
                    add_game(name,image)
                    st.success("보드게임이 등록되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

st.subheader("📚 보드게임 목록")
search=st.text_input("🔎 보드게임 검색",placeholder="게임 이름 입력")
filtered=get_games(search)

if not filtered:
    st.info("등록된 보드게임이 없습니다. 새 보드게임을 추가해 주세요.")
else:
    for i in range(0,len(filtered),2):
        cols=st.columns(2)
        for col,game in zip(cols,filtered[i:i+2]):
            with col:
                with st.container(border=True):
                    if game["image_path"] and Path(game["image_path"]).exists():
                        st.image(game["image_path"],use_container_width=True)
                    else:
                        st.info("등록된 사진이 없습니다.")
                    st.markdown(f"### {game['name']}")
                    if game["status"]=="대여 중":
                        st.warning("● 대여 중")
                        st.write(f"대여자: {game['borrower'] or '미입력'}")
                        st.write(f"대여일: {game['loan_date'] or '미입력'}")
                        st.write(f"반납일: {game['return_date'] or '미입력'}")
                    else:
                        st.success("● 대여 가능")
                    with st.expander("✏️ 대여 정보 수정"):
                        with st.form(f"edit_{game['id']}"):
                            borrower=st.text_input("대여자 이름",value=game["borrower"] or "")
                            status=st.selectbox("대여 상태",["대여 가능","대여 중"],index=0 if game["status"]=="대여 가능" else 1)
                            loan_enabled=st.checkbox("대여일 입력",value=bool(game["loan_date"]))
                            loan_date=st.date_input("대여일",value=date.fromisoformat(game["loan_date"]) if game["loan_date"] else date.today()) if loan_enabled else None
                            return_enabled=st.checkbox("반납일 입력",value=bool(game["return_date"]))
                            return_date=st.date_input("반납일",value=date.fromisoformat(game["return_date"]) if game["return_date"] else date.today()) if return_enabled else None
                            if st.form_submit_button("변경사항 저장"):
                                if status=="대여 중" and not borrower.strip():
                                    st.error("대여자 이름을 입력하세요.")
                                elif loan_date and return_date and return_date<loan_date:
                                    st.error("반납일은 대여일보다 빠를 수 없습니다.")
                                else:
                                    update_game(game["id"],borrower,status,loan_date.isoformat() if loan_date else None,return_date.isoformat() if return_date else None)
                                    st.success("저장되었습니다.")
                                    st.rerun()
                    with st.expander("🗑️ 보드게임 삭제"):
                        confirm=st.checkbox("삭제 확인",key=f"confirm_{game['id']}")
                        if st.button("보드게임 삭제",key=f"delete_{game['id']}",disabled=not confirm):
                            delete_game(game["id"])
                            st.success("삭제되었습니다.")
                            st.rerun()

st.divider()
st.caption("데이터는 boardgames.db에, 사진은 images 폴더에 저장됩니다.")

