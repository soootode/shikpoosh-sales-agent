from agent import sales_bot
from data import PRODUCTS
from db import get_all_orders
from langchain_core.messages import AIMessage, HumanMessage
import pandas as pd
import streamlit as st

# تنظیمات صفحه
st.set_page_config(
    page_title="فروشگاه اینترنتی شیک‌پوش", page_icon="🛍️", layout="wide"
)

# زیباسازی و چیدمان استاندارد پیام‌ها (RTL و پیام کاربر سمت راست)
st.markdown("""
<style>
    /* فونت و راست‌چین کلی */
    html, body, [class*="css"], .stApp {
        font-family: 'Tahoma', 'Vazirmatn', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* اصلاح چیدمان پیام‌ها */
    div[data-testid="stChatMessage"] {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
    }

    /* پیام کاربر: کاملاً سمت راست با تم متمایز */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]),
    div[data-testid="stChatMessage"]:has(.stChatMessageAvatarUser) {
        flex-direction: row !important; /* آیکون سمت راست */
        background-color: rgba(99, 102, 241, 0.1) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
    }

    /* پیام شایان (دستیار): تم خنثی */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]),
    div[data-testid="stChatMessage"]:has(.stChatMessageAvatarAssistant) {
        flex-direction: row !important;
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* تیتر اصلی بدون گلیچ */
    h1 {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.8rem !important;
    }
</style>
""", unsafe_allow_html=True)

# عنوان اصلی
st.title("🛍️ دستیار هوشمند فروشگاه شیک‌پوش")
st.caption(
    "توسعه‌یافته با LangGraph و هوش مصنوعی خودمختار (Agentic Sales Assistant)"
)

# سایدبار: پنل مدیریت زنده
with st.sidebar:
    st.header("📊 پنل انبارداری و سفارشات (ادمین)")

    st.subheader("📦 موجودی انبار")
    # ساخت کپی از دیتاست و تبدیل سایزها به متن ساده برای جلوگیری از ارور
    df_products = pd.DataFrame(PRODUCTS)[
        ["id", "name", "price", "stock", "sizes"]
    ].copy()
    df_products["sizes"] = df_products["sizes"].apply(
        lambda x: ", ".join(map(str, x))
    )

    # تغییر نام ستون‌ها به فارسی
    df_products.rename(
        columns={
            "id": "کد",
            "name": "نام کالا",
            "price": "قیمت (تومان)",
            "stock": "موجودی",
            "sizes": "سایزها",
        },
        inplace=True,
    )

    st.dataframe(df_products, use_container_width=True, hide_index=True)

    st.subheader("📝 سفارش‌های جدید ثبت‌شده")
    orders = get_all_orders()
    if orders:
        df_orders = pd.DataFrame(orders)[
            ["order_id", "product_name", "customer", "phone", "amount"]
        ].copy()
        df_orders.rename(
            columns={
                "order_id": "شناسه",
                "product_name": "کالا",
                "customer": "مشتری",
                "phone": "شماره",
                "amount": "مبلغ",
            },
            inplace=True,
        )
        st.dataframe(df_orders, use_container_width=True, hide_index=True)
    else:
        st.info("هنوز سفارشی ثبت نشده است.")

# مدیریت حافظه چت در Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_text = "سلام! من «شایان»، کارشناس فروش فروشگاه شیک‌پوش هستم. چطور می‌تونم کمکتون کنم؟"
    st.session_state.messages.append(AIMessage(content=welcome_text))

# نمایش پیام‌های قبلی در صفحه
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            st.write(msg.content)

# دریافت ورودی جدید از کاربر
user_input = st.chat_input("پیام خود را بنویسید...")

if user_input:
    # نمایش پیام کاربر
    with st.chat_message("user"):
        st.write(user_input)

    st.session_state.messages.append(HumanMessage(content=user_input))

    # اجرای ایجنت
    with st.chat_message("assistant"):
        with st.spinner("شایان در حال بررسی دیتابیس..."):
            result = sales_bot.invoke({"messages": st.session_state.messages})
            st.session_state.messages = result["messages"]
            latest_reply = st.session_state.messages[-1].content
            st.write(latest_reply)

    # رفرش صفحه برای بروزرسانی لحظه‌ای جدول‌های سایدبار
    st.rerun()