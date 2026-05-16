🌾 Crop Yield Estimator
Intelligent agriculture prediction platform using Machine Learning.

Quick Start
# 1. Setuppython -m venv venvvenv\Scripts\activate        # Windowspip install -r requirements.txt# 2. Place dataset in data/raw/yield_df.csv# 3. Train the modelpython main.py --mode train# 4. Test a predictionpython main.py --mode predict# 5. Start the APIpython main.py --mode serve# Open http://localhost:8000/docs# 6. Start the dashboardstreamlit run streamlit_app.py# Open http://localhost:8501
API Endpoints
Endpoint	Method	Description
/predict	POST	Predict crop yield
/metrics	GET	Model performance
/health	GET	Health check
/recommendations	POST	Agricultural advice
Example
curl -X POST http://localhost:8000/predict \  -H "Content-Type: application/json" \  -d '{"crop":"Rice","country":"India","rainfall":1200,"pesticide":150,"temperature":28,"year":2025}'