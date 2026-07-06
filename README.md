🛒 OptiCart – AI-Powered Smart Shopping Platform

OptiCart is an intelligent e-commerce web application developed using Django that helps users make better purchasing decisions through AI-powered product recommendations, price comparison, review sentiment analysis, and an integrated shopping assistant chatbot.

The system combines machine learning, natural language processing, and modern web technologies to provide a personalized online shopping experience.

---

 ✨ Features

 👤 User Features

- User Registration & Login
- Secure Authentication
- User Profile Management
- Shopping Cart
- Wishlist
- Product Search
- Category-wise Product Browsing
- Product Reviews & Ratings


 🤖 AI Features

- AI Shopping Assistant Chatbot (Google Gemini)
- AI Product Score
- Review Sentiment Analysis
- Personalized Shopping Experience

 💰 Price Tracking

- Price Comparison
- Product Price History
- Automatic Price Synchronization
- Price Trend Analysis

🛠 Admin Features

- Product Management
- Category Management
- User Management
- Review Management


---

 💬 AI Chatbot

The project integrates **Google Gemini AI** using LangChain.

The chatbot can:

- Recommend products
- Answer shopping-related queries
- Help users navigate the website
- Provide product information
- Assist during shopping

---

 📊 Review Analysis

Customer reviews are analyzed to determine overall sentiment.

Possible sentiments include:

- Positive
- Neutral
- Negative

This helps customers make informed purchasing decisions.

---

 🛠 Tech Stack

 Frontend

- HTML5
- CSS3
- Bootstrap 5
- JavaScript

 Backend

- Python
- Django 5.2

 Database

- SQLite3

 AI & Machine Learning

- Scikit-learn
- Pandas
- NumPy
- LangChain
- Google Gemini API

 Other Libraries

- APScheduler
- Requests
- python-dotenv
- Joblib

---

 📂 Project Structure

```
Ecommerce/
│
├── cart/
├── chatbot/
├── Ecommerce/
├── media/
├── static/
├── templates/
├── manage.py
├── requirements.txt
└── db.sqlite3
```

---

 ⚙ Installation

 1. Clone Repository

```bash
git clone https://github.com/<your-username>/OptiCart.git
```

---

 2. Move into Project

```bash
cd OptiCart/Ecommerce
```

---

 3. Create Virtual Environment

 Windows

```bash
python -m venv venv
venv\Scripts\activate
```

 Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

 5. Configure Environment Variables

Create a `.env` file in the project directory.

Example:

```env
DJANGO_SECRET_KEY=your_secret_key

GOOGLE_API_KEY=your_google_gemini_api_key

EMAIL_HOST_USER=your_email

EMAIL_HOST_PASSWORD=your_password
```

---

 6. Apply Migrations

```bash
python manage.py makemigrations

python manage.py migrate
```

---

 7. Create Superuser

```bash
python manage.py createsuperuser
```

---

 8. Run Development Server

```bash
python manage.py runserver
```

Open:

```
http://127.0.0.1:8000/
```

---

 📦 Dependencies

- Django
- Scikit-learn
- NumPy
- Pandas
- LangChain
- Google Generative AI
- APScheduler
- Requests
- python-dotenv
- Joblib

---

🚀 Future Enhancements

- 📉 Price Drop Notifications
- 💰 Budget-Based Shopping Alerts
- 📱 Android & iOS Mobile App
- 🎙 Voice Shopping Assistant
- 🧾 Advanced Purchase Analytics
- 🔔 Personalized Deal Notifications
- 🌍 Multi-Vendor Marketplace Support
- 🧠 Deep Learning Recommendation Models

---

 🎓 Academic Objectives

- Django Web Development
- Machine Learning Integration
- Recommendation Systems
- Artificial Intelligence
- Natural Language Processing
- Database Design
- Full Stack Web Development

---

 📄 License

This project was developed as an MCA Major Project for educational purposes.

---

👨‍💻 Author
Sreeraj K Sajeevan

Master of Computer Applications (MCA)

---

