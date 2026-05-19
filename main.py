import streamlit as st
import pandas as pd
import requests

# 1. Настройка страницы
st.set_page_config(page_title="Ozon Unit Eco - ОСНО", layout="wide")

# 2. Простая авторизация
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("Введите пароль доступа", type="password")
    if pwd == "ozon2026":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# 3. Заголовок и ввод ключей
st.title("📊  Автоматический расчет Юнит-экономики (ОСНО)")

st.sidebar.header("🔑  Доступ к Ozon API")
client_id = st.sidebar.text_input("Client-ID (из ЛК Ozon)")
api_key = st.sidebar.text_input("API Key (тип: Администратор)", type="password")

st.sidebar.markdown("---")
st.sidebar.write("⚙️  **Система:** ОСНО (НДС 20%)")
st.sidebar.info("Данные подгружаются напрямую из вашего личного кабинета.")

if not client_id or not api_key:
    st.warning("👈 Пожалуйста, введите ваши API ключи в боковой панели, чтобы система могла построить расчеты.")
else:
    # Функция для запроса данных о товарах
    def get_ozon_products(c_id, a_key):
        url = "https://api-seller.ozon.ru/v2/product/list"
        headers = {"Client-Id": c_id, "Api-Key": a_key}
        payload = {"filter": {"visibility": "ALL"}, "limit": 100}
        
        try:
            res = requests.post(url, headers=headers, json=payload)
            if res.status_code == 200:
                return res.json().get('result', {}).get('items', [])
            else:
                st.error(f"Ошибка API: {res.status_code}")
                return []
        except Exception as e:
            st.error(f"Не удалось связаться с Ozon: {e}")
            return []

    # 4. Основная логика
    with st.spinner('Синхронизируюсь с вашим кабинетом...'):
        products = get_ozon_products(client_id, api_key)
        
        if products:
            st.success(f"Найдено товаров: {len(products)}")
            
            # Здесь мы будем строить таблицу как в твоем файле v8.9.0
            # Пока выведем список для проверки связи
            st.subheader("Ваши товары (данные из API)")
            df_items = pd.DataFrame(products)
            st.write("Список SKU получен успешно. Настраиваю расчетные формулы НДС...")
            
            # ПРИМЕР РАСЧЕТА (Берем логику из твоей таблицы)
            st.markdown("---")
            st.subheader("Модель расчета ОСНО")
            
            # Тестовая строка для демонстрации математики НДС
            calc_data = {
                "Показатель": ["Цена продажи", "Себестоимость закупа", "Комиссия Ozon", "Логистика"],
                "Сумма (с НДС)": [5000.0, 2200.0, 600.0, 450.0]
            }
            df_calc = pd.DataFrame(calc_data)
            df_calc['Без НДС (основа)'] = df_calc['Сумма (с НДС)'] / 1.2
            df_calc['НДС (20%)'] = df_calc['Сумма (с НДС)'] - df_calc['Без НДС (основа)']
            
            st.table(df_calc)
            
            profit = df_calc.iloc[0, 2] - df_calc.iloc[1, 2] - df_calc.iloc[2, 2] - df_calc.iloc[3, 2]
            st.metric("Чистая прибыль на 1 единицу (после НДС)", f"{round(profit, 2)} руб.")
            
        else:
            st.info("Товары не найдены или ключи не подходят.")
