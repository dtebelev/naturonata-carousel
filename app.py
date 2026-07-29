"""
📸 Instagram Carousel Generator — Naturonata
Дашборд для создания каруселей для Instagram.
GPT-4 для текста, FLUX-2/Flash для картинок, Playwright для экспорта PNG.
Логотип на каждом слайде, CTA-изображение на последнем.

Запуск:
  pip install streamlit openai fal-client playwright Pillow requests
  playwright install chromium
  python -m streamlit run app.py --server.port 8501
"""

import streamlit as st
import os
import sys
import json
import base64
import tempfile
import asyncio
import re
import zipfile
from pathlib import Path
from io import BytesIO

import requests

# ─── Проверка Playwright (необязательный) ────────────────────────────
_playwright_available = False
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        browser.close()
    _playwright_available = True
except Exception:
    pass

# ─── Конфигурация страницы ───────────────────────────────────────────
st.set_page_config(
    page_title="📸 Карусель Генератор — Naturonata",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Пути к файлам ───────────────────────────────────────────────────
# Локальные пути (относительно app.py)
SCRIPT_DIR = Path(__file__).parent.resolve()
ASSETS_DIR = SCRIPT_DIR / "assets"
DEFAULT_LOGO_PATH = str(ASSETS_DIR / "logo.png")
DEFAULT_CTA_IMAGE_PATH = str(ASSETS_DIR / "cta_image.jpg")

# ─── Форматы ─────────────────────────────────────────────────────────
FORMATS = {
    "1:1 (Квадрат 1080×1080)": {"w": 1080, "h": 1080, "preview_w": 420, "preview_h": 420, "ratio": "1:1", "flux_size": "square_hd"},
    "4:5 (Прямоугольник 1080×1350)": {"w": 1080, "h": 1350, "preview_w": 420, "preview_h": 525, "ratio": "4:5", "flux_size": "portrait_4_5"},
    "3:4 (Прямоугольник 1080×1440)": {"w": 1080, "h": 1440, "preview_w": 420, "preview_h": 560, "ratio": "3:4", "flux_size": "portrait_3_4"},
}

FONTS = {
    "Plus Jakarta Sans": "Plus+Jakarta+Sans:wght@300;400;500;600;700;800",
    "Inter": "Inter:wght@300;400;500;600;700;800;900",
    "Montserrat": "Montserrat:wght@300;400;500;600;700;800;900",
    "Poppins": "Poppins:wght@300;400;500;600;700;800;900",
    "Nunito": "Nunito:wght@300;400;500;600;700;800;900",
    "Playfair Display": "Playfair+Display:wght@400;500;600;700;800;900",
    "Oswald": "Oswald:wght@300;400;500;600;700",
    "Merriweather": "Merriweather:wght@300;400;700;900",
}

FLUX_MODELS = {
    "FLUX-2/Flash (быстрый, дешёвый)": "fal-ai/flux-2/flash",
    "FLUX-2/Dev (качественный)": "fal-ai/flux/dev",
    "FLUX-2/Pro (макс. качество)": "fal-ai/flux-2-pro",
}

# ═════════════════════════════════════════════════════════════════════
#  🧠 АУДИТОРИИ NATURONATA
# ═════════════════════════════════════════════════════════════════════

AUDIENCES = {
    "🧒 Мамы: первые тревоги и свежий диагноз РАС/ЗПРР": {
        "description": "Мать ребёнка 2–7 лет с РАС/ЗПРР, только начавшая обследование. Пищевой откат, отсутствие речи, новые заключения, советы из чатов.",
        "cta_goal": "Перейти в Telegram-канал Naturonata",
        "pain_points": "Ограниченный рацион ребёнка, задержка речи, отсутствие контакта, хаос рекомендаций, страх навредить, дефицит нутриентов",
        "desires": "Понятные шаги, доверие к специалисту, план питания, прозрачность, результаты у других семей",
        "tone": "Эмпатичный, поддерживающий, конкретный, без шаблонов",
        "language_notes": "Избегать: «аутист», «аутёнок». Говорить: «ребёнок с РАС», «особенности развития». Не обещать чудес. Опираться на данные.",
        "cta_text": "Подпишись на канал @naturonata — там пошаговые советы и поддержка",
        "stat": "72% детей с аутизмом едят очень узкий набор продуктов",
    },
    "🍽️ Мамы: избирательность в еде, ЖКТ, выгорание": {
        "description": "Мать ребёнка 3–12 лет с РАС/ЗПРР. Выстроенный маршрут, но застой: ест 5 продуктов, запоры, вздутие, скачки поведения, нарушения сна.",
        "cta_goal": "Перейти в Telegram-канал Naturonata",
        "pain_points": "Избирательность в еде (5 продуктов), хронические запоры, нарушение сна, выгорание, отсутствие специалистов в регионах",
        "desires": "Постепенное введение новых продуктов, устранение дефицитов, помощь со сном, онлайн-поддержка",
        "tone": "Понимающий, практичный, без давления. Она уже устала от советов.",
        "language_notes": "Не предлагать «просто попробуй новый продукт» — это не работает при сенсорных особенностях. Объяснять связи: сенсорика → ЖКТ → поведение.",
        "cta_text": "В канале @naturonata — реальные истории и рабочие шаги",
        "stat": "46–89% детей с аутизмом имеют трудности с кормлением",
    },
    "🏥 Родители: ДЦП и/или эпилепсия, медицинские риски": {
        "description": "Семьи детей 1–14 лет с ДЦП и/или эпилепсией. Недостаточный вес, дисфагия, запоры, кетодиета, вопросы о медицинской диете.",
        "cta_goal": "Перейти в Telegram-канал Naturonata",
        "pain_points": "Трёхчасовые кормления, страх подавиться, запоры, кетодиета с побочными эффектами, недосып, отсутствие системной помощи",
        "desires": "Индивидуальный план с учётом диагноза, понимание рисков дисфагии, прозрачность, связь с врачами",
        "tone": "Осторожный, медицински грамотный, без обещаний, уважающий риски",
        "language_notes": "Обязательно упоминать медицинские риски. Не предлагать универсальные диеты. Подчёркивать: «не ставлю диагнозы, работаю по своей системе».",
        "cta_text": "В @naturonata — про питание при ДЦП и эпилепсии с доказательствами",
        "stat": "92% детей с ДЦП имеют проблемы с ЖКТ",
    },
    "👨 Папы и финансовые со-решатели": {
        "description": "Отец 30–50 лет, редко сам ищет информацию, но участвует в согласовании дорогих решений. Включается на этапе оплаты и оценки рисков.",
        "cta_goal": "Перейти в Telegram-канал Naturonata",
        "pain_points": "Недоверие к специалистам, море противоречивых советов, неясный план и расходы, скрытые платежи",
        "desires": "Доказательства, прозрачная цена, понятный план, границы компетенции специалиста",
        "tone": "Фактовый, конкретный, без эмоций. Цифры, исследования, логика.",
        "language_notes": "Меньше эмоций, больше фактов. Показывать цифры, исследования, прозрачность. Он — рациональный покупатель.",
        "cta_text": "Канал @naturonata — доказательный подход к питанию. Без «чудес».",
        "stat": "59% взрослых в России имеют избыточный вес",
    },
    "👩‍⚕️ Логопеды и специалисты-рефереры": {
        "description": "Логопеды, дефектологи, ABA-специалисты, неврологи, детские центры. Направляют семьи к специалистам по питанию.",
        "cta_goal": "Перейти в Telegram-канал Naturonata (для профессионального роста и направления семей)",
        "pain_points": "Фрагментарные знания по питанию, засилье «гуру» с детоксами, страх навредить рекомендацией, нехватка надёжных партнёров",
        "desires": "Надёжный эксперт без токсичных обещаний, междисциплинарное взаимодействие, доказательность",
        "tone": "Профессиональный, уважающий их экспертизу, партнёрский",
        "language_notes": "Подчёркивать: профильное образование, 9 лет практики, 1000+ консультаций, опора на научные данные. Уважать их компетенцию.",
        "cta_text": "Канал @naturonata — для специалистов, которые ищут надёжного партнёра",
        "stat": "Только 40% медработников чувствуют уверенность в диетологических рекомендациях",
    },
    "🤝 Админы сообществ и родительские лидеры": {
        "description": "Люди, управляющие чатами, форумами, НКО-проектами. Сами родители особых детей. Ищут контент для сообществ.",
        "cta_goal": "Перейти в Telegram-канал Naturonata",
        "pain_points": "Хронический дефицит времени, нехватка знаний, фильтрация псевдонауки, эмоциональная нагрузка модерации",
        "desires": "Качественный контент, вебинары, чек-листы, надёжные источники, экономия времени",
        "tone": "Равный среди равных, полезный, конкретный, без навязчивой продажи",
        "language_notes": "Она сама мама. Давать контент, который можно переслать в чат. Не продавить — дать повод подписаться.",
        "cta_text": "Канал @naturonata — контент, который можно пересылать в свои чаты",
        "stat": "Матери с ограниченной грамотностью в здоровье чаще верят соцсетям, чем официальным источникам",
    },
}

CONTENT_FORMATS = {
    "🧩 Викторина (Quiz)": {
        "icon": "🧩", "description": "Вопрос-ответ. Заставляет остановиться и подумать.",
        "structure": "Хук-вопрос → Варианты → Правильный ответ → Объяснение → CTA",
        "prompt_suffix": "Формат: ВИКТОРИНА. Начни с интригующего вопроса про питание или здоровье ребёнка. Дай варианты ответов (А, Б, В). Затем раскрой правильный ответ с объяснением. Используй статистику для убедительности.",
        "name": "ВИКТОРИНА",
    },
    "📋 Пошаговый гайд": {
        "icon": "📋", "description": "Пошаговая инструкция. Высокая сохраняемость.",
        "structure": "Хук-обещание → Шаг 1 → Шаг 2 → ... → Итог → CTA",
        "prompt_suffix": "Формат: ПОШАГОВЫЙ ГАЙД. Дай чёткие шаги, которые родитель может сделать ПРЯМО СЕЙЧАС. Нумеруй: «Шаг 1», «Шаг 2» и т.д. Каждый шаг — конкретное действие.",
        "name": "ГАЙД",
    },
    "💡 Лайфхак": {
        "icon": "💡", "description": "Быстрый совет. Высокие шеры.",
        "structure": "Хук-проблема → Лайфхак → Как это работает → Результат → CTA",
        "prompt_suffix": "Формат: ЛАЙФХАК. Дай конкретный, практичный совет. «Сделай X вместо Y — и получишь Z».",
        "name": "ЛАЙФХАК",
    },
    "🔥 Тренды / Новости": {
        "icon": "🔥", "description": "Актуальная новость. Быстро набирает охваты.",
        "structure": "Новость → Почему это важно → Что делать → CTA",
        "prompt_suffix": "Формат: ТРЕНДЫ/НОВОСТИ. Начни с актуальной новости или тренда. Объясни, почему это важно именно для этой аудитории.",
        "name": "ТРЕНДЫ",
    },
    "🍽️ Меню / Еда": {
        "icon": "🍽️", "description": "Меню, рецепты, питание. Самый сохраняемый контент.",
        "structure": "Хук-меню → День 1 → День 2 → ... → Советы → CTA",
        "prompt_suffix": "Формат: МЕНЮ/ПИТАНИЕ. Дай конкретное меню или рецепт, адаптированный для ребёнка с особенностями. Укажи питательные вещества.",
        "name": "МЕНЮ",
    },
    "💬 История / Кейс": {
        "icon": "💬", "description": "Реальная история. Высокие комментарии.",
        "structure": "Завязка → Развитие → Кульминация → Урок → CTA",
        "prompt_suffix": "Формат: ИСТОРИЯ/КЕЙС. Расскажи историю, с которой родитель себя узнает. Эмоциональная, но обнадёживающая.",
        "name": "ИСТОРИЯ",
    },
    "📊 Факты / Статистика": {
        "icon": "📊", "description": "Удивительные факты. Высокая шеряемость.",
        "structure": "Шокирующий факт → Контекст → Объяснение → CTA",
        "prompt_suffix": "Формат: ФАКТЫ/СТАТИСТИКА. Начни с удивительного факта или цифры, которая ломает стереотип. Объясни контекст.",
        "name": "ФАКТЫ",
    },
    "✅ Чек-лист": {
        "icon": "✅", "description": "Список для проверки. Максимальный save rate.",
        "structure": "Хук-чек-лист → Пункт 1 → Пункт 2 → ... → Бонус → CTA",
        "prompt_suffix": "Формат: ЧЕК-ЛИСТ. Дай конкретный список пунктов. Каждый пункт — конкретное действие.",
        "name": "ЧЕК-ЛИСТ",
    },
}


# ─── Session State ────────────────────────────────────────────────────
def init_state():
    defaults = {
        "carousel_html": None, "carousel_data": None, "slides_generated": False,
        "exported_slides": [], "generated_images": {}, "style_info": None, "html_path": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── CSS ──────────────────────────────────────────────────────────────
STYLES = """
<style>
    .stApp { background: #0a0a0a; }
    .main-title { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 0.5rem; }
    .subtitle { text-align: center; color: #888; font-size: 1.1rem; margin-bottom: 2rem; }
    .step-header { font-size: 1.4rem; font-weight: 700; color: #fff; margin: 1.5rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #333; }
    .preview-container { background: #1a1a1a; border-radius: 16px; padding: 24px; margin: 1rem 0; }
    .audience-box { background: linear-gradient(135deg, #1a1a2e 0%, #2d1b4e 100%); border: 1px solid #444; border-radius: 12px; padding: 16px; margin: 8px 0; }
    div.stButton > button:first-child { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; font-weight: 700; font-size: 1.1rem; padding: 12px 32px; border-radius: 12px; }
    div.stButton > button:hover { background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); }
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════
#  ХЕЛПЕРЫ
# ═════════════════════════════════════════════════════════════════════

def image_to_base64(image_file) -> str:
    if image_file is None: return ""
    image_file.seek(0)
    data = image_file.read()
    b64 = base64.b64encode(data).decode("utf-8")
    mime = image_file.type or "image/jpeg"
    return f"data:{mime};base64,{b64}"


def file_path_to_base64(path: str) -> str:
    """Convert a file path to base64 data URI."""
    if not path or not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime = mime_map.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def embed_fonts_in_html(html_path: str, font_name: str):
    import urllib.request
    font_url_str = FONTS.get(font_name, FONTS["Plus Jakarta Sans"])
    google_fonts_url = f"https://fonts.googleapis.com/css2?family={font_url_str}&display=swap"
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    try:
        req = urllib.request.Request(google_fonts_url, headers={"User-Agent": UA})
        css = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
        for font_url in set(re.findall(r"url\((https://[^)]+\.woff2)\)", css)):
            font_data = urllib.request.urlopen(font_url, timeout=15).read()
            b64 = base64.b64encode(font_data).decode("ascii")
            css = css.replace(font_url, f"data:font/woff2;base64,{b64}")
        css = css.replace("font-display: swap;", "font-display: block;")
        html = Path(html_path).read_text(encoding="utf-8")
        html = re.sub(r'<link[^>]*fonts\.googleapis\.com[^>]*>', f"<style>{css}</style>", html)
        html = re.sub(r'<link[^>]*rel=["\']preconnect["\'][^>]*>', '', html)
        Path(html_path).write_text(html, encoding="utf-8")
        return True
    except Exception as e:
        st.warning(f"⚠️ Не удалось встроить шрифты: {e}")
        return False


def generate_carousel_content(blog_post: str, num_slides: int, focus: str,
                               api_key: str, audience: dict, content_format: dict,
                               custom_cta: str = "") -> list:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    aud_desc = audience.get("description", "")
    aud_cta = custom_cta or audience.get("cta_text", audience.get("cta_goal", ""))
    aud_pain = audience.get("pain_points", "")
    aud_desires = audience.get("desires", "")
    aud_tone = audience.get("tone", "")
    aud_lang = audience.get("language_notes", "")
    aud_stat = audience.get("stat", "")

    fmt_name = content_format.get("name", "Карусель")
    fmt_structure = content_format.get("structure", "")
    fmt_prompt = content_format.get("prompt_suffix", "")

    content_prompt = f"""Ты — профессиональный SMM-копирайтер для Instagram-аккаунта Naturonata (@naturonata). Создай сценарий карусели из {num_slides} слайдов.

═══ О НАТАЛЬЕ (АВТОР КАРУСЕЛИ) ═══
Наталья Коршунова — нутрициолог, диетолог, натуропат. Специалист по системному восстановлению здоровья детей с особенностями развития немедикаментозными методами. Мама мальчика с РАС (11 лет). 9 лет практики, 1000+ консультаций. Не ставит диагнозы. Работает по своей системе — идёт к причинам, а не к симптомам.
Образование: PreventAge Lifestyle School (2 года), Международная Академия Натуропатии (Майкл Мюррей, Джозеф Пицорно), десятки курсов.

═══ АУДИТОРИЯ ═══
{aud_desc}
• Боли: {aud_pain}
• Желания: {aud_desires}
• Тон: {aud_tone}
• Языковые нюансы: {aud_lang}
• Ключевая статистика: {aud_stat}

═══ ФОРМАТ КОНТЕНТА ═══
{fmt_name}
Структура: {fmt_structure}
{fmt_prompt}

═══ ЦЕЛЬ CTA ═══
Последний слайд должен вести к: {aud_cta}
CTA должен быть мягким, не агрессивным. Не «купите», а «подпишись» или «переходи».
Важно: CTA должен вести в Telegram-канал @naturonata, НЕ на консультации.

═══ ФОКУС ═══
{focus}

═══ ПРАВИЛА ═══
- Слайд 1 (Хук): 1 жирный заголовок + 1 короткая поддерживающая строка. Эмоциональный триггер.
- Основные слайды: 1 жирный заголовок + 2-3 строки текста. 40-60 слов. → для списков.
- Последний слайд (CTA): 1 заголовок + 1 строка призыва к действию (подписка на @naturonata).
- Обращение на «ты». Эмпатия, но без жалости — с уважением.
- Запрещено: «аутист», «аутёнок», обещания чудес, детоксы, шаблоны.
- Если есть статистика — используй для убедительности.

═══ ИСТОЧНИК ═══
{blog_post}

═══ ФОРМАТ ВЫВОДА — строго JSON ═══
```json
[{{"type": "hook", "headline": "...", "body": "...", "accent": "..."}},
 {{"type": "content", "headline": "...", "body": "...", "accent": ""}},
 ...
 {{"type": "cta", "headline": "...", "body": "...", "accent": "..."}}]
```
headline — жирный заголовок, body — основной текст, accent — акцентная строка (для хука и CTA).
ИТОГО: ровно {num_slides} слайдов."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты — SMM-копирайтер для Naturonata. Отвечай ТОЛЬКО валидным JSON без markdown."},
            {"role": "user", "content": content_prompt},
        ],
        temperature=0.8, max_tokens=4000,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            try: return json.loads(match.group())
            except: pass
        st.error("❌ Не удалось распарсить JSON от GPT-4. Попробуйте ещё раз.")
        st.code(raw[:2000])
        return []


def analyze_reference_image(image_b64: str, api_key: str) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": """Проанализируй этот дизайн карусели для Instagram и извлеки стиль. Ответь ТОЛЬКО валидным JSON без markdown:{"primary_color":"#hex","secondary_color":"#hex","accent_color":"#hex","background_color":"#hex","text_color":"#hex","subtitle_color":"#hex","style_description":"описание","layout_type":"minimalist/magazine/bold/gradient","has_gradient":true,"gradient_from":"#hex","gradient_to":"#hex","number_position":"top-left/top-right/bottom-left/bottom-right/center","font_style":"modern/classic/serif/sans-serif","key_design_elements":["элемент1","элемент2"]}"""},
            {"type": "image_url", "image_url": {"url": image_b64}}
        ]}], max_tokens=1000,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    try: return json.loads(raw)
    except:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try: return json.loads(match.group())
            except: return {}
        return {}


def generate_flux_image(prompt: str, fal_key: str, model: str = "fal-ai/flux-2/flash", image_size: str = "square_hd") -> str:
    import fal_client
    os.environ["FAL_KEY"] = fal_key
    result = fal_client.subscribe(model, arguments={"prompt": prompt, "image_size": image_size, "enable_safety_checker": True})
    if result and result.get("images"): return result["images"][0]["url"]
    return ""


def build_carousel_html(slides_data, format_info, brand_name, handle, display_name, accent_color,
                         text_dark, text_body_color, bg_color, font_name, font_url, style_info=None,
                         generated_images=None, profile_photo_b64="", content_format_name="",
                         logo_b64="", cta_image_b64=""):
    total = len(slides_data)
    pw, ph = format_info["preview_w"], format_info["preview_h"]
    s = style_info or {}
    primary = s.get("primary_color", accent_color)
    secondary = s.get("secondary_color", "#1a1a2e")
    bg = s.get("background_color", bg_color)
    gradient_from = s.get("gradient_from", secondary)
    gradient_to = s.get("gradient_to", primary)
    has_gradient = s.get("has_gradient", True)
    number_pos = s.get("number_position", "top-left")
    images = generated_images or {}

    slides_html = ""
    for i, slide in enumerate(slides_data):
        sn = i + 1
        stype = slide.get("type", "content")
        headline = slide.get("headline", "")
        body = slide.get("body", "").replace("\n", "<br>")
        accent = slide.get("accent", "")
        is_hook = stype == "hook"
        is_cta = stype == "cta"

        bg_style = f"background: linear-gradient(135deg, {gradient_from} 0%, {gradient_to} 100%);" if has_gradient else f"background: {bg};"
        bg_img_div = f'<div class="bg-image" style="background-image:url(\'{images.get(str(i), "")}\');"></div>' if images.get(str(i), "") else ""

        num_pos = {"top-left": "top:28px; left:32px;", "top-right": "top:28px; right:32px;",
                    "bottom-left": "bottom:76px; left:32px;", "bottom-right": "bottom:76px; right:32px;",
                    "center": "top:28px; left:50%; transform:translateX(-50%);"}
        num_css = num_pos.get(number_pos, num_pos["top-left"])

        if is_hook: hs, hw, hlh, bs = "32px", "900", "1.15", "17px"; badge = f'<div class="slide-badge">{content_format_name or "КАРУСЕЛЬ"}</div>'
        elif is_cta: hs, hw, hlh, bs = "28px", "800", "1.2", "16px"; badge = ""
        else: hs, hw, hlh, bs = "24px", "700", "1.25", "15px"; badge = ""

        deco = f'<div class="deco-line" style="background:{primary};"></div>' if is_hook else ""
        arrow = """<div class="swipe-arrow"><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M9 18l6-6-6-6" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"/></svg></div>""" if i < total - 1 else ""
        pct = ((i + 1) / total) * 100
        acc_html = f'<p class="accent-text">{accent}</p>' if accent else ""

        # ── Логотип на каждом слайде (CSS class, no repeated base64) ──
        logo_html = '<div class="slide-logo"></div>' if logo_b64 else ""

        # ── CTA-изображение на последнем слайде ──
        cta_img_html = ""
        if is_cta and cta_image_b64:
            cta_img_html = f'<div class="cta-image-container"><img class="cta-image" src="{cta_image_b64}" alt="Naturonata CTA"></div>'

        # ── Разное позиционирование для CTA-слайда ──
        inner_class = "slide-inner cta-inner" if is_cta else "slide-inner"

        slides_html += f"""
        <div class="slide slide-{i}" data-index="{i}">
            {bg_img_div}
            <div class="slide-content">
                {logo_html}
                <div class="slide-number" style="{num_css}">{sn}<span class="slide-total">/{total}</span></div>
                <div class="{inner_class}">{badge}{deco}<h2 class="headline" style="font-size:{hs};font-weight:{hw};line-height:{hlh};">{headline}</h2><p class="body-text" style="font-size:{bs};">{body}</p>{acc_html}{cta_img_html}</div>
                <div class="slide-bottom"><div class="brand-bar"><span class="brand-name">{brand_name}</span><span class="brand-handle">{handle}</span></div></div>
            </div>
            <div class="progress-bar"><div class="progress-track"><div class="progress-fill" style="width:{pct}%;"></div></div><span class="progress-counter">{sn}/{total}</span></div>
            {arrow}
        </div>"""

    # ── Logo CSS: base64 embedded ONCE as background-image ──
    logo_css = ""
    if logo_b64:
        logo_css = f".slide-logo{{position:absolute;top:28px;right:32px;height:38px;width:auto;object-fit:contain;z-index:3;opacity:0.85;background-image:url('{logo_b64}');background-size:contain;background-repeat:no-repeat;background-position:center right;min-width:60px;}}"

    html = f"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><link href="https://fonts.googleapis.com/css2?family={font_url}&display=swap" rel="stylesheet"><style>
@import url('https://fonts.googleapis.com/css2?family={font_url}&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'{font_name}',sans-serif;background:#0a0a0a;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;}}
.carousel-viewport{{width:{pw}px;height:{ph}px;overflow:hidden;position:relative;border-radius:12px;box-shadow:0 25px 80px rgba(0,0,0,0.6);}}
.carousel-track{{display:flex;transition:transform 0.45s cubic-bezier(0.25,0.46,0.45,0.94);height:100%;}}
.slide{{min-width:{pw}px;height:{ph}px;position:relative;overflow:hidden;{bg_style}display:flex;flex-direction:column;}}
.bg-image{{position:absolute;top:0;left:0;width:100%;height:100%;background-size:cover;background-position:center;opacity:0.2;z-index:0;}}
.slide-content{{position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:0 36px 80px 36px;justify-content:center;}}
.slide-number{{position:absolute;font-size:14px;font-weight:700;color:rgba(255,255,255,0.5);letter-spacing:1px;z-index:2;}}
.slide-total{{color:rgba(255,255,255,0.25);}}
.slide-inner{{display:flex;flex-direction:column;gap:14px;}}
.slide-badge{{display:inline-block;background:{primary};color:#fff;font-size:10px;font-weight:800;padding:5px 16px;border-radius:20px;letter-spacing:2px;text-transform:uppercase;width:fit-content;}}
.deco-line{{width:48px;height:4px;border-radius:2px;}}
.headline{{color:#ffffff;letter-spacing:-0.5px;max-width:92%;}}
.body-text{{line-height:1.65;color:rgba(255,255,255,0.75);max-width:88%;}}
.accent-text{{font-size:15px;font-weight:700;color:{primary};margin-top:2px;}}
.slide-bottom{{position:absolute;bottom:64px;left:36px;right:36px;}}
.brand-bar{{display:flex;align-items:center;gap:10px;}}
.brand-name{{font-size:13px;font-weight:700;color:rgba(255,255,255,0.6);}}
.brand-handle{{font-size:12px;color:rgba(255,255,255,0.3);}}
.progress-bar{{position:absolute;bottom:0;left:0;right:0;padding:14px 28px 18px;display:flex;align-items:center;gap:12px;z-index:10;}}
.progress-track{{flex:1;height:3px;background:rgba(255,255,255,0.12);border-radius:3px;overflow:hidden;}}
.progress-fill{{height:100%;background:{primary};border-radius:3px;transition:width 0.3s;}}
.progress-counter{{font-size:11px;font-weight:600;color:rgba(255,255,255,0.3);min-width:30px;text-align:right;}}
.swipe-arrow{{position:absolute;right:0;top:0;bottom:0;width:52px;display:flex;align-items:center;justify-content:center;background:linear-gradient(to right,transparent,rgba(0,0,0,0.08));z-index:5;}}
.nav-dots{{display:flex;justify-content:center;gap:8px;margin-top:20px;}}
.nav-dot{{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.15);cursor:pointer;transition:all 0.3s;border:none;}}
.nav-dot.active{{background:{primary};width:28px;border-radius:4px;}}
/* ── Логотип на каждом слайде (base64 embedded ONCE in CSS) ── */
{logo_css}
/* ── CTA-изображение на последнем слайде ── */
.cta-inner{{gap:12px;}}
.cta-image-container{{display:flex;justify-content:center;margin-top:8px;}}
.cta-image{{width:220px;height:auto;max-height:200px;object-fit:contain;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.3);}}
</style></head><body>
<div class="carousel-viewport" id="viewport"><div class="carousel-track" id="track">{slides_html}</div></div>
<div class="nav-dots" id="dots">{''.join([f'<div class="nav-dot{" active" if i==0 else ""}" data-slide="{i}"></div>' for i in range(total)])}</div>
<script>let cs=0;const ts={total},sw={pw};function gs(i){{if(i<0||i>=ts)return;cs=i;document.getElementById('track').style.transform='translateX('+(-i*sw)+'px)';document.querySelectorAll('.nav-dot').forEach((d,j)=>{{d.classList.toggle('active',j===i);}});}}document.querySelectorAll('.nav-dot').forEach(d=>{{d.addEventListener('click',()=>gs(parseInt(d.dataset.slide)));}});let sx=0,id=false;const vp=document.getElementById('viewport');vp.addEventListener('pointerdown',e=>{{sx=e.clientX;id=true;}});vp.addEventListener('pointerup',e=>{{if(!id)return;id=false;const df=e.clientX-sx;if(df<-40)gs(cs+1);else if(df>40)gs(cs-1);}});document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight')gs(cs+1);if(e.key==='ArrowLeft')gs(cs-1);}});</script>
</body></html>"""
    return html


async def export_slides_to_png(html_path, output_dir, total_slides, slide_w, slide_h, preview_w, preview_h):
    from playwright.async_api import async_playwright
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    scale = slide_w / preview_w
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        page = await browser.new_page(viewport={"width": preview_w + 400, "height": preview_h + 400}, device_scale_factor=scale)
        await page.set_content(Path(html_path).read_text(encoding="utf-8"), wait_until="networkidle")
        await page.evaluate("() => document.fonts.ready")
        await page.wait_for_timeout(3000)
        await page.evaluate("""() => {const t=document.querySelector('.carousel-track');if(t){t.style.transition='none';t.style.transform='none';t.style.display='block';}document.querySelectorAll('.slide').forEach(s=>{s.style.display='block';s.style.minWidth='unset';});const v=document.querySelector('.carousel-viewport');if(v){v.style.cssText='overflow:visible;aspect-ratio:unset;';}}""")
        await page.wait_for_timeout(500)
        slides = await page.query_selector_all(".slide")
        exported = []
        for i, slide in enumerate(slides):
            fp = str(out / f"slide_{i+1:02d}.png")
            await slide.screenshot(path=fp)
            exported.append(fp)
        await browser.close()
    return exported


def export_slides_to_png_sync(html_path, output_dir, total_slides, slide_w, slide_h, preview_w, preview_h):
    """Sync wrapper for export — runs in existing event loop or new one."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, export_slides_to_png(
                html_path, output_dir, total_slides, slide_w, slide_h, preview_w, preview_h
            )).result()
        return result
    else:
        return asyncio.run(export_slides_to_png(
            html_path, output_dir, total_slides, slide_w, slide_h, preview_w, preview_h
        ))


# ═════════════════════════════════════════════════════════════════════
#  БОКОВАЯ ПАНЕЛЬ
# ═════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("⚙️ Настройки")
    st.subheader("🔑 API Ключи")
    openai_key = st.text_input("OpenAI API Key", type="password")
    fal_key = st.text_input("fal.ai API Key", type="password")
    st.divider()
    st.subheader("🎨 Бренд")
    brand_name = st.text_input("Название", value="Naturonata")
    handle = st.text_input("Instagram handle", value="@naturonata")
    display_name = st.text_input("Отображаемое имя", value="Наталья Коршунова")
    st.divider()
    st.subheader("🎨 Цвета")
    c1, c2 = st.columns(2)
    with c1:
        accent_color = st.color_picker("Акцент", value="#2FAD64")
        text_dark = st.color_picker("Тёмный текст", value="#0f1419")
    with c2:
        text_body_color = st.color_picker("Текст", value="#333333")
        bg_color = st.color_picker("Фон", value="#1a1a2e")
    st.divider()
    st.subheader("🔤 Шрифт")
    font_choice = st.selectbox("Шрифт", list(FONTS.keys()), index=2)
    st.divider()
    st.subheader("🖼️ Модель картинок")
    flux_model = st.selectbox("FLUX модель", list(FLUX_MODELS.keys()), index=0)
    st.divider()
    st.subheader("🏷️ Логотип и CTA-изображение")
    st.caption("Логотип на **каждом слайде**, CTA-изображение — на **последнем**")

    # Логотип
    logo_upload = st.file_uploader("🏷️ Логотип (PNG)", type=["png", "jpg", "jpeg", "webp"], key="logo_upload",
        help="Загрузите логотип или будет использован дефолтный Naturonata")
    use_default_logo = st.checkbox("✅ Использовать дефолтный логотип", value=True, key="use_default_logo")

    # CTA-изображение
    cta_image_upload = st.file_uploader("🖼️ CTA-изображение (последний слайд)", type=["jpg", "jpeg", "png", "webp"], key="cta_image_upload",
        help="Загрузите изображение для последнего слайда или будет использовано дефолтное")
    use_default_cta_image = st.checkbox("✅ Использовать дефолтное CTA-изображение", value=True, key="use_default_cta_image")

    st.divider()
    st.subheader("👤 Фото профиля")
    profile_photo = st.file_uploader("Загрузите фото", type=["jpg", "jpeg", "png", "webp"], key="profile_photo")

# ── Определяем logo_b64 и cta_image_b64 ──
if logo_upload:
    logo_b64 = image_to_base64(logo_upload)
elif use_default_logo and os.path.exists(DEFAULT_LOGO_PATH):
    logo_b64 = file_path_to_base64(DEFAULT_LOGO_PATH)
else:
    logo_b64 = ""

if cta_image_upload:
    cta_image_b64 = image_to_base64(cta_image_upload)
elif use_default_cta_image and os.path.exists(DEFAULT_CTA_IMAGE_PATH):
    cta_image_b64 = file_path_to_base64(DEFAULT_CTA_IMAGE_PATH)
else:
    cta_image_b64 = ""


# ═════════════════════════════════════════════════════════════════════
#  ОСНОВНАЯ ОБЛАСТЬ
# ═════════════════════════════════════════════════════════════════════

st.markdown('<h1 class="main-title">📸 Карусель Генератор</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Naturonata — карусели, которые останавливают скролл</p>', unsafe_allow_html=True)

# ─── Шаг 1: Аудитория ────────────────────────────────────────────────
st.markdown('<div class="step-header">1️⃣ Аудитория</div>', unsafe_allow_html=True)

audience_choice = st.selectbox("Для кого эта карусель?", list(AUDIENCES.keys()), index=0)
audience = AUDIENCES[audience_choice]

st.markdown(f'<div class="audience-box">', unsafe_allow_html=True)
st.markdown(f"**{audience.get('description', '')}**")
if audience.get("pain_points"): st.markdown(f"💢 **Боли:** {audience['pain_points']}")
if audience.get("desires"): st.markdown(f"✨ **Желания:** {audience['desires']}")
if audience.get("stat"): st.markdown(f"📊 **Статистика:** {audience['stat']}")
if audience.get("tone"): st.markdown(f"🗣️ **Тон:** {audience['tone']}")
st.markdown('</div>', unsafe_allow_html=True)

custom_cta = st.text_input("✏️ Кастомный CTA (необязательно)", placeholder=audience.get("cta_text", ""))

# ─── Шаг 2: Формат контента ──────────────────────────────────────────
st.markdown('<div class="step-header">2️⃣ Формат контента</div>', unsafe_allow_html=True)

fmt_cols = st.columns(4)
selected_format = None
for idx, (fmt_name, fmt_data) in enumerate(CONTENT_FORMATS.items()):
    with fmt_cols[idx % 4]:
        if st.button(f"{fmt_data['icon']}\n{fmt_name.split('(', 1)[0].strip()}", key=f"fmt_{idx}", use_container_width=True):
            selected_format = fmt_name

if selected_format is None:
    selected_format = list(CONTENT_FORMATS.keys())[0]

content_format = CONTENT_FORMATS[selected_format]

st.markdown(f'<div class="audience-box"><strong>{selected_format}</strong><br>{content_format["description"]}<br><em>Структура: {content_format["structure"]}</em></div>', unsafe_allow_html=True)

# ─── Шаг 3: Настройки ────────────────────────────────────────────────
st.markdown('<div class="step-header">3️⃣ Настройки карусели</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1: num_slides = st.slider("Количество слайдов", 3, 10, 7, 1)
with c2: format_choice = st.selectbox("Формат", list(FORMATS.keys()), index=1); format_info = FORMATS[format_choice]
with c3: ref_image = st.file_uploader("📸 Референс", type=["jpg", "jpeg", "png", "webp"], help="Загрузите пример дизайна карусели")

# ─── Шаг 4: Контент ──────────────────────────────────────────────────
st.markdown('<div class="step-header">4️⃣ Контент</div>', unsafe_allow_html=True)

blog_post = st.text_area("📝 Вставьте текст статьи / поста / транскрипта", height=250,
    placeholder="Вставьте сюда текст, из которого нужно сделать карусель. GPT-4 превратит его в захватывающий сценарий для вашей аудитории.")
focus = st.text_input("🎯 Фокус карусели", placeholder="Например: «Как расширить рацион ребёнка с РАС»")

# ─── Шаг 5: Изображения ──────────────────────────────────────────────
st.markdown('<div class="step-header">5️⃣ Изображения (опционально)</div>', unsafe_allow_html=True)
generate_images = st.checkbox("🎨 Генерировать фоновые изображения", value=False)
image_prompt_template = ""
selected_slides = []
if generate_images:
    image_prompt_template = st.text_area("Промпт для изображений", height=100, placeholder="Warm pastel colors, soft gradients, children, hopeful atmosphere, no text")
    st.markdown("**Выберите слайды для генерации:**")
    ic = st.columns(min(num_slides, 5))
    for i in range(num_slides):
        with ic[i % len(ic)]:
            if st.checkbox(f"Слайд {i+1}", value=(i == 0), key=f"img_slide_{i}"):
                selected_slides.append(i)

# ─── Шаг 6: Генерация ────────────────────────────────────────────────
st.markdown('<div class="step-header">6️⃣ Генерация</div>', unsafe_allow_html=True)

gc1, gc2 = st.columns([1, 3])
with gc1: generate_btn = st.button("🚀 Сгенерировать карусель", type="primary", use_container_width=True)
with gc2:
    if not openai_key: st.warning("⚠️ Введите OpenAI API Key")
    if not blog_post: st.info("💡 Вставьте текст поста")

if generate_btn:
    if not openai_key: st.error("❌ Введите OpenAI API Key!")
    elif not blog_post: st.error("❌ Вставьте текст поста!")
    else:
        progress = st.progress(0, text="Начинаем генерацию...")

        style_info = {}
        if ref_image and openai_key:
            progress.progress(10, text="📸 Анализ референса...")
            try:
                style_info = analyze_reference_image(image_to_base64(ref_image), openai_key)
                st.session_state.style_info = style_info
                st.success("✅ Референс проанализирован!")
                if style_info:
                    with st.expander("🎨 Извлечённый стиль"): st.json(style_info)
            except Exception as e: st.warning(f"⚠️ Ошибка анализа референса: {e}")

        progress.progress(30, text="✍️ GPT-4 создаёт сценарий...")
        try:
            slides_data = generate_carousel_content(
                blog_post=blog_post, num_slides=num_slides, focus=focus or "Общая тема",
                api_key=openai_key, audience=audience, content_format=content_format,
                custom_cta=custom_cta,
            )
            if not slides_data: st.stop()
            st.session_state.carousel_data = slides_data
            st.success(f"✅ Сценарий готов: {len(slides_data)} слайдов!")

            with st.expander("📄 Сценарий"):
                for i, slide in enumerate(slides_data):
                    st.markdown(f"**Слайд {i+1} ({slide.get('type', 'content')}):**")
                    st.markdown(f"- **Заголовок:** {slide.get('headline', '')}")
                    st.markdown(f"- **Текст:** {slide.get('body', '')}")
                    if slide.get('accent'): st.markdown(f"- **Акцент:** {slide.get('accent', '')}")
                    st.divider()
        except Exception as e: st.error(f"❌ Ошибка: {e}"); st.stop()

        generated_images = {}
        if generate_images and fal_key and image_prompt_template and selected_slides:
            progress.progress(50, text="🖼️ Генерация изображений...")
            flux_model_id = FLUX_MODELS[flux_model]
            flux_size = format_info.get("flux_size", "square_hd")
            for idx, si in enumerate(selected_slides):
                sh = slides_data[si].get("headline", "") if si < len(slides_data) else ""
                prompt = f"{image_prompt_template}, theme: {sh}, no text, no letters, background only, abstract"
                try:
                    progress.progress(50 + int((idx / max(len(selected_slides), 1)) * 30), text=f"🖼️ Слайд {si+1}...")
                    img_url = generate_flux_image(prompt=prompt, fal_key=fal_key, model=flux_model_id, image_size=flux_size)
                    if img_url: generated_images[str(si)] = img_url; st.success(f"✅ Картинка для слайда {si+1}!")
                except Exception as e: st.warning(f"⚠️ Слайд {si+1}: {e}")
            st.session_state.generated_images = generated_images
        elif generate_images and not fal_key: st.warning("⚠️ Введите fal.ai API Key!")

        progress.progress(85, text="🔧 Сборка HTML...")
        try:
            carousel_html = build_carousel_html(
                slides_data=slides_data, format_info=format_info, brand_name=brand_name,
                handle=handle, display_name=display_name, accent_color=accent_color,
                text_dark=text_dark, text_body_color=text_body_color, bg_color=bg_color,
                font_name=font_choice, font_url=FONTS[font_choice], style_info=style_info,
                generated_images=generated_images, profile_photo_b64=image_to_base64(profile_photo) if profile_photo else "",
                content_format_name=content_format.get("name", ""),
                logo_b64=logo_b64,
                cta_image_b64=cta_image_b64,
            )
            st.session_state.carousel_html = carousel_html
            st.session_state.slides_generated = True
            tmp_dir = tempfile.mkdtemp()
            html_path = os.path.join(tmp_dir, "carousel.html")
            with open(html_path, "w", encoding="utf-8") as f: f.write(carousel_html)
            st.session_state.html_path = html_path
            progress.progress(100, text="✅ Готово!")
            st.success("🎉 Карусель готова! Прокрутите вниз для превью и экспорта.")
        except Exception as e: st.error(f"❌ Ошибка: {e}"); st.stop()


# ─── Превью и экспорт ────────────────────────────────────────────────
if st.session_state.carousel_html:
    st.markdown('<div class="step-header">7️⃣ Превью</div>', unsafe_allow_html=True)
    st.markdown('<div class="preview-container">', unsafe_allow_html=True)
    st.components.v1.html(st.session_state.carousel_html, height=format_info["preview_h"] + 100, scrolling=False)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="step-header">8️⃣ Скачать слайды</div>', unsafe_allow_html=True)

    # ── Кнопка: скачать HTML-файл карусели ──
    st.markdown("**Способ 1: Скачать HTML-файл** (откройте в браузере и сделайте скриншоты)")
    st.download_button(
        "📥 Скачать carousel.html", 
        st.session_state.carousel_html.encode("utf-8"), 
        "carousel.html", "text/html",
        help="Скачайте HTML-файл, откройте в браузере и делайте скриншоты каждого слайда"
    )

    # ── Кнопка: скачать PNG через Playwright (только локально) ──
    st.markdown("**Способ 2: PNG-экспорт** (работает только при локальном запуске)")
    if not _playwright_available:
        st.caption("⚠️ На Streamlit Cloud PNG-экспорт недоступен. Для PNG запустите программу на своём компьютере.")
    
    ec1, ec2 = st.columns([1, 1])
    with ec1: export_btn = st.button("📥 Экспортировать в PNG", type="primary", use_container_width=True, disabled=not _playwright_available)
    with ec2:
        if st.session_state.exported_slides: st.info(f"✅ {len(st.session_state.exported_slides)} слайдов готовы")

    if export_btn and _playwright_available:
        with st.spinner("🔄 Экспорт..."):
            try:
                html_path = st.session_state.get("html_path", "")
                if not html_path or not os.path.exists(html_path):
                    tmp_dir = tempfile.mkdtemp()
                    html_path = os.path.join(tmp_dir, "carousel.html")
                    with open(html_path, "w", encoding="utf-8") as f: f.write(st.session_state.carousel_html)
                    st.session_state.html_path = html_path
                embed_fonts_in_html(html_path, font_choice)
                output_dir = os.path.join(os.path.dirname(html_path), "slides")
                exported = export_slides_to_png_sync(
                    html_path=html_path, output_dir=output_dir,
                    total_slides=len(st.session_state.carousel_data),
                    slide_w=format_info["w"], slide_h=format_info["h"],
                    preview_w=format_info["preview_w"], preview_h=format_info["preview_h"],
                )
                st.session_state.exported_slides = exported
                st.success(f"✅ Экспортировано {len(exported)} слайдов ({format_info['w']}×{format_info['h']}px)!")
            except Exception as e: st.error(f"❌ Ошибка экспорта: {e}")

    if st.session_state.exported_slides:
        st.subheader("📂 Слайды")
        sc = st.columns(min(len(st.session_state.exported_slides), 5))
        for i, sp in enumerate(st.session_state.exported_slides):
            with sc[i % len(sc)]: st.image(sp, caption=f"Слайд {i+1}")

        st.subheader("📥 Скачать")
        dc = st.columns(min(len(st.session_state.exported_slides), 5))
        for i, sp in enumerate(st.session_state.exported_slides):
            with dc[i % len(dc)]:
                with open(sp, "rb") as f:
                    st.download_button(f"📥 Слайд {i+1}", f.read(), f"slide_{i+1:02d}.png", "image/png", key=f"dl_{i}")

        zb = BytesIO()
        with zipfile.ZipFile(zb, "w", zipfile.ZIP_DEFLATED) as zf:
            for sp in st.session_state.exported_slides: zf.write(sp, os.path.basename(sp))
        zb.seek(0)
        st.download_button("📦 Скачать все (ZIP)", zb.getvalue(), "carousel_slides.zip", "application/zip")

st.divider()
st.markdown("""<div style="text-align:center;color:#666;padding:2rem 0;"><p>📸 Naturonata Carousel Generator • GPT-4 + FLUX-2/Flash + Playwright</p></div>""", unsafe_allow_html=True)
