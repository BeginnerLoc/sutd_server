from fastapi import APIRouter, Response, status
from config.database import db
from models.answer_model import Answer
from utils.tokenize import to_words
from datetime import datetime
from utils.codedist import calculate_code_distance

answer_api_router = APIRouter()


import httpx
from utils.tokenize import to_words


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
            response = Response(content="Question not found in the database", status_code=404)
            return response
        
        collection = db[collection_name]
        document = collection.find_one({ 'deadline': { '$exists': True } })
        deadline = document['deadline']
        
        if now >= deadline:
            response = Response(content="The submission deadline is over", status_code=404)
            return response
        
        async with httpx.AsyncClient() as client:
            response = await client.get(answer_file_url)
            if response.status_code != status.HTTP_200_OK:
                response = Response(content="Unable to retrieve the code from cloud", status_code=404)
                return response
            
            python_code = response.text

        tokenized_code = to_words(python_code)

        document = {
            'student_id': student_id,
            'tokenized_code': tokenized_code,
            'submitted': now
        }

        result = collection.insert_one(document)

        if result.inserted_id:
            response = Response(content="Document inserted successfully.", status_code=200)
            return response
        else:
            response = Response(content="Unable to save the code", status_code=500)
            return response

    except Exception as e:
        response = Response(content=str(e), status_code=500)
        return response
    


@answer_api_router.get("/api/calculate_distance")
async def calculate_distance(student_id, year, module_code, question_no):
    try:
        collection_name = f"{year}{module_code}Q{question_no}"
        if collection_name not in db.list_collection_names():
            # When there is no collection matched the submitted question
            response = Response(content="Question not found in the database", status_code=404)
            return response
        
        list_of_code = []  # contains all tokenized_code
        student_id_list = []  # this list aligns with the code list
        
        collection = db[collection_name]
        
        lecturer_answer = collection.find_one({'module_code': {'$exists': True}, 'question_no': {'$exists': True}})
        question = lecturer_answer['question']

        documents = collection.find({'tokenized_code': {'$exists': True}})

        for document in documents:
            tokenized_code = document['tokenized_code']
            student_id_list.append(document['student_id'])  # Collect all student IDs
            if student_id == document['student_id']:
                list_of_code.insert(0, tokenized_code)
            else:
                list_of_code.append(tokenized_code)
                
        if student_id not in student_id_list:
            response = Response(content="Student's submission not found", status_code=404)
            return response

        if len(student_id_list) == 1:
            response = Response(content="No other submission to compare", status_code=404)
            return response

        result, code_index = await calculate_code_distance(list_of_code)

        response_content = [
            {"student_code": list_of_code[0]},
            {"closest_code": list_of_code[code_index]},
            {"question": question},
            {"distance": result}
        ]
        return response_content
    except Exception as e:
        response = Response(content=str(e), status_code=500)
        return response


