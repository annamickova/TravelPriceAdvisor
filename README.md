# Travel Advisor
---

# 1. Decision Table (Technologies & Architecture)

## 1.1 Overview
The project is a system that:
- Collects flight, bus/train, weather and holiday data
- Cleans and merges datasets
- Trains a machine learning model (XGBoost classifier)
- Serves predictions via Streamlit web application

---

## 1.2 Technology Decision Table

| Layer | Technology | Purpose | Why chosen | Alternatives |
|------|------------|--------|------------|--------------|
| Data collection (flights) | Python + Playwright | Scraping Ryanair flight prices | Handles dynamic JS pages, reliable scraping | Selenium, Scrapy |
| Data collection (bus/train) | requests + RegioJet API | Fetch bus/train connections | Public API, no auth required | Selenium scraping, paid APIs |
| Weather data | Open-Meteo API | Weather forecasts per destination | Free, no API key, reliable | Visual Crossing, OpenWeatherMap |
| Holidays data | Nager.Date API + manual MŠMT data | Public holidays + school breaks | Free API + local accuracy | Google Calendar API |
| Data processing | Pandas | Cleaning, merging, feature engineering | Industry standard for tabular data | Polars, Spark |
| ML model | XGBoost Classifier | Predict BUY_NOW / WAIT / EXPENSIVE | High accuracy, handles non-linear data well | RandomForest, LightGBM |
| Baseline model | RandomForestClassifier | Comparison / fallback | Simple and interpretable | Logistic Regression |
| Encoding | One-hot encoding (pandas get_dummies) | Convert categorical variables | Simple and effective for tree models | Target encoding |
| Scaling | MinMaxScaler (sklearn) | Normalize numeric features | Required for consistent ML input | StandardScaler |
| Label encoding | LabelEncoder | Convert target labels to numeric | Required for XGBoost | Manual mapping |
| Model tuning | GridSearchCV | Hyperparameter optimization | Systematic search, cross-validation | RandomizedSearchCV |
| Visualization | Matplotlib + Seaborn | Analysis plots | Easy integration | Plotly |
| Dashboard | Streamlit | Web UI for predictions | Fast development, Python-based | Flask + React |
| Charts in app | Plotly | Interactive charts | Better UX than matplotlib in web apps | Altair |
| Model persistence | Joblib | Save model, scaler, encoder | Standard for sklearn models | Pickle |
| Scheduling scrapers | schedule library | Periodic data updates | Simple cron-like scheduling | Airflow, cron |

---

## 1.3 System Architecture

```
Scrapers:
- Ryanair (Playwright)
- RegioJet API
- Weather API (Open-Meteo)
- Holidays API (Nager.Date + MŠMT)
        
Raw CSV datasets - Data preprocessing (Pandas) - Feature engineering - Merging dataset - XGBoost model training - Saving model (joblib) - Streamlit application - User prediction interface
```

---

# 2. README.md

## 2.1 Project Title

**Travel Price Advisor – ML-based flight & transport price prediction system**

---

## 2.2 Project Description

This project predicts whether it is the best time to buy a travel ticket based on:
- Flight prices (Ryanair)
- Bus/train prices (RegioJet)
- Weather conditions
- Public holidays & school breaks
- Time before departure

The system classifies prices into three categories:
- BUY_NOW(green color) – ticket is cheap
- WAIT(yellow color) – price may drop
- EXPENSIVE(red color) – overpriced

---

## 2.3 Features

- Data scraping from multiple sources
- Data merging (flight + bus + weather + holidays)
- Feature engineering (seasonality, holidays, time features)
- Machine learning classification model (XGBoost)
- Interactive Streamlit dashboard
- Alternative date recommendations
- Price trend visualization

---

## 2.4 Installation

### Requirements
```bash
pip install pandas numpy scikit-learn xgboost streamlit plotly joblib requests schedule playwright
playwright install
```

---

## 2.6 How to Run
## 2.6.1 Using PyCharm

### 1. Dowload project from GitHub and open in PyCharm
### 2. Run data collection
```bash
python scraper_ryanair.py
python scraper_regiojet.py
python scraper_weather.py
python scraper_holidays.py
```

### 3. Train model (Google Colab)
- Run notebook
- Outputs saved in Colab
- Load saved model into app in ide

### 4. Run Streamlit app
```bash
streamlit run app.py
```
## 2.6.2 In terminal
### Prerequisites
Python 3.9 or higher installed on your system.

Your project folder should contain: app.py, lib.py, requirements.txt, and the data/, model/ folders.

### Windows
### 1. Open Terminal: Navigate to your project folder in Command Prompt or PowerShell.
### 2. Create Virtual Environment:
```bash
python -m venv venv
```
### 3. Activate Environment:
```bash
venv\Scripts\activate
```
### 4. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 5. Run Application:
```bash
streamlit run app.py
```

### MacOS
### 1. Open Terminal: Navigate to your project folder.
### 2. Create Virtual Environment:
```bash
python3 -m venv venv
```
### 3. Activate Environment:
```bash
venv\Scripts\activate
```
### 4. Install Dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run Application:
```bash
python3 -m streamlit run app.py
```

### Linux (Ubuntu/Debian)
### 1. Open Terminal: Navigate to your project folder.
### 2. Update System & Install Venv:
```bash
sudo apt update
sudo apt install python3-venv
```
### 3. Create & Activate Environment:
```bash
python3 -m venv venv
source venv/bin/activate
```
### 4. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 5. Run Application:
```bash
streamlit run app.py
```
---

## 2.7 Machine Learning Pipeline

1. Data cleaning
2. Feature engineering:
   - season
   - holiday flag
   - weekend flag
   - time features
3. Encoding:
   - One-hot encoding
4. Scaling:
   - MinMaxScaler
5. Model:
   - XGBoost classifier
6. Evaluation:
   - accuracy
   - confusion matrix
   - cross-validation

---

## 2.8 Model Output Logic

The model predicts:

| Label | Meaning |
|------|--------|
| BUY_NOW | price is below average - good time to buy |
| WAIT | uncertain trend - wait |
| EXPENSIVE | price above average - avoid |

---

## 2.9 Key Insights from Data

- Prices depend on days until departure
- Mid-week flights are cheaper
- Holidays increase prices significantly
- Certain destinations have stable pricing patterns

---

## 2.10 Future Improvements

- Replace GridSearchCV with Bayesian optimization
- Add LightGBM / CatBoost comparison
- Add real-time API inference endpoint (FastAPI)
- Improve weather forecasting accuracy integration
- Add user personalization layer

