from fastapi import APIRouter, Query, HTTPException
from config.database import db
from models.answer_model import Answer
from schemas.answer_schema import answer_serializer, answers_serializer
from utils.tokenize import to_words
from datetime import datetime, timedelta
from utils.codedist import calculate_code_distance

answer_api_router = APIRouter()


import httpx
from utils.tokenize import to_words

from fastapi import status

@answer_api_router.post("/api/submit_answer_file")
async def submit_answer_file(answer: Answer):
    
    now = datetime.now()
    
    try:
        question_no = answer.question_no
        answer_file_url = answer.python_code
        student_id = answer.student_id
        module_code = answer.module_code
        current_year = datetime.now().year
        
        collection_name = f"{current_year}{module_code}Q{question_no}"
        if collection_name not in db.list_collection_names():
            # When there is no collection matched the submitted question
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in the database")
        
        collection = db[collection_name]
        document = collection.find_one({ 'deadline': { '$exists': True } })
        # Retrieve the deadline from the lecturer's answer
        deadline = document['deadline']
        
        if now >= deadline:
            # The submission deadline is over
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The submission deadline is over")
        
        # Download the answer file using the answer_file_url
        async with httpx.AsyncClient() as client:
            response = await client.get(answer_file_url)
            if response.status_code != status.HTTP_200_OK:
                # Unable to retrieve the code from the cloud
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to retrieve the code from cloud")
            
            python_code = response.text

        # Tokenize the Python code
        tokenized_code = to_words(python_code)

        document = {
            'student_id': student_id,
            'tokenized_code': tokenized_code,
            'submitted': now
        }

        result = collection.insert_one(document)

        if result.inserted_id:
            return {"status": "ok", "message": "Document inserted successfully."}
        else:
            # Unable to save the code
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save the code")
    
    except Exception as e:
        # Any other exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@answer_api_router.get("/api/calculate_distance")
async def calculate_distance(student_id, year, module_code, question_no):
    try:
        collection_name = f"{year}{module_code}Q{question_no}"
        if collection_name not in db.list_collection_names():
            # When there is no collection matched the submitted question
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in the database")
        
        list_of_code = [] # contains all tokenized_code
        student_id_list = [] # this list aligns with the code list
        
        collection = db[collection_name]
        print(collection_name)
        
        documents = collection.find({'tokenized_code': {'$exists': True}})
        for document in documents:
            tokenized_code = document['tokenized_code']
            if student_id == document['student_id']:
                list_of_code.insert(0, tokenized_code)
                student_id_list.insert(0, document['student_id'])
                # tokenized_code with the matched student_id is always placed at index 0
            else:
                list_of_code.append(tokenized_code)
                student_id_list.append(document['student_id'])
        result = calculate_code_distance(list_of_code)
        print(f"Closest file to Student's answer is '???' with a distance of {result}.")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get
# get single answer using 2 params question_no and student_id
# @answer_api_router.get("/api/get_answer/2018/midterm")
# async def get_answer(question_no: str = Query(None), student_id: str = Query(None)):
#     results = []
#     if student_id and question_no:
#         collection = db[f"2018MidtermQ{question_no}"]
#         filter = {"student_id": student_id}
#         results = answer_serializer(collection.find_one(filter))
#     else:
#         results = [{"error": "cannot find matching data"}]
#     return {"status": "ok", "data": results}

# get all
# @answer_api_router.get("/api/get_answers/2018/midterm")
# async def get_answers(question_no: str = Query()):
#     results = []
#     if question_no:
#         collection = db[f"2018MidtermQ{question_no}"]
#         results = answers_serializer(collection.find())
#     else:
#         results = [{"error": "cannot find matching data"}]
#     return {"status": "ok", "data": results}

# post
# submit student's code as string -> to be tokenized and stored in the database
# @answer_api_router.post("/api/submit_answer/2018/midterm")
# async def submit_answer(answer: Answer):
#     try:
#         question_no = answer.question_no
#         python_code = answer.python_code
#         student_id = answer.student_id
#         collection = db[f"2018MidtermQ{question_no}"]

#         tokenized_code = to_words(python_code)
#         # tokenized_code = python_code

#         print(tokenized_code)

#         document = {
#             'student_id': student_id,
#             'tokenized_code': tokenized_code
#         }

#         result = collection.insert_one(document)

#         if result.inserted_id:
#             print("Document inserted successfully.")
#         else:
#             print("Failed to insert the document.")

#         return {"status": "ok"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# submit answer in file

# delete
# @answer_api_router.delete("/api/delete_answer/2018/midterm")
# async def delete_answer(question_no: str = Query(None), student_id: str = Query(None)):
#     try:
#         result = None

#         if student_id and question_no:
#             collection = db[f"2018MidtermQ{question_no}"]
#             result = collection.delete_one({'student_id': student_id})
#             if result.deleted_count == 1:
#                 result = f"Document with studentid {student_id} deleted successfully."
#             else:
#                 result = f"No document found with studentid {student_id}."
#         return {"status": "ok", "result": result}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

