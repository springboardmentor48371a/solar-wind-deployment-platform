try:
    print("Starting import...")
    from app.main import app
    print("✅ Import successful!")
    import uvicorn
    print("✅ Uvicorn imported!")
    print("🚀 Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()