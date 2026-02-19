from sqlalchemy import create_engine
import traceback

try:
    engine = create_engine(
        "mysql+pymysql://survey_testing:Peng1234@127.0.0.1:3308/survey_testing",
        connect_args={"connect_timeout": 5},
    )
    conn = engine.connect()
    print("✅ SUCCESS: Connected to database!")
    conn.close()
    engine.dispose()
except Exception as e:
    print(f"❌ ERROR: {e}")
    traceback.print_exc()
