import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Ozon Unit Eco - ОСНО", layout="wide")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("Введите пароль доступа", type="password")
    if pwd == "ozon2026":
        st.session_state.auth = True
        st.rerun()
    st.stop()

st.title("📊  Автоматический расчет Юнит-экономики (ОСНО)")

st.sidebar.header("🔑  Доступ к Ozon API")
client_id = st.sidebar.text_input("Client-ID")
api_key = st.sidebar.text_input("API Key (Admin)", type="password")

if client_id and api_key:
    # ИСПОЛЬЗУЕМ V3 API (самый стабильный)
    url = "https://api-seller.ozon.ru/v3/product/list"
    headers = {"Client-Id": client_id, "Api-Key": api_key}
    payload = {"filter": {"visibility": "ALL"}, "limit": 100}
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            products = res.json().get('result', {}).get('items', [])
            st.success(f"Соединение установлено! Найдено товаров: {len(products)}")
            # Здесь будет таблица катушек
        else:
            st.error(f"Ozon ответил ошибкой {res.status_code}. Проверьте правильность ключей.")
    except Exception as e:
        st.error(f"Ошибка сети: {e}")
else:
    st.info("👈 Введите API ключи в левом меню.")
