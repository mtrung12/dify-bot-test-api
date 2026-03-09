import os
import uuid
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, Header
from fastapi.responses import FileResponse
from .utils import call_dify_api
from sentence_transformers import SentenceTransformer, util

api = FastAPI()

RESULTS_DIR = "/tmp/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

similarity_model = SentenceTransformer('dangvantuan/vietnamese-embedding')
request_keys = {}

@api.post("/bot-test")
async def start_test(background_tasks: BackgroundTasks, file: UploadFile = File(...), dify_api_key: str = Header(None)):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an .xlsx file.")
    
    request_id = str(uuid.uuid4())
    file_path = f"/tmp/{request_id}_{file.filename}"
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
    request_keys[request_id] = dify_api_key
    
    if background_tasks:
        background_tasks.add_task(process_file, request_id, file_path)
        
    return {"request_id": request_id, "message": "Test processing started in the background."}

def evaluate_answer(bot_answer, expected_answer):
    if pd.isna(expected_answer) or str(expected_answer).strip() == "":
        return "N/A", None
    
    bot_str = str(bot_answer).strip().lower()
    exp_str = str(expected_answer).strip().lower()
    
    if not bot_str or not exp_str:
        return "N/A", None
    
    emb_bot = similarity_model.encode(bot_str)
    emb_exp = similarity_model.encode(exp_str)
    similarity_score = util.cos_sim(emb_bot, emb_exp)[0][0].item()
    
    evaluation = "Đúng" if similarity_score >= 0.5 else "Sai"
    
    return evaluation, round(similarity_score, 4)

def process_file(request_id, file_path):
    print(f"Processing file {file_path} for request {request_id}")
    try:
        df = pd.read_excel(file_path)
        bot_answers = []
        evaluations = []
        scores = [] # New list to store similarity scores
        
        dify_conversation_mapping = {}
        request_api_key = request_keys.get(request_id)
        
        for index, row in df.iterrows():
            message = row.get('message')
            agent_id = row.get('agent_id', None)
            expected_answer = row.get('expected_answer', None) 
            
            raw_conv_id = row.get('conversation_id')
            
            if pd.isna(message) or str(message).strip() == "":
                bot_answers.append("")
                evaluations.append("")
                scores.append(None) # Keep list lengths consistent
                continue
            
            if pd.notna(raw_conv_id) and str(raw_conv_id).strip() != "":
                excel_conv_id = str(raw_conv_id).strip()
                
                if excel_conv_id in dify_conversation_mapping:
                    dify_conv_id = dify_conversation_mapping[excel_conv_id]
                else:
                    dify_conv_id = ""
            else:
                excel_conv_id = None
                dify_conv_id = ""
                
            try:
                answer, new_dify_conv_id = call_dify_api(dify_conv_id, message, request_api_key)
                
                if excel_conv_id and excel_conv_id not in dify_conversation_mapping:
                    dify_conversation_mapping[excel_conv_id] = new_dify_conv_id
                
                bot_answers.append(answer)
                
                # Unpack the tuple returned from evaluate_answer
                evaluation, score = evaluate_answer(answer, expected_answer)
                evaluations.append(evaluation)
                scores.append(score)
                
            except Exception as e:
                bot_answers.append(f"Error: {str(e)}")
                evaluations.append("Lỗi API")
                scores.append(None) # Append None if there was an API error

        df['bot_answer'] = bot_answers
        df['evaluation'] = evaluations
        df['score'] = scores # Add the scores array as a new column
        
        result_path = os.path.join(RESULTS_DIR, f"{request_id}_result.xlsx")
        df.to_excel(result_path, index=False)
        print(f"Finished processing request {request_id}. Result saved.")
        
    except Exception as e:
        print(f"Failed to process {request_id}: {e}")

@api.get("/bot-test/{request_id}")
async def get_test_result(request_id: str):
    result_path = os.path.join(RESULTS_DIR, f"{request_id}_result.xlsx")
    
    if os.path.exists(result_path):
        return FileResponse(
            path=result_path, 
            filename=f"test_result_{request_id}.xlsx",
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    return {"request_id": request_id, "status": "processing_or_failed", "message": "Result is not ready yet."}