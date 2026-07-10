import sys
sys.path.insert(0, '.')
from api.main import app
import uvicorn

print('Starting FastAPI...')
print('Listen on: http://0.0.0.0:8000')

uvicorn.run(
    app,
    host='0.0.0.0',
    port=8000,
    log_level='info'
)
