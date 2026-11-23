
import streamlit as st
import sqlite3
import os
import uuid
from datetime import date

st.set_page_config(
    page_title="보드게임 대여 관리",
    page_icon="🎲",
    layout="wide"
)

DB = "boardgames.db"
IMAGE_DIR = "images"

os.makedirs(IMAGE_DIR, exist_ok=True)


# -----------------------------
# 데이터베이스 연결
# -----------------------------

def connect():
    return sqlite3.connect(DB, timeout=30)


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

        existing_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(games)").fetchall()
        }

        required_columns = {
            "name": "TEXT NOT NULL DEFAULT ''",
            "image": "TEXT",
            "borrower": "TEXT DEFAULT ''",
            "status": "TEXT DEFAULT '대여 가능'",
            "rental_date": "TEXT",
            "return_date": "TEXT"
        }

        for column, definition in required_columns.items():
            if column not in existing_columns:
                conn.execute(
                    f"ALTER TABLE games ADD COLUMN {column} {definition}"
                )


def get_games():
    with connect() as conn:
        return conn.execute("""
            SELECT
                id,
                name,
                image,
                borrower,
                status,
                rental_date,
                return_date
            FROM games
            ORDER BY id DESC
        """).fetchall()


def add_game(name, image):
    with connect() as conn:
        conn.execute("""
            INSERT INTO games (name, image)
            VALUES (?, ?)
        """, (name, image))


def update_rental(game_id, borrower, status, rental_date, return_date):
    with connect() as conn:
        conn.execute("""
            UPDATE games
            SET
                borrower = ?,
                status = ?,
                rental_date = ?,
                return_date = ?
            WHERE id = ?
        """, (
            borrower,
            status,
            rental_date,
            return_date,
            game_id
        ))


def delete_game(game_id):
    with connect() as conn:
        result = conn.execute(
            "SELECT image FROM games WHERE id = ?",
            (game_id,)
        ).fetchone()

        conn.execute(
            "DELETE FROM games WHERE id = ?",
            (game_id,)
        )

    if result and result[0] and os.path.exists(result[0]):
        os.remove(result[0])


# -----------------------------
# 이미지 관리
# -----------------------------

def save_image(uploaded_file):
    extension = os.path.splitext(uploaded_file.name)[1]
    filename = f"{uuid.uuid4().hex}{extension}"
    path = os.path.join(IMAGE_DIR, filename)

    with open(path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return path


def valid_image(path):
    return bool(path) and os.path.exists(path)


# -----------------------------
# 날짜 처리
# -----------------------------

def parse_date(value):
    if value:
        try:
            return date.fromisoformat(value)
        except (ValueError, TypeError):
            pass

    return date.today()


# -----------------------------
# 데이터베이스 초기화
# -----------------------------

init_db()


# -----------------------------
# 디자인
# -----------------------------

st.markdown("""
<style>
.stApp {
    background-color: #111827;
    color: #F9FAFB;
}

header[data-testid="stHeader"] {
    background-color: #111827;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

.main-title {
    font-size: 34px;
    font-weight: 800;
    color: #F9FAFB;
    margin-bottom: 5px;
}

.sub-title {
    color: #9CA3AF;
    font-size: 15px;
    margin-bottom: 28px;
}

.metric-card {
    background: #1F2937;
    padding: 20px;
    border-radius: 18px;
    border: 1px solid #374151;
}

.metric-label {
    color: #9CA3AF;
    font-size: 14px;
}

.metric-value {
    color: #F9FAFB;
    font-size: 30px;
    font-weight: 800;
    margin-top: 5px;
}

.game-card {
    background: #1F2937;
    border: 1px solid #374151;
    border-radius: 20px;
    padding: 18px;
    margin-bottom: 22px;
}

.game-name {
    font-size: 21px;
    font-weight: 800;
    color: #F9FAFB;
    margin-top: 10px;
    margin-bottom: 8px;
}

.available-badge {
    display: inline-block;
    background: #064E3B;
    color: #6EE7B7;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
}

.rented-badge {
    display: inline-block;
    background: #78350F;
    color: #FCD34D;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
}

div[data-testid="stTextInput"] input,
div[data-testid="stDateInput"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: #374151;
    color: #F9FAFB;
    border-radius: 12px;
}

div[data-testid="stTextInput"] input {
    border: 1px solid #4B5563;
}

.stButton button,
.stFormSubmitButton button {
    border-radius: 12px;
    font-weight: 700;
    min-height: 42px;
}

.stButton button[kind="primary"],
.stFormSubmitButton button[kind="primary"] {
    background-color: #3B82F6;
    border: none;
    color: white;
}

div[data-testid="stTabs"] button {
    border-radius: 12px 12px 0 0;
    font-weight: 700;
}

div[data-testid="stFileUploader"] section {
    background: #1F2937;
    border: 1px dashed #4B5563;
    border-radius: 16px;
}

label, p, span {
    color: #F9FAFB;
}

hr {
    border-color: #374151;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# 상단 제목
# -----------------------------

st.markdown(
    '<div class="main-title">🎲 보드게임 대여 관리</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">우리의 보드게임을 한눈에 관리해 보세요!</div>',
    unsafe_allow_html=True
)


# -----------------------------
# 데이터 및 통계
# -----------------------------

games = get_games()

total_count = len(games)
rented_count = sum(1 for game in games if game[4] == "대여 중")
available_count = total_count - rented_count

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🎲 전체 보드게임</div>
            <div class="metric-value">{total_count}개</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📦 대여 중</div>
            <div class="metric-value">{rented_count}개</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">✨ 대여 가능</div>
            <div class="metric-value">{available_count}개</div>
        </div>
    """, unsafe_allow_html=True)


st.write("")
st.write("")


# -----------------------------
# 탭 구성
# -----------------------------

tab1, tab2 = st.tabs([
    "📋 보드게임 관리",
    "➕ 보드게임 등록"
])


# -----------------------------
# 보드게임 관리
# -----------------------------

with tab1:

    st.subheader("보드게임 목록")

    search_col, filter_col = st.columns([2, 1])

    with search_col:
        search_text = st.text_input(
            "🔍 보드게임 검색",
            placeholder="보드게임 이름을 입력하세요"
        )

    with filter_col:
        status_filter = st.selectbox(
            "대여 상태 필터",
            ["전체", "대여 가능", "대여 중"]
        )

    filtered_games = []

    for game in games:
        game_id, name, image, borrower, status, rental_date, return_date = game

        if search_text and search_text.lower() not in name.lower():
            continue

        if status_filter != "전체" and status != status_filter:
            continue

        filtered_games.append(game)

    if not filtered_games:
        st.info("조건에 맞는 보드게임이 없습니다.")

    else:
        columns = st.columns(2)

        for index, game in enumerate(filtered_games):
            game_id, name, image, borrower, status, rental_date, return_date = game

            with columns[index % 2]:

                st.markdown('<div class="game-card">', unsafe_allow_html=True)

                if valid_image(image):
                    st.image(image, use_container_width=True)
                else:
                    st.markdown(
                        """
                        <div style="
                            height:180px;
                            background:#374151;
                            border-radius:15px;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-size:50px;
                        ">🎲</div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f'<div class="game-name">{name}</div>',
                    unsafe_allow_html=True
                )

                if status == "대여 중":
                    st.markdown(
                        '<span class="rented-badge">📦 대여 중</span>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<span class="available-badge">✨ 대여 가능</span>',
                        unsafe_allow_html=True
                    )

                st.write("")
                st.markdown("---")

                # 대여 정보 입력 폼
                with st.form(f"rental_form_{game_id}"):

                    new_status = st.selectbox(
                        "대여 상태",
                        ["대여 가능", "대여 중"],
                        index=0 if status == "대여 가능" else 1,
                        key=f"status_{game_id}"
                    )

                    new_borrower = st.text_input(
                        "대여자 이름",
                        value=borrower or "",
                        placeholder="대여자 이름을 입력하세요",
                        key=f"borrower_{game_id}"
                    )

                    new_rental = st.date_input(
                        "대여 날짜",
                        value=parse_date(rental_date),
                        key=f"rental_{game_id}"
                    )

                    new_return = st.date_input(
                        "반납 날짜",
                        value=parse_date(return_date),
                        key=f"return_{game_id}"
                    )

                    submitted = st.form_submit_button(
                        "💾 대여 정보 저장",
                        use_container_width=True
                    )

                    if submitted:

                        if new_status == "대여 중":

                            if not new_borrower.strip():
                                st.error("대여자 이름을 입력해 주세요.")

                            elif new_return < new_rental:
                                st.error("반납 날짜는 대여 날짜보다 빠를 수 없습니다.")

                            else:
                                update_rental(
                                    game_id,
                                    new_borrower.strip(),
                                    "대여 중",
                                    new_rental.isoformat(),
                                    new_return.isoformat()
                                )

                                st.success("대여 정보가 저장되었습니다.")
                                st.rerun()

                        else:
                            update_rental(
                                game_id,
                                "",
                                "대여 가능",
                                None,
                                None
                            )

                            st.success("대여 정보가 초기화되었습니다.")
                            st.rerun()

                if st.button(
                    "🗑️ 보드게임 삭제",
                    key=f"delete_{game_id}",
                    use_container_width=True
                ):
                    delete_game(game_id)
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# 보드게임 등록
# -----------------------------

with tab2:

    st.subheader("새로운 보드게임 등록")

    st.write("보드게임 이름과 사진을 등록해 주세요.")

    with st.form("add_game_form"):

        game_name = st.text_input(
            "보드게임 이름",
            placeholder="예: 루미큐브"
        )

        uploaded_image = st.file_uploader(
            "보드게임 사진",
            type=["png", "jpg", "jpeg", "webp"]
        )

        add_submitted = st.form_submit_button(
            "🎲 보드게임 등록하기",
            use_container_width=True
        )

        if add_submitted:

            if not game_name.strip():
                st.error("보드게임 이름을 입력해 주세요.")

            elif uploaded_image is None:
                st.error("보드게임 사진을 등록해 주세요.")

            else:
                image_path = save_image(uploaded_image)
                add_game(game_name.strip(), image_path)

                st.success("보드게임이 등록되었습니다!")
                st.rerun()
