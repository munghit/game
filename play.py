with st.expander("✏️ 대여 정보 수정"):
    with st.form(f"edit_{game['id']}"):
        borrower=st.text_input(
            "대여자 이름",
            value=game["borrower"] or ""
        )

        status=st.selectbox(
            "대여 상태",
            ["대여 가능","대여 중"],
            index=0 if game["status"]=="대여 가능" else 1
        )

        loan_date=st.date_input(
            "📅 대여일",
            value=date.fromisoformat(game["loan_date"]) if game["loan_date"] else date.today(),
            format="YYYY-MM-DD"
        )

        return_date=st.date_input(
            "📅 반납일",
            value=date.fromisoformat(game["return_date"]) if game["return_date"] else date.today(),
            format="YYYY-MM-DD"
        )

        if st.form_submit_button("변경사항 저장"):
            if status=="대여 중" and not borrower.strip():
                st.error("대여자 이름을 입력하세요.")
            elif status=="대여 중" and return_date<loan_date:
                st.error("반납일은 대여일보다 빠를 수 없습니다.")
            else:
                update_game(
                    game["id"],
                    borrower,
                    status,
                    loan_date.isoformat(),
                    return_date.isoformat()
                )
                st.success("저장되었습니다.")
                st.rerun()
