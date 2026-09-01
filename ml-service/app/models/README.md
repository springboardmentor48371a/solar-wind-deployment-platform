# Model Files

Trained model files are stored in this directory:

- `solar_model2.pkl`     — XGBoost solar capacity factor model (10 features, Module 5)
- `wind_model.pkl`       — XGBoost wind power estimator (10 features from SCADA, Module 6)
- `land_cover_model.pkl` — XGBoost land cover bridge model (3 features, Module 4)
- `land_cover_cnn.pth`   — PyTorch CNN land cover classifier (Module 4)
- `forecast_model.pt`    — PyTorch LSTM energy forecaster (Module 8 - placeholder/paused)

These binary files are gitignored due to size. They are trained on Kaggle and copied/mounted here.

