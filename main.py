import streamlit as st

st.set_page_config(page_title="Ozon Unit Eco - ОСНО", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        pwd = st.text_input("Введите пароль доступа", type="password")
        if pwd == "ozon2026":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            if pwd: st.error("Неверный пароль")
            return False
    return True

if check_password():
    st.title("🚀  Дашборд Юнит-Экономики (ОСНО)")
    st.sidebar.header("Настройки подключения")
    client_id = st.sidebar.text_input("Ozon Client-ID")
    api_key = st.sidebar.text_input("Ozon API Key", type="password")
    
    if not client_id or not api_key:
        st.info("Введите API ключи в боковой панели для загрузки данных из Ozon.")
    else:
        st.success("API ключи получены. Настраиваем интеграцию...")
        st.write("Здесь скоро появятся ваши реальные данные.")
