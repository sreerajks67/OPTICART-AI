# OptiCart — AI Shopping Decision Agent

Django web app for smart shopping: price comparison, ML price hints, AI agent logs, simulated checkout, and Gemini chatbot.

## Setup

1. **Create virtual environment** (do not use committed `hello/` folder):

```bash
cd Ecommerce
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment variables** — copy `.env.example` to `.env` and set:

- `DJANGO_SECRET_KEY`
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` (optional, for mail)
- `GOOGLE_API_KEY` in `.env` or `key.env` (for chatbot)

3. **Database & data**:

```bash
python manage.py migrate
python import_data.py
python manage.py reclassify_products --delete-empty
python manage.py sync_product_prices
python ml/train_model.py
```

**Prices:** `current_price` and `price_day_1`–`10` come from the CSV. `old_price` is the peak of the 10-day history only when it is above the current price (no random markup). Re-run `sync_product_prices` after imports.

**Categories:** Products are mapped into 10 standard categories (Electronics, Fashion, Home & Furniture, etc.). Re-run `reclassify_products` after bulk imports.

4. **Run server**:

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Default flows

- **User**: Register → Login → Browse products → Compare → Product detail (ML chart) → Cart → Checkout (simulated order)
- **Admin**: Register once at `/admin_register/` → Login → `/admin_login/` dashboard
- **AI**: Nav → AI → search logs; admin can `/run-agent/` to evaluate products

## Project layout

| Path | Purpose |
|------|---------|
| `cart/` | Models, views, agent utils |
| `ml/` | Train & load price prediction model |
| `chatbot/` | LangChain + Gemini |
| `service/` | Chatbot product filtering |
| `Templates/` | HTML UI |
| `datasets/` | Amazon & Flipkart CSV imports |

## Notes

- Orders are **simulated** (`is_simulated=True`); no real payments.
- Product images use external URLs (proxied for Amazon/Flipkart).
- Agent runs on a schedule (every 6 hours) and processes 100 random products per run; logs capped at 5000 rows.
