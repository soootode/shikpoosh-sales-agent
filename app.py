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

# ====================================================
# استایل اختصاصی مدرن و پیام‌رسانی (Telegram-like UI)
# ====================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

    /* فونت و پس‌زمینه‌ی کلی — بدون دست‌کاری جهت روی همه‌ی المان‌ها */
    html, body, .stApp {
        font-family: 'Vazirmatn', 'Tahoma', sans-serif !important;
        background-color: #09090b !important;
    }

    /* RTL فقط برای عناصر متنی/مارک‌داون، نه برای ویجت‌های کانواس مثل دیتافریم */
    .stApp .block-container,
    .stMarkdown, .stCaption, .stApp h1, .stApp h2, .stApp h3,
    .stApp p, .stApp label, .stApp li {
        direction: rtl !important;
        text-align: right !important;
    }

    /* عنوان اصلی */
    h1 {
        color: #fafafa !important;
        font-size: 1.8rem !important;
        margin-bottom: 0.2rem !important;
    }

    /* ---------------------------------------------- */
    /* اصلاح حیاتی: جدول موجودی و سفارش‌ها در سایدبار  */
    /* دیتافریم را کاملاً LTR و شفاف نگه می‌داریم تا    */
    /* گرید داخلی‌اش (canvas-based) درست رندر شود      */
    /* ---------------------------------------------- */
    div[data-testid="stDataFrame"] {
        direction: ltr !important;
        text-align: left !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #3f3f46 !important;
    }
    div[data-testid="stDataFrame"] * {
        direction: ltr !important;
    }

    /* کانتینر چت */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 0.4rem 0 !important;
    }

    /* حباب پیام کاربر (بنفش تلگرامی، گوشه‌های گرد، سمت راست) */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]),
    div[data-testid="stChatMessage"]:has(.stChatMessageAvatarUser) {
        flex-direction: row-reverse !important;
        margin-right: 0 !important;
        margin-left: auto !important;
        max-width: 85% !important;
        direction: rtl !important;
    }

    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) div[data-testid="stChatMessageContent"],
    div[data-testid="stChatMessage"]:has(.stChatMessageAvatarUser) div[data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%) !important;
        color: #ffffff !important;
        border-radius: 18px 4px 18px 18px !important;
        padding: 10px 16px !important;
        box-shadow: 0 4px 14px rgba(67, 56, 202, 0.25) !important;
        text-align: right !important;
        direction: rtl !important;
    }

    /* حباب پیام شایان / دستیار (خاکستری مدرن، سمت چپ) */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]),
    div[data-testid="stChatMessage"]:has(.stChatMessageAvatarAssistant) {
        flex-direction: row-reverse !important;
        margin-left: 0 !important;
        margin-right: auto !important;
        max-width: 90% !important;
        direction: rtl !important;
    }

    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) div[data-testid="stChatMessageContent"],
    div[data-testid="stChatMessage"]:has(.stChatMessageAvatarAssistant) div[data-testid="stChatMessageContent"] {
        background: #18181b !important;
        border: 1px solid #27272a !important;
        color: #f4f4f5 !important;
        border-radius: 4px 18px 18px 18px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        text-align: right !important;
        direction: rtl !important;
    }

    /* جدول‌های مارک‌داون داخل چت (خروجی متنی مدل، نه دیتافریم) */
    div[data-testid="stChatMessage"] table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin: 12px 0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #3f3f46 !important;
        font-size: 13px !important;
        direction: rtl !important;
    }

    div[data-testid="stChatMessage"] th {
        background-color: #27272a !important;
        color: #a1a1aa !important;
        font-weight: 600 !important;
        padding: 8px 10px !important;
        border: 1px solid #3f3f46 !important;
    }

    div[data-testid="stChatMessage"] td {
        padding: 8px 10px !important;
        border: 1px solid #27272a !important;
        background-color: #121215 !important;
    }

    /* ورودی چت پایین صفحه */
    div[data-testid="stChatInput"] {
        direction: rtl !important;
    }
    div[data-testid="stChatInput"] textarea {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Vazirmatn', sans-serif !important;
        background-color: #18181b !important;
        border: 1px solid #3f3f46 !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# عنوان اصلی
st.title("🛍️ دستیار هوشمند فروشگاه شیک‌پوش")
st.caption("توسعه‌یافته با LangGraph و هوش مصنوعی خودمختار (Agentic Sales Assistant)")

# سایدبار: پنل مدیریت زنده
with st.sidebar:
    st.header("📊 پنل انبارداری و سفارشات (ادمین)")

    st.subheader("📦 موجودی انبار")
    df_products = pd.DataFrame(PRODUCTS)[
        ["id", "name", "price", "stock", "sizes"]
    ].copy()
    df_products["sizes"] = df_products["sizes"].apply(
        lambda x: ", ".join(map(str, x))
    )

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

    st.subheader("📝 سفارش‌های جدید ثبت‌شده (SQLite)")
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

# نمایش پیام‌ها
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            st.write(msg.content)

# ورودی کاربر
user_input = st.chat_input("پیام خود را بنویسید...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    st.session_state.messages.append(HumanMessage(content=user_input))

    with st.chat_message("assistant"):
        with st.spinner("شایان در حال بررسی دیتابیس..."):
            result = sales_bot.invoke({"messages": st.session_state.messages})
            st.session_state.messages = result["messages"]
            latest_reply = st.session_state.messages[-1].content
            st.write(latest_reply)

    st.rerun()
