from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form
from config.database import db
from utils.tokenize import to_words
from models.answer_model import Answer
from datetime import datetime


admin_api_router = APIRouter()

@admin_api_router.post("/api/admin/{user_id}/create_question/{year}/{module_code}/{question_no}")
async def create_question(
    user_id: str,
    year: int,
    module_code: str,
    question_no: str,
    question: str = Form(...),
    deadline_date: str = Form(...),
    file: UploadFile = File(...)
):
    if file is not None:
        try:
            contents = await file.read()
            python_code = contents.decode("utf-8")
            answer = to_words(python_code)

            collection_name = f'{year}{module_code}Q{question_no}'  # e.g: 2023G123Q4
            
            # Check if collection already exists
            if collection_name not in db.list_collection_names():
                collection = db.create_collection(collection_name)
            else:
                collection = db[f'{collection_name}']
                
            now = datetime.now()
            deadline = datetime.strptime(deadline_date, "%Y-%m-%d")

            document = {
                'lecturer_id': user_id,
                'module_code': module_code,
                'question_no': question_no,
                'question': question,
                'answer': answer,
                'created': now,
                'deadline': deadline
            }

            collection.insert_one(document)
            return {"message": "Operation successful"}

        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))

@admin_api_router.post("/api/admin/{user_id}/edit_question/{year}/{module_code}/{question_no}")
async def edit_question(
    user_id: str,
    year: int,
    module_code: str,
    question_no: str,
    question: str = Form(None),  # Allow question to be optional
    deadline_date: str = Form(None),  # Allow deadline_date to be optional
    file: UploadFile = File(None)  # Set a default value for file
):
    try:
        collection_name = f'{year}{module_code}Q{question_no}'
        collection = db[collection_name]

        # Find the existing document
        existing_document = collection.find_one({'lecturer_id': user_id, 'module_code': module_code, 'question_no': question_no})

        if not existing_document:
            raise HTTPException(status_code=404, detail="Question not found")

        # Read the uploaded file if provided
        if file is not None:
            contents = await file.read()
            python_code = contents.decode("utf-8")
            answer = to_words(python_code)
            collection.update_one({'_id': existing_document['_id']}, {'$set': {'answer': answer}})

        # Update the question if provided
        if question:
            collection.update_one({'_id': existing_document['_id']}, {'$set': {'question': question}})

        # Update the deadline if provided
        if deadline_date:
            new_deadline = datetime.strptime(deadline_date, "%Y-%m-%d")
            collection.update_one({'_id': existing_document['_id']}, {'$set': {'deadline': new_deadline}})

        return {"message": "Question information updated successfully"}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@admin_api_router.delete("/api/admin/{user_id}/delete_question/{year}/{module_code}/{question_no}")
async def delete_question(
    user_id: str,
    year: int,
    module_code: str,
    question_no: str
):
    try:
        collection_name = f'{year}{module_code}Q{question_no}'
        collection = db[collection_name]

        # Find the existing document
        existing_document = collection.find_one({'lecturer_id': user_id, 'module_code': module_code, 'question_no': question_no})

        if not existing_document:
            raise HTTPException(status_code=404, detail="Question not found")

        # Delete the collection
        db.drop_collection(collection_name)

        return {"message": f"Question and collection {collection_name} deleted successfully"}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
@admin_api_router.get("/api/admin/get_all_questions")
async def get_all_questions():
    
    response = []
    
    collection_names = db.list_collection_names()
    # Iterate over the collections
    for collection_name in collection_names:
        # Check if the collection represents a question
        if collection_name.startswith('2023g'):
            # Retrieve the lecturer's answer from the collection
            collection = db[collection_name]
            lecturer_answer = collection.find_one({'module_code': {'$exists': True}, 'question_no': {'$exists': True}})
            print(collection.count_documents({}))
        
            # Process the lecturer's answer
            if lecturer_answer:
                status = ['past']
                if datetime.now() < lecturer_answer['deadline']:
                    status = ['current']
                response.append({
                    'module_code': lecturer_answer['module_code'],
                    'question_no': lecturer_answer['question_no'],
                    'question': lecturer_answer['question'],
                    'created': lecturer_answer['created'],
                    'deadline': lecturer_answer['deadline'],
                    'status': status,
                    'no_submisison': collection.count_documents({})
                })
    return response


# To modify student's submission
# submit student's code as string -> to be tokenized and stored in the database
@admin_api_router.post("/api/submit_answer/{year}/{module_code}")
async def submit_answer(year: int, module_code: str, answer: Answer):
    try:
        question_no = answer.question_no
        python_code = answer.python_code
        student_id = answer.student_id
        collection = db[f"{year}{module_code}Q{question_no}"]

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
    except Exception as e:
        return {"status": "error", "message": str(e)}

# delete student's answer
@admin_api_router.delete("/api/delete_answer/{year}/{module_code}")
async def delete_answer(year: int, module_code: str, question_no: str = Query(None), student_id: str = Query(None)):
    try:
        result = None

        if student_id and question_no:
            collection = db[f"{year}{module_code}Q{question_no}"]
            result = collection.delete_one({'student_id': student_id})
            if result.deleted_count == 1:
                result = f"Document with studentid {student_id} deleted successfully."
            else:
                result = f"No document found with studentid {student_id}."
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
