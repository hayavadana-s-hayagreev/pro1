def get_recommendations(crop: str, country: str, yield_level: str, rainfall: float, temp: float):
    recommendations = []
    
    # Basic rule-based recommendations
    if rainfall < 500:
        recommendations.append("💧 IRRIGATION: Low rainfall detected. Consider implementing drip irrigation systems to conserve water.")
    elif rainfall > 2000:
        recommendations.append("🌧️ CLIMATE: High rainfall detected. Ensure proper field drainage to prevent waterlogging and root rot.")
        
    if temp > 30:
        recommendations.append("☀️ CLIMATE: High temperatures may cause heat stress. Consider heat-tolerant varieties or shading techniques if applicable.")
    elif temp < 15:
        recommendations.append("❄️ CLIMATE: Low temperatures may slow growth. Use row covers or consider cold-hardy crop varieties.")
        
    if yield_level == "Low":
        recommendations.append("🌱 FERTILIZER: Predicted yield is low. Conduct a soil test to optimize NPK fertilizer application.")
        recommendations.append("🛡️ PEST: Review pesticide and integrated pest management (IPM) practices.")
    elif yield_level == "High":
        recommendations.append("🏆 EXCELLENT: Predicted yield is optimal. Maintain current agricultural practices.")
        
    # Crop specific advice
    if crop.lower() == "rice, paddy":
        recommendations.append("🌾 RICE: Maintain appropriate water levels in paddies, especially during the vegetative stage.")
    elif crop.lower() == "wheat":
        recommendations.append("🌾 WHEAT: Monitor for rust diseases, especially in humid conditions.")
        
    if len(recommendations) < 3:
        recommendations.append("💡 ALTERNATIVE: Consider crop rotation with legumes to naturally improve soil nitrogen levels.")
        
    return recommendations
