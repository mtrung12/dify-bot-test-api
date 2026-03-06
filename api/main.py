from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from uuid_utils import uuid4

api = FastAPI()

@api.post("/bot-test")
async def start_test(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    if not file.filename.endswith('.xlxs'):
        return HTTPException(status_code=400, detail="Invalid file type. Please upload an .xlxs file.")
    request_id = str(uuid4())
    file_path = f"/tmp/{request_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    if background_tasks:
        background_tasks.add_task(process_file, request_id, file_path)
    return {"request_id": request_id}

def process_file(request_id, file_path):
    print(f"Processing file {file_path} for request {request_id}")
    
@api.get("/bot-test/{request_id}")
async def get_test_result(request_id: str):
    return {"request_id": request_id, "status": "completed", "result": "Test result data here"}
    