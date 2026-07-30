# 📸 Naturonata Carousel Generator — Полная документация для разработчика

> **Версия:** v5.3 (30 июля 2026)
> **Файл программы:** `app.py` (~1226 строк)
> **Цель:** Дашборд для генерации Instagram-каруселей для бренда Naturonata

---

## 1. Что делает эта программа

Streamlit-дашборд, который создаёт Instagram-карусели на русском языке для бренда **Naturonata** (@naturonata). 

**Пайплайн:**
1. Пользователь выбирает аудиторию, формат контента, вставляет текст
2. GPT-4o генерирует сценарий карусели (JSON с заголовками, текстами, акцентами)
3. (Опционально) FLUX-2/Flash генерирует фоновые изображения ИЛИ используется кастомный фон (NEW v5.1)
4. Сценарий собирается в интерактивный HTML-превью (свайп, навигация)
5. Playwright экспортирует каждый слайд в PNG 1080×1350px
6. ZIP-архив для скачивания (клиентский html-to-image + серверный Playwright)

---

## 2. Бренд и контекст

**Naturonata** — Наталья Коршунова, нутрициолог, диетолог, натуропат.
- Мама мальчика с РАС (11 лет, зовут Алекс)
- 9 лет практики, 1000+ консультаций
- Работает по системе восстановления здоровья детей с особенностями развития немедикаментозными методами
- Не ставит диагнозы — идёт к причинам, а не к симптомам
- Образование: PreventAge Lifestyle School (2 года), Международная Академия Натуропатии (Майкл Мюррей, Джозеф Пицорно)

**Ключевые правила:**
- CTA всегда ведёт в **Telegram-канал @naturonata** (НЕ на консультации)
- Запрещённые слова: «аутист», «аутёнок»
- Тон: эмпатичный, поддерживающий, без жалости — с уважением
- Обращение на «ты»
- Публикации ежедневно, 1-3 раза/день

---

## 3. Аудитории (6 персон)

| # | Аудитория | Возраст ребёнка | Ключевая боль |
|---|-----------|-----------------|---------------|
| 1 | 🧒 Мамы: первые тревоги, свежий диагноз РАС/ЗПРР | 2-7 лет | Хаос рекомендаций, дефицит нутриентов |
| 2 | 🍽️ Мамы: избирательность в еде, ЖКТ, выгорание | 3-12 лет | 5 продуктов, запоры, нарушения сна |
| 3 | 🏥 Родители: ДЦП и/или эпилепсия | 1-14 лет | Дисфагия, кетодиета, медицинские риски |
| 4 | 👨 Папы и финансовые со-решатели | Мужчины 30-50 | Недоверие, неясные расходы |
| 5 | 👩‍⚕️ Логопеды и специалисты-рефереры | 25-55 | Фрагментарные знания, страх навредить |
| 6 | 🤝 Админы сообществ и родительские лидеры | 28-50 | Дефицит времени, фильтрация псевдонауки |

---

## 4. Форматы контента (8 типов)

| Формат | Ключ | Структура |
|--------|------|-----------|
| 🧩 Викторина | ВИКТОРИНА | Хук-вопрос → Варианты → Ответ → Объяснение → CTA |
| 📋 Пошаговый гайд | ГАЙД | Хук-обещание → Шаг 1 → ... → Итог → CTA |
| 💡 Лайфхак | ЛАЙФХАК | Хук-проблема → Лайфхак → Как работает → Результат → CTA |
| 🔥 Тренды | ТРЕНДЫ | Новость → Почему важно → Что делать → CTA |
| 🍽️ Меню/Еда | МЕНЮ | Хук-меню → День 1 → ... → Советы → CTA |
| 💬 История/Кейс | ИСТОРИЯ | Завязка → Развитие → Кульминация → Урок → CTA |
| 📊 Факты/Статистика | ФАКТЫ | Шок-факт → Контекст → Объяснение → CTA |
| ✅ Чек-лист | ЧЕК-ЛИСТ | Хук-чек-лист → Пункт 1 → ... → Бонус → CTA |

**v5 FIX:** выбор формата сохраняется в `session_state.selected_content_format` с ✅ и primary.

---

## 5. Архитектура программы

### Структура файлов v5.1

```
├── app.py              # Весь код ~1190 строк v5.1
├── assets/
│   ├── logo.png           # Логотип текстовый NATURONATA 150×200px 17KB
│   ├── cta_image.jpg      # CTA круглая иллюстрация 83KB
│   ├── cta_image.png      # Оригинал 2.2MB
│   ├── custom_bg_beige_with_logo.jpg      # NEW бежевый фон с логотипом 1080×1350 115KB
│   ├── custom_bg_beige_no_logo.jpg        # NEW бежевый фон без логотипа 102KB (рекомендуется)
│   ├── custom_bg_beige_with_logo_preview.jpg # превью 420×525
│   └── custom_bg_beige_no_logo_preview.jpg
├── requirements.txt
├── packages.txt
├── CONTEXT.md          # ОБНОВЛЯТЬ ПОСЛЕ КАЖДОГО ИЗМЕНЕНИЯ
└── README.md
```

### Ключевые функции

| Функция | Назначение |
|---------|-----------|
| `image_to_base64` | Загруженный файл → data URI |
| `file_path_to_base64` | Файл с диска → data URI |
| `embed_fonts_in_html` | Google Fonts → base64 для Playwright |
| `generate_carousel_content` | GPT-4o JSON сценарий |
| `analyze_reference_image` | GPT-4o Vision анализ референса |
| `generate_flux_image` | FLUX фоны |
| `build_carousel_html(..., custom_bg_b64, custom_bg_opacity, hide_logo_on_custom_bg)` | HTML превью v5.1 с поддержкой кастомного фона |
| `build_zip_export_html(..., custom_bg_b64, ...)` | ZIP экспорт с кастомным фоном |
| `export_slides_to_png` | Playwright экспорт |

### Новые константы v5/v5.1

```python
COLOR_PRESETS = {
  "🎨 Кастом": None,
  "🌙 Dark": {"accent": "#2FAD64", "headline": "#FFFFFF", "body": "#FFFFFF", "bg": "#1a1a2e"},
  "☀️ Light": {"accent": "#2FAD64", "headline": "#0f1419", "body": "#333333", "bg": "#F9F7F3"},
  "🤍 Minimal White": {...},
  "🌿 Deep Green": {...},
  "💫 Soft Pastel": {...},
}
# v5.1 custom background CSS (как логотип — один раз в CSS)
# .custom-bg{ background-image:url('data:...'); background-size:cover; opacity:{custom_bg_opacity} }
```

### Поток данных v5.1

```
Аудитория + Формат + Текст → GPT-4o → slides_data
        + 
Кастомный фон (опционально, base64 ONCE) → custom_bg_b64
        + 
Цвета (из пресета / пикера / референса) → headline_color/body_color/primary/bg
        + 
Логотип/CTA → logo_b64/cta_image_b64
                          ↓
               build_carousel_html / build_zip_export_html
                          ↓
                  Превью (html-to-image) / PNG (Playwright) → ZIP
```

---

## 6. Технические детали

### 6.1. Формат вывода GPT-4

JSON массив `[{type, headline, body, accent}]`

### 6.2. Промпт GPT-4

См. PROMPT.md, включает аудиторию, формат, CTA → @naturonata, фокус, правила, источник.

### 6.3. HTML-шаблон карусели v5.1

**Размеры:** превью 420×525, экспорт 1080×1350, scale 2.571

**Структура слайда v5.1:**
```
.slide (bg fallback цвет)
  ├── .custom-bg (NEW v5.1, если загружен кастомный фон, opacity из слайдера, z-index 0)
  ├── .bg-image (FLUX фон, opacity 0.2, если нет кастомного фона)
  ├── .slide-content
  │   ├── .slide-logo (если не hide_logo_on_custom_bg)
  │   ├── .slide-number
  │   ├── .slide-inner
  │   │   ├── badge, deco-line, h2.headline (color: headline_color), p.body-text (color: body_color), accent
  │   │   └── cta-image (последний слайд)
  │   └── brand-bar
  ├── progress-bar
  └── swipe-arrow
```

**Критически важно:**
- Логотип и кастомный фон — через CSS class с base64 **один раз**, не в каждом слайде. Это экономит мегабайты.
- `custom_bg_div = '<div class="custom-bg"></div>'` в каждом слайде, а CSS `.custom-bg{background-image:url(...)}` один раз.
- Если `has_custom_bg=True`, то `bg_img_div=""` (FLUX фоны отключаются) и `bg_style = background: {bg}` (fallback).

### 6.4. Playwright-экспорт

- viewport +400 buffer
- device_scale_factor
- fonts.ready + 3000ms
- JS распаковка carusel
- slide.screenshot()

Клиентский экспорт через `html-to-image@1.11.13 + jszip + FileSaver` — работает на Cloud и поддерживает custom background (так как кастомный фон — обычный div с background-image, он захватывается).

### 6.5. Цвета и стили v5

| Пикер | Ключ | Дефолт | Что красит |
|-------|------|--------|------------|
| Акцент | accent_picker | #2FAD64 | badge, deco-line, accent-text, progress, gradient To |
| Заголовок | headline_picker | #FFFFFF | headline, slide-number, brand-name |
| Основной текст | body_picker | #FFFFFF | body-text, brand-handle, progress-counter |
| Фон | bg_picker | #1a1a2e | secondary, bg, gradient From |

Логика:
```python
primary = s.get("primary_color", accent_color) or accent_color
secondary = s.get("secondary_color", bg_color) or bg_color
headline_color = s.get("text_color", text_dark) or text_dark
body_color = s.get("subtitle_color", text_body_color) or text_body_color
```
Референс имеет приоритет.

### 6.6. Форматы Instagram

1:1 1080×1080 square_hd, 4:5 1080×1350 portrait_4_5, 3:4 1080×1440 portrait_3_4

### 6.7. Пресеты цветов v5

`COLOR_PRESETS` dict, selectbox `color_preset`, session_state `last_preset`, `*_picker` ключи. При смене пресета — запись в session_state и rerun.

### 6.8. Кастомный фон v5.1 (NEW)

(см. выше — полный опис в файле сохранён, кратко: custom_bg_b64 ONCE CSS, hide_logo flag, opacity slider, примеры бежевых фонов)

### 6.9. Позиция логотипа v5.2 (NEW)

**Задача:** На примере бежевого фона логотип по центру сверху, а программа ставила всегда правый верх.

**Решение:**

1. **Константа LOGO_POSITIONS:**
```python
LOGO_POSITIONS = {
    "Правый верх (дефолт)": {"css": "top:28px; right:32px; left:auto; bottom:auto;", "bg_pos": "center right", "transform": ""},
    "Левый верх": {"css": "top:28px; left:32px;", "bg_pos": "center left"},
    "Центр верх (как на твоём бежевом фоне)": {"css": "top:28px; left:50%;", "bg_pos": "center", "transform": "transform:translateX(-50%);"},
    "Правый низ": {"css": "bottom:80px; right:32px;"},
    "Левый низ": {...},
    "Центр низ": {"css": "bottom:80px; left:50%;", "transform": "translateX(-50%);"},
}
```

2. **Sidebar:** `logo_position_choice = st.selectbox("Позиция логотипа", list(LOGO_POSITIONS.keys()), key="logo_position", help="Центр верх — как на твоём бежевом фоне")`

3. **Session State:** `logo_position` default "Правый верх (дефолт)"

4. **В build функциях:**
```python
pos_info = LOGO_POSITIONS.get(logo_position, LOGO_POSITIONS["Правый верх (дефолт)"])
logo_css = f".slide-logo{position:absolute;{pos_info['css']} {pos_info['transform']} height:38px; ... background-position:{pos_info['bg_pos']}; ...}"
```

5. **Совместимость:** Работает с кастомным фоном — можно выбрать "Центр верх" чтобы логотип был как на примере бежевого фона, или "Правый верх" для классики. Учитывает hide_logo_on_custom_bg.

### 6.10. Размер логотипа v5.3 (NEW)

**Задача:** Логотип был фикс 38px, пользователь захотел регулировать под бежевый фон (крупнее по центру).

**Решение:**
- `logo_size` в init_state default 38
- Slider в sidebar 20-80px key=logo_size
- `logo_css` height:{logo_size}px
- Передаётся в обе build функции

---

## 7. Известные проблемы и решения

### 7.1. Белый экран в Streamlit
HTML слишком большой из-за base64. Решение: логотип и кастомный фон через CSS один раз, уменьшенные картинки.

### 7.2. Шрифты в Playwright
Google Fonts не работает в headless. Решение: embed_fonts_in_html().

### 7.3. Обрезка правого края
Viewport +400 buffer.

### 7.4. Playwright не устанавливается
playwright install chromium.

### 7.5. Russian text на FLUX
FLUX только фоны, текст через HTML.

### 7.6. FIX v5: Формат сбрасывался в Викторину
session_state.selected_content_format + rerun + ✅ primary.

### 7.7. FIX v5: Цвета не работали
text_dark и text_body_color не использовались → теперь headline_color/body_color.

### 7.8. Пресеты цветов v5
COLOR_PRESETS + selectbox + session_state.

### 7.9. NEW v5.1: Кастомный фон для всех слайдов
Реализовано: file_uploader, custom_bg_b64 once CSS, hide_logo flag, opacity slider, примеры бежевых фонов.

---

## 8. API и зависимости

OpenAI gpt-4o ~$0.01-0.03 за карусель, fal.ai FLUX-2/Flash $0.005/MP, streamlit, openai, fal-client, Pillow, requests, playwright опционально.

---

## 9. Логотип, CTA и фоны

### 9.1. Логотип
assets/logo.png 150×200 17KB, CSS once.

### 9.2. CTA-изображение
assets/cta_image.jpg 83KB круг мама+мальчик.

### 9.3. Кастомный фон v5.1
- assets/custom_bg_beige_with_logo.jpg 1080×1350 115KB — оригинал примера с логотипом по центру
- assets/custom_bg_beige_no_logo.jpg 1080×1350 102KB — очищенная версия без логотипа (рекомендуется)
- Загрузка через sidebar "Фон для всех слайдов", checkbox hide_logo, opacity slider
- CSS once: .custom-bg

### 9.4. Замена файлов
Через UI или заменить в assets/. Для фона рекомендуется 1080×1350 без логотипа, до 200KB.

---

## 10. Roadmap

Приоритетные:
1. Редактирование слайдов после генерации
2. Сохранение истории
3. Batch-генерация
4. Шаблоны дизайна — частично v5 пресеты, v5.1 кастомные фоны ✅

Средние:
5. Настраиваемая позиция логотипа (в т.ч. центр как в примере фона)
6. Разные фоны для разных слайдов
7. Instagram-рамка превью
8. Автопостинг

Долгосрочные: мультиязычность, Reels, A/B.

---

## 11. Структура дашборда v5.1

Sidebar:
- API ключи
- Бренд
- Цвета: пресет selectbox (6) + 4 color_picker (теперь работают)
- Шрифт (8)
- FLUX модель
- Логотип и CTA
- **NEW Фон для всех слайдов**: uploader + checkbox hide_logo + opacity slider
- Фото профиля

Main: 6 шагов (аудитория, формат ✅, настройки, контент, изображения FLUX, генерация) + превью + экспорт (ZIP с поддержкой кастомного фона + Playwright)

---

## 12. Deploy

Streamlit Community Cloud рекомендуется. packages.txt fonts-liberation, fonts-noto-color-emoji. Railway/Render/HF Spaces альтернативы.

---

## 13. Локальный запуск

```bash
pip install streamlit openai fal-client Pillow requests playwright
playwright install chromium
python -m streamlit run app.py
```

---

## 14. История изменений

| Версия | Дата | Изменения |
|--------|------|-----------|
| v1 | 2026-07-27 | Базовый дашборд, GPT-4, FLUX, Playwright |
| v2 | 2026-07-28 | 6 аудиторий, 8 форматов |
| v3 | 2026-07-28 | Бренд интеграция, промпт с контекстом |
| v4 | 2026-07-28 | Логотип на каждом слайде, CTA на последнем, оптимизация HTML 2.5MB→50KB |
| v5 | 2026-07-30 | FIX формата (session_state), FIX цветов (headline/body), NEW пресеты цветов (Dark/Light/White/Deep Green/Pastel), sidebar help, 791→1056 строк |
| v5.1 | 2026-07-30 | **NEW кастомный фон для всех слайдов**: file_uploader custom_bg_upload + checkbox hide_logo_on_custom_bg + slider custom_bg_opacity + CSS once .custom-bg (как логотип) + логика has_custom_bg отключает FLUX и градиент + поддержка в обеих функциях build_carousel_html и build_zip_export_html + примеры фонов assets/custom_bg_beige_with_logo.jpg 115KB и custom_bg_beige_no_logo.jpg 102KB 1080×1350 + рекомендации без логотипа + совместимость с пресетами Light для светлого фона. 1056→1190 строк. |
| v5.2 | 2026-07-30 | **NEW позиция логотипа**: LOGO_POSITIONS dict (6 позиций: правый верх дефолт, левый верх, центр верх как на бежевом фоне, правый/левый/центр низ) + selectbox в sidebar key=logo_position + session_state + logo_css теперь использует pos_info['css'] + transform + bg_pos вместо хардкода top:28px;right:32px + поддержка в обеих функциях + совместимость с кастомным фоном (можно центр верх как на примере или правый верх). 1190→1213 строк. |
| v5.3 | 2026-07-30 | **NEW размер логотипа**: slider logo_size 20-80px step 2 key=logo_size default 38 + session_state + logo_css height:{logo_size}px вместо хардкода 38px + передача в build_carousel_html и build_zip_export_html + совместимость с позицией и кастомным фоном. 1213→1226 строк. |

---

## 15. Правила для следующего агента (ОБЯЗАТЕЛЬНО)

> После КАЖДОГО изменения сразу обновлять CONTEXT.md

1. Не ломать рабочее — хирургические diff.
2. session_state для формата и пресетов — сохранять.
3. Логотип и кастомный фон — через CSS ONCE (base64 один раз).
4. Цвета — headline_color/body_color из пикера, не хардкод.
5. Обновлять CONTEXT.md сразу.
6. Проверять `python -m py_compile app.py`
7. Для кастомного фона: если фон светлый — советовать пресет Light/Pastel для тёмного текста.

*Файл для передачи новому агенту. v5.1 от 30 июля 2026 — добавлена поддержка кастомного фона.*
