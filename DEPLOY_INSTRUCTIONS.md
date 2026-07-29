# 🚀 Пошаговая инструкция: деплой Naturonata Carousel Generator

## ЧТО НУЖНО ЗАРАНЕЕ

1. **Аккаунт на GitHub** — у вас есть ✅
2. **Аккаунт на Google** — для входа на Streamlit Cloud (или войти через GitHub)

---

## ШАГ 1: Создать репозиторий на GitHub

1. Откройте **https://github.com** и войдите в свой аккаунт
2. Нажмите кнопку **«+»** в правом верхнем углу → **«New repository»**
3. Заполните:
   - **Repository name:** `naturonata-carousel`
   - **Description:** `Instagram Carousel Generator for Naturonata`
   - **Private** ✅ (выберите Private — это ваш приватный репозиторий)
   - ❌ НЕ ставьте галочку «Add a README file»
   - ❌ НЕ ставьте галочку «Add .gitignore»
   - ❌ НЕ выбирайте «Choose a license»
4. Нажмите **«Create repository»**
5. Вы увидите страницу с инструкциями — **закройте её**, мы загрузим файлы по-другому

---

## ШАГ 2: Загрузить файлы в репозиторий

Вы будете загружать файлы **через веб-интерфейс GitHub** (без командной строки):

### 2.1. Скачайте ZIP-файл

Я подготовил ZIP-файл со всеми файлами. Скачайте его из Arena.ai и распакуйте на своём компьютере.

### 2.2. Загрузите каждый файл

В вашем репозитории на GitHub (`https://github.com/ВАШ_ЛОГИН/naturonata-carousel`):

1. Нажмите **«Add file»** → **«Upload files»**
2. Перетащите **ВСЕ файлы** из распакованной папки в окно загрузки
3. **Структура должна быть такой:**

```
naturonata-carousel/
├── .gitignore
├── .streamlit/
│   └── config.toml
├── app.py
├── assets/
│   ├── cta_image.jpg
│   └── logo.png
├── CONTEXT.md
├── packages.txt
├── README.md
└── requirements.txt
```

4. Внизу страницы в поле **«Commit changes»** напишите: `Initial commit`
5. Нажмите **«Commit changes»** (зелёная кнопка)

⚠️ **ВАЖНО:** Файл `.gitignore` — скрытый файл (начинается с точки). Если GitHub не даёт его загрузить через веб — НЕ страшно, без него всё работает.

### 2.3. Как загрузить папки (.streamlit и assets)

GitHub не позволяет загрузить папку напрямую. Вот как это сделать:

**Для папки `.streamlit/`:**
1. В репозитории нажмите **«Add file»** → **«Create new file»**
2. В поле имени файла напишите: `.streamlit/config.toml`
3. В поле содержимого вставьте текст из файла `config.toml`
4. Нажмите **«Commit changes»**

**Для папки `assets/`:**
1. В репозитории нажмите **«Add file»** → **«Upload files»**
2. Перетащите файлы `logo.png` и `cta_image.jpg`
3. GitHub автоматически создаст папку `assets/`
4. Нажмите **«Commit changes»**

---

## ШАГ 3: Задеплоить на Streamlit Community Cloud

1. Откройте **https://share.streamlit.io**
2. Нажмите **«Sign in»** → войдите через **GitHub**
3. После входа нажмите **«New app»** (или «Deploy an app»)
4. Заполните:
   - **Repository:** выберите `naturonata-carousel` из выпадающего списка
   - **Branch:** `main`
   - **Main file path:** `app.py` (должно быть уже заполнено)
   - **App URL** (опционально): `naturonata-carousel` (это будет ваш URL)
5. Нажмите **«Deploy!»** (зелёная кнопка внизу)

### Что произойдёт:

- Streamlit Cloud начнёт сборку (2-5 минут в первый раз)
- Установит Python-зависимости из `requirements.txt`
- Установит системные библиотеки из `packages.txt`
- Запустит приложение
- Вы увидите прогресс-бар, а потом — ваш дашборд!

### Ваш URL будет:

```
https://naturonata-carousel.streamlit.app
```

(или с вашим логином: `https://ВАШ_ЛОГИН-naturonata-carousel.streamlit.app`)

---

## ШАГ 4: Введите API ключи

Когда дашборд откроется:

1. В **боковой панели** (слева) введите:
   - **OpenAI API Key** — для генерации текста
   - **fal.ai API Key** — для генерации изображений (опционально)
2. Начните создавать карусели! 🎉

---

## ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

### Приложение не загружается
- Проверьте, что файл `app.py` загружен в корень репозитория
- Проверьте, что `requirements.txt` загружен
- Зайдите в **Settings** → **Logs** на Streamlit Cloud — там будут ошибки

### PNG-экспорт не работает
- Playwright может не работать на Streamlit Cloud из-за ограничений памяти
- Превью карусели в HTML будет работать всегда
- Для PNG-экспорта используйте локальный запуск (см. ниже)

### Ошибка «Module not found»
- Добавьте недостающий пакет в `requirements.txt`
- Закоммитьте изменения → Streamlit Cloud пересоберёт автоматически

---

## ЛОКАЛЬНЫЙ ЗАПУСК (альтернатива)

Если Streamlit Cloud не подходит:

```bash
# 1. Установите Python 3.9+ (python.org)
# 2. Откройте терминал/командную строку
# 3. Перейдите в папку с распакованными файлами
cd путь/к/naturonata-carousel

# 4. Установите зависимости
pip install -r requirements.txt
playwright install chromium

# 5. Запустите
python -m streamlit run app.py

# 6. Откройте http://localhost:8501
```

---

## ОБНОВЛЕНИЕ КОДА

Если вы изменили код на GitHub:

1. Streamlit Cloud **автоматически** пересоберёт приложение
2. Если нет — нажмите **«Reboot app»** в меню на Streamlit Cloud

---

## СТРУКТУРА ПРОЕКТА

```
naturonata-carousel/
├── .gitignore              # Список файлов, которые не загружать на GitHub
├── .streamlit/
│   └── config.toml         # Настройки Streamlit (тёмная тема)
├── app.py                  # Главный файл дашборда (812 строк)
├── assets/
│   ├── logo.png            # Логотип Naturonata (на каждом слайде)
│   └── cta_image.jpg       # CTA-изображение (на последнем слайде)
├── CONTEXT.md              # Полная документация для разработчика
├── packages.txt            # Системные библиотеки (для Streamlit Cloud)
├── README.md               # Краткое описание
└── requirements.txt        # Python-зависимости
```
