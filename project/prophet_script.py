import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from prophet import Prophet
import datetime
import altair as alt


# הורדת נתונים מ-Yahoo Finance
start_date = "2024-01-01"
end_date = "2025-04-07"
data = yf.download('TA35.TA', start=start_date, end=end_date, auto_adjust=False)['Adj Close']
data.to_csv('GPRE.csv')

# חישוב תשואות יומיות (שינוי יחסי במחיר)
returns = data.pct_change().dropna()*100

# יצירת היסטוגרמה עם KDE עבור תשואות יומיות
plt.figure(figsize=(10, 5))
sns.histplot(returns, kde=True, bins=50, color='blue', alpha=0.6)
plt.title("התפלגות תשואות יומיות של GPRE")
plt.xlabel("תשואה יומית (%)")
plt.ylabel("תדירות")
plt.show()

# יצירת Boxplot עבור תשואות יומיות
plt.figure(figsize=(10, 5))
sns.boxplot(x=returns.squeeze(), color='green')  # שימוש ב-squeeze() כדי להפוך לוקטור חד-ממדי
plt.title("Boxplot של תשואות יומיות של GPRE")
plt.xlabel("תשואה יומית (%)")
plt.show()




# הגדרת טווח תאריכים (פורמט YYYY-MM-DD)
start_date = "2024-01-01"  # תאריך התחלה
end_date = "2025-04-07"    # תאריך סיום

# הורדת נתונים מ-Yahoo Finance

data = yf.download('TA35.TA', start=start_date, end=end_date, auto_adjust=False)['Adj Close']
data.to_csv('TA35.csv')
# עיבוד הנתונים לפורמט מתאים עבור Prophet
df = data.reset_index()[['Date', 'TA35.TA']]

df = df.rename(columns={'Date': 'ds', 'TA35.TA': 'y'})
df.to_csv('test.csv')
# מילוי ערכים חסרים ב-ffill ולאחר מכן ב-bfill
#df['y'] = df['y'].fillna(method='bfill').fillna(method='ffill')



model = Prophet(interval_width=0.95)  # 95% רווח סמך
#df['y'] = df['y'].fillna(method='ffill').fillna(method='bfill')


# התאמת המודל לנתונים
model.fit(df)

# יצירת תחזית קדימה ל-15 ימים
future = model.make_future_dataframe(periods=25, freq='D')

forecast = model.predict(future)

# הצגת התחזית
print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())

# הצגת גרף של התחזית
fig1 = model.plot(forecast)
fig2 = model.plot_components(forecast)

# יצירת DataFrame חדש עבור הגרף
plot_df = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].melt('ds', var_name='Metric', value_name='Price')

# יצירת גרף אינטראקטיבי עם Altair
chart = alt.Chart(plot_df).mark_line(point=True).encode(
    x='ds:T',
    y=alt.Y('Price:Q', title='מחיר'),
    color='Metric:N',
    tooltip=['ds', 'Price', 'Metric']
).properties(
    title='תחזית מחיר GPRE'
).interactive()

# שמירת הגרף כקובץ JSON
chart.save('GPRE_price_forecast.json')





# הגדרת טווח תאריכים (פורמט YYYY-MM-DD)
start_date = "2024-01-01"  # תאריך התחלה
end_date = "2025-04-07"    # תאריך סיום

# הורדת נתונים מ-Yahoo Finance

data = yf.download('TA35.TA', start=start_date, end=end_date, auto_adjust=False)['Adj Close']
data.to_csv('TA35.csv')
# עיבוד הנתונים לפורמט מתאים עבור Prophet
df = data.reset_index()[['Date', 'TA35.TA']]

df = df.rename(columns={'Date': 'ds', 'TA35.TA': 'y'})
df.to_csv('test.csv')
# מילוי ערכים חסרים ב-ffill ולאחר מכן ב-bfill
#df['y'] = df['y'].fillna(method='bfill').fillna(method='ffill')



model = Prophet(interval_width=0.95)  # 95% רווח סמך
#df['y'] = df['y'].fillna(method='ffill').fillna(method='bfill')


# התאמת המודל לנתונים
model.fit(df)

# יצירת תחזית קדימה ל-15 ימים
future = model.make_future_dataframe(periods=25, freq='D')

forecast = model.predict(future)

# הצגת התחזית
print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())

# הצגת גרף של התחזית
fig1 = model.plot(forecast)
fig2 = model.plot_components(forecast)

# יצירת DataFrame חדש עבור הגרף
plot_df = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].melt('ds', var_name='Metric', value_name='Price')

# יצירת גרף אינטראקטיבי עם Altair
chart = alt.Chart(plot_df).mark_line(point=True).encode(
    x='ds:T',
    y=alt.Y('Price:Q', title='מחיר'),
    color='Metric:N',
    tooltip=['ds', 'Price', 'Metric']
).properties(
    title='תחזית מחיר GPRE'
).interactive()

# שמירת הגרף כקובץ JSON
chart.save('GPRE_price_forecast.json')

import matplotlib.pyplot as plt

# נתונים מקוריים
plt.figure(figsize=(10, 6))
plt.plot(df['ds'], df['y'], 'k.', label='נתונים היסטוריים')  # נקודות שחורות

# נתוני תחזית
plt.plot(forecast['ds'], forecast['yhat'], 'b-', label='Future price')  # קו תחזית
plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color='blue', alpha=0.2, label='Future price range')  # תחום

# הגדרות גרף
plt.xlabel('תאריך')
plt.ylabel('מחיר')
plt.legend()
plt.grid(False)
plt.title('תחזית מול נתונים מקוריים')
plt.show()


forecast_only = forecast[forecast['ds'] > df['ds'].max()]

# יצירת גרף
plt.figure(figsize=(20, 15))

# נתוני תחזית בלבד
plt.plot(forecast_only['ds'], forecast_only['yhat'], 'b-', label='תחזית')  # קו תחזית
plt.fill_between(forecast_only['ds'], forecast_only['yhat_lower'], forecast_only['yhat_upper'], color='blue', alpha=0.2, label='טווח אי-ודאות')  # תחום אי-ודאות

# הגדרות גרף
plt.xlabel('תאריך')
plt.ylabel('מחיר')
plt.legend()
plt.grid(False)
plt.title('תחזית מחיר (מתחילת תחזית בלבד)')
plt.show()


start_date = "2022-01-01"
end_date = "2025-04-02"
data = yf.download('TA35.TA', start=start_date, end=end_date, auto_adjust=False)['Adj Close']

# Prepare the DataFrame for Prophet
df = data.reset_index()[['Date', 'TA35.TA']]
df = df.rename(columns={'Date': 'ds', 'TA35.TA': 'y'})

# Fill missing values with forward fill (ffill) and backward fill (bfill)
#df['y'] = df['y'].fillna(method='bfill').fillna(method='ffill')

# Load the holidays CSV
holidays = pd.read_csv('/content/Jewish_Israeli_holidays.csv')

# Convert 'date' to datetime and rename columns correctly for Prophet
holidays['ds'] = pd.to_datetime(holidays['date'], format='%m/%d/%Y')
holidays = holidays.rename(columns={'eng_name': 'holiday'})

# Keep only necessary columns for Prophet
holidays = holidays[['ds', 'holiday']]

# Initialize and fit the Prophet model with holidays
model = Prophet(holidays=holidays, interval_width=0.99)
model.fit(df)

# Create a future dataframe for prediction (30 days ahead)
future = model.make_future_dataframe(periods=25, freq='D')
forecast = model.predict(future)

# Show the forecast for the last 5 days
print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())

# Plot the forecast
fig1 = model.plot(forecast)
fig2 = model.plot_components(forecast)