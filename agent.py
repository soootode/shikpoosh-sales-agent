import json
import re
from typing import Annotated, Literal
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

# ایمپورت دیتابیس لوکال از فایل data.py
from data import PRODUCTS

# ایمپورت لایه‌ی SQLite برای ذخیره‌سازی سفارش‌ها
from db import insert_order

# خواندن متغیرهای محیطی و کلید GROQ_API_KEY از فایل .env
load_dotenv()


# ----------------------------------------------------
# ۱. تعریف ابزارها (Tools)
# ----------------------------------------------------
@tool
def search_products(query: str) -> str:
    """برای جستجوی محصولات در دیتابیس فروشگاه بر اساس نام یا دسته‌بندی کالا."""
    results = []
    for p in PRODUCTS:
        if (
            query.lower() in p["name"].lower()
            or query.lower() in p["category"].lower()
            or query.lower() in p["description"].lower()
        ):
            status = "موجود" if p["stock"] > 0 else "ناموجود"
            results.append(
                f"کد کالا: {p['id']} | نام: {p['name']} | قیمت: {p['price']:,} تومان | وضعیت: {status} | سایزهای موجود: {p['sizes']}"
            )

    if not results:
        return "هیچ محصولی با این مشخصات پیدا نشد."
    return "\n".join(results)


@tool
def register_order(
    product_id: int, customer_name: str, phone_number: str, address: str
) -> str:
    """
    ثبت سفارش نهایی مشتری.
    فقط زمانی این تابع را فراخوانی کن که هر سه مورد (نام کامل، شماره تماس معتبر، و آدرس پستی) را از کاربر دریافت کرده باشی.
    """
    # اعتبارسنجی شماره موبایل ایران
    if not re.match(r"^09\d{9}$", phone_number):
        return "خطا: شماره موبایل معتبر نیست! شماره باید ۱۱ رقمی بوده و با 09 شروع شود."

    # بررسی موجودی کالا
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return "خطا: کد محصول وارد شده در سیستم یافت نشد."
    if product["stock"] <= 0:
        return f"متاسفانه موجودی محصول '{product['name']}' به اتمام رسیده است."

    # ساخت فاکتور و ثبت در دیتابیس SQLite
    order_id = insert_order(
        product_id=product_id,
        product_name=product["name"],
        amount=product["price"],
        customer=customer_name,
        phone=phone_number,
        address=address,
    )
    product["stock"] -= 1  # کسر از انبار

    return (
        f"سفارش با موفقیت ثبت شد!\n"
        f"شماره پیگیری: {order_id}\n"
        f"کالا: {product['name']}\n"
        f"مبلغ قابل پرداخت: {product['price']:,} تومان\n"
        f"تحویل‌گیرنده: {customer_name}"
    )


tools = [search_products, register_order]


# ----------------------------------------------------
# ۲. تعریف ساختار وضعیت گراف (Agent State)
# ----------------------------------------------------
class AgentState(TypedDict):
    # پیام‌ها به صورت خودکار به لیست اضافه (Append) می‌شوند
    messages: Annotated[list, add_messages]


# ----------------------------------------------------
# ۳. پرامپت سیستمی و مدل زبانی (Groq)
# ----------------------------------------------------
SYSTEM_PROMPT = """شما «شایان»، دستیار هوشمند، حرفه‌ای و کارشناس فروش فروشگاه اینترنتی «شیک‌پوش» هستید.
قوانین سفت‌وسخت شما:
۱. بسیار مودب، خوش‌برخورد، پرانرژی و به زبان فارسی روان صحبت کنید.
۲. برای پاسخ به هر سوالی درباره موجودی، قیمت و مشخصات کالاها، حتماً از ابزار `search_products` استفاده کنید و هرگز از خود اطلاعات نسازید!
۳. اگر کالایی ناموجود بود، با خوش‌رویی اطلاع دهید و کالای مشابه موجود را معرفی کنید.
۴. برای ثبت سفارش با ابزار `register_order`، حتماً باید این ۳ مورد را دقیقاً داشته باشید: «نام و نام خانوادگی»، «شماره تماس (09xxxxxxxxx)» و «آدرس کامل پستی». اگر هر کدام ناقص بود، با احترام از مشتری بخواهید آن را تکمیل کند و زودتر از موعد ابزار ثبت را صدا نزنید!
"""

# اتصال به مدل پرسرعت و رایگان Groq
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.1,
)

# متصل کردن ابزارها به مدل زبانی
llm_with_tools = llm.bind_tools(tools)


# ----------------------------------------------------
# ۴. تعریف نودها و سیم‌کشی جریان گراف
# ----------------------------------------------------
def sales_agent_node(state: AgentState):
    messages = state["messages"]
    # قرار دادن پرامپت سیستمی در ابتدای پیام‌ها در صورت نبودن
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    last_message = state["messages"][-1]
    # اگر مدل درخواست فراخوانی ابزار داده بود
    if last_message.tool_calls:
        return "tools"
    # اگر کار تمام شده بود
    return END


# ساخت معماری گراف
workflow = StateGraph(AgentState)

# تعریف نودها
workflow.add_node("agent", sales_agent_node)
workflow.add_node("tools", ToolNode(tools))

# مسیرها
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# کامپایل گراف برای اجرا
sales_bot = workflow.compile()