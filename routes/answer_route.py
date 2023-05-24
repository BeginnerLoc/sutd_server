from fastapi import APIRouter, Query
from config.database import db
from models.answer_model import Answer
from schemas.answer_schema import answer_serializer, answers_serializer


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



#tokenize string
import io
from tokenize import generate_tokens, TokenInfo

def to_words(python_code):
    tokenized_code = io.StringIO()
    l = {0: "(EOF)", 4: "(NEWLINE)", 5: "(INDENT)", 6: "(DEDENT)", 59: "(ERROR)"}
    code_lines = python_code.splitlines()
    for line in code_lines:
        tokens = generate_tokens(io.StringIO(line).readline)
        line_tokens = [l.get(token.type, token.string) if token.type != 3 else token.string.replace("\n", "\\n") for token in tokens if token.type < 60]
        tokenized_code.write("\n".join(line_tokens) + "\n")
    return tokenized_code.getvalue()  
    
