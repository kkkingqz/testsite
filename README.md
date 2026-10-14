# KTAWF — сайт-візитка + інтеграція Cal.com (етап 3)

Адаптивний односторінковий статичний сайт на **HTML, CSS, JavaScript** без npm, фреймворків, бази даних і власного бекенду.

40 текстових блоків із `docs/content-source.csv` та сім графічних ресурсів із наданого користувачем `kkk.zip` уже інтегровані. Тексти, контакти та зображення демонстраційні; перед публікацією перевірте їхню точність і права використання.

**Cal.com:** у `public/assets/js/booking-config.js` уже підключено публічну подію **`https://cal.com/bogdan-n-usjpw6/consultation`**. Inline Embed показує реальні доступні години, а резервне посилання відкриває цю саму подію. **Тестове бронювання і синхронізація Google Calendar ще потребують перевірки в акаунті.** Інструкція: **[docs/stage3.md](docs/stage3.md)**.

## Швидкий старт

```sh
# У корені проєкту:
python3 -m http.server 8000 --directory public
# http://localhost:8000

python3 tests/smoke.py
node tests/booking-node.js
```

Жодної компіляції немає. Для тесту у браузері відкривайте сайт через локальний HTTP-сервер, а не через `file://`.

## Cal.com — налаштована подія

Посилання для запису: **https://cal.com/bogdan-n-usjpw6/consultation**.

1. Конфігурація URL уже заповнена у `public/assets/js/booking-config.js` — додаткове редагування HTML не потрібне.
2. У Cal.com перевірте тривалість зустрічі (на сайті поки зазначено **45 хв**), графік `Europe/Kyiv`, поля форми та сповіщення.
3. Перевірте синхронізацію з Google Calendar, пробну реальну бронь і її скасування.
4. Публікація сайту відбувається окремо: цей архів **не опубліковано на домені**.

Щоб вимкнути запис, змініть `eventUrl` на порожній рядок. Жодних API-ключів або секретів у JavaScript не потрібно.

## Структура

```text
business-website/
├── public/
│   ├── index.html
│   ├── privacy.html
│   ├── 404.html
│   ├── favicon.svg
│   └── assets/
│       ├── css/site.css
│       ├── js/
│       │   ├── site.js
│       │   ├── booking-config.js  <-- URL події Cal.com
│       │   └── booking.js         <-- автоматичний Cal.com Inline Embed
│       └── images/
│           ├── hero-art.webp
│           ├── gallery-01.webp
│           ├── gallery-02.webp
│           ├── gallery-03.webp
│           ├── logo.svg
│           └── og-image.jpg
├── docs/
│   ├── content.md
│   ├── content-source.csv
│   ├── images.md
│   └── stage3.md
├── tests/
│   ├── smoke.py
│   ├── booking-node.js
│   └── booking_browser.py     (опційний, вимагає Playwright)
└── README.md
```

## Що змінювати

- Тексти й SEO: `public/index.html`, див. `docs/content.md`.
- Зображення: замінюйте файли зі збереженням назв, див. `docs/images.md`.
- Календар: **тільки** `public/assets/js/booking-config.js`.
- Правила бронювання, календар і сповіщення змінюються **лише в Cal.com**, не в коді сайту.
- Для Cloudflare Pages: framework `None`, build command `exit 0`, output `public`, production branch `main`.

## Перед публікацією

1. Перевірити контактні дані та всі фактичні твердження з CSV.
2. Перевірити ліцензії зображень і фактичну відповідність фотографій компанії.
3. Перевірити справжню подію Cal.com (URL вже підключено) та зробити тестову повну бронь.
4. Замінити `https://example.com` для `og:image` на HTTPS-домен сайту.
5. Замінити демонстраційну **`privacy.html`** на реальну політику обробки персональних даних, до запуску реальних заявок.
6. Протестувати мобільну версію, email-повідомлення, календар Google, скасування, перенесення та резервне посилання.
# testsite
# testsite
