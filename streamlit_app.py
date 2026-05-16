"""
🌾 Crop Yield Estimator - Web Dashboard
Run: streamlit run streamlit_app.py
"""

import streamlit as st
import requests
import json
from pathlib import Path

st.set_page_config(page_title="🌾 Crop Yield Estimator", layout="wide")

API_URL = "http://localhost:8000"

st.sidebar.title("🌾 Crop Yield Estimator")
page = st.sidebar.radio("Navigate", ["🏠 Home", "🔮 Predict", "📊 Metrics"])

# ── Load known crops and countries ────────────────────────
@st.cache_data
def get_reference_data():
    crops_path = Path("models/known_crops.json")
    countries_path = Path("models/known_countries.json")
    crops = json.loads(crops_path.read_text()) if crops_path.exists() else ["Rice", "Wheat", "Maize"]
    countries = json.loads(countries_path.read_text()) if countries_path.exists() else ["India", "Brazil"]
    return crops, countries

KNOWN_CROPS, KNOWN_COUNTRIES = get_reference_data()

if page == "🏠 Home":
    st.title("🌾 Crop Yield Estimator")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Crops Supported", len(KNOWN_CROPS))
    with col2:
        st.metric("Countries Covered", len(KNOWN_COUNTRIES))
    with col3:
        st.metric("ML Models", "5")
    st.info(
        "This platform uses Machine Learning to predict crop yields and provides "
        "smart recommendations for irrigation, fertilization, pest management, "
        "and climate adaptation."
    )
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        if r.status_code == 200:
            st.success(f"✅ API Online | Model Loaded: {r.json().get('model_loaded', False)}")
        else:
            st.warning("⚠️ API running but may need model training")
    except:
        st.error("❌ API not running. Start it: `python main.py --mode serve`")

elif page == "🔮 Predict":
    st.title("🔮 Predict Crop Yield")
    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Crop Type", KNOWN_CROPS)
        country = st.selectbox("Country", KNOWN_COUNTRIES)
        year = st.number_input("Year", min_value=1961, max_value=2100, value=2025)
    with col2:
        rainfall = st.slider("Annual Rainfall (mm)", 50, 5000, 1200)
        pesticide = st.slider("Pesticide Usage (tonnes)", 0, 5000, 150)
        temperature = st.slider("Average Temperature (°C)", -5, 45, 28)
    
    if st.button("🌾 Predict Yield", type="primary", use_container_width=True):
        with st.spinner("Predicting..."):
            try:
                r = requests.post(f"{API_URL}/predict", json={
                    "crop": crop, "country": country, "rainfall": rainfall,
                    "pesticide": pesticide, "temperature": temperature, "year": year,
                }, timeout=30)
                if r.status_code == 200:
                    result = r.json()
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Predicted Yield", f"{result['predicted_yield_hg_ha']:,.0f} hg/ha")
                    with c2:
                        st.metric("Tonnes/Hectare", f"{result['predicted_yield_tonnes_ha']:.2f}")
                    with c3:
                        st.metric("Yield Level", result.get('yield_level', 'N/A'))
                    
                    st.markdown("### 💡 Recommendations")
                    for rec in result.get("recommendations", []):
                        if "IRRIGATION" in rec:
                            st.success(rec)
                        elif "FERTILIZER" in rec:
                            st.warning(rec)
                        elif "ALTERNATIVE" in rec:
                            st.info(rec)
                        elif "CLIMATE" in rec:
                            st.error(rec)
                        elif "PEST" in rec:
                            st.warning(rec)
                        else:
                            st.markdown(f"- {rec}")
                else:
                    st.error(f"Error: {r.text}")
            except requests.exceptions.ConnectionError:
                st.error("❌ API not running. Start it: `python main.py --mode serve`")
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "📊 Metrics":
    st.title("📊 Model Performance")
    try:
        r = requests.get(f"{API_URL}/metrics", timeout=5)
        if r.status_code == 200:
            data = r.json()
            best = min(data, key=lambda k: data[k].get("rmse", float("inf")))
            st.markdown(f"### Best Model: **{best}**")
            metrics = data[best]
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("RMSE", f"{metrics.get('rmse', 0):,.2f}")
            with c2:
                st.metric("MAE", f"{metrics.get('mae', 0):,.2f}")
            with c3:
                st.metric("R² Score", f"{metrics.get('r2', 0):.4f}")
            
            st.markdown("### All Models")
            import pandas as pd
            df_metrics = pd.DataFrame(data).T
            if not df_metrics.empty:
                st.dataframe(df_metrics.style.format("{:.2f}"), use_container_width=True)
        else:
            st.warning("No metrics yet. Train the model first.")
    except:
        st.error("Could not fetch metrics. Is the API running?")