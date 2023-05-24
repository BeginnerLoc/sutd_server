from fastapi import APIRouter, Query
from config.database import db
from models.answer_model import Answer
from schemas.answer_schema import answer_serializer, answers_serializer
from utils.tokenize import to_words

answer_api_router = APIRouter()


# get
# get single answer using 2 params question_no and student_id
@answer_api_router.get("/api/get_answer/2018Midterm")
async def get_answer(question_no: str = Query(None), student_id: str = Query(None)):

    results = []
    if student_id and question_no:
        collection = db[f"2018MidtermQ{question_no}"]
        filter = {"student_id": student_id}
        results = answer_serializer(collection.find_one(filter))
    else:
        results = [{"error: cannot find matching data"}]
    
    return {"status": "ok", "data": results}

# get all
@answer_api_router.get("/api/get_answers/2018Midterm")
async def get_answers(question_no: str = Query(None)):

    results = []
    if question_no:
        collection = db[f"2018MidtermQ{question_no}"]
        results = answers_serializer(collection.find())
    else:
        results = [{"error: cannot find matching data"}]
    
    return {"status": "ok", "data": results}

# post
# submit studnet's code as string -> to be tokenized and store in database 
@answer_api_router.post("/api/submit_answer/2018Midterm")
async def submit_answer(answer: Answer):
    question_no = answer.question_no
    python_code = answer.python_code
    student_id = answer.student_id
    collection = db[f"2018MidtermQ{question_no}"]
    
    tokenized_code = to_words(python_code)    
    # tokenized_code = python_code

    print(tokenized_code)
    
    document = {
        'student_id': student_id,
        'tokenized_code': tokenized_code
    }
    
    result = collection.insert_one(document)
    
    if result.inserted_id:
        print("Document inserted successfully.")
    else:
        print("Failed to insert the document.")
   
    return {"status": "ok"}
 
# delete
@answer_api_router.delete("/api/delete_answer/2018Midterm")
async def delete_answer(question_no: str = Query(None), student_id: str = Query(None)):

    result = None

    if student_id and question_no:
        collection = db[f"2018MidtermQ{question_no}"]
        result = collection.delete_one({'student_id': student_id})
        if result.deleted_count == 1:
            result = f"Document with studentid {student_id} deleted successfully."
        else:
            result = f"No document found with studentid {student_id}."
    return {"status": "ok", "result": result}  



    
