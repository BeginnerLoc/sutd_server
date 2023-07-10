from fastapi import APIRouter, File, UploadFile, HTTPException
from config.database import db
from utils.tokenize import to_words

admin_api_router = APIRouter()


from datetime import datetime, timedelta

@admin_api_router.post("/api/admin/{user_id}/create_question/{module_code}/{question_no}")
async def create_question(
    user_id: str,
    module_code: str,
    question_no: str,
    file: UploadFile = File(...)
):
    if file is not None:
        try:
            contents = await file.read()
            python_code = contents.decode("utf-8")
            answer = to_words(python_code)

            current_year = datetime.now().year
            collection_name = f'{current_year}{module_code}Q{question_no}' # e.g: 2023G123Q4
            
            # Check if collection already exists
            if collection_name not in db.list_collection_names():
                collection = db.create_collection(collection_name)
            else:
                collection = db[f'{collection_name}']
                
            now = datetime.now()

            document = {
                'lecturer_id': user_id,
                'module_code': module_code,
                'question_no': question_no,
                'answer': answer,
                'created': now,
                'deadline': now + timedelta(weeks=1) # default deadline is set to 1 week
            }

            collection.insert_one(document)
            return {"message": "Operation successful"}

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
                    'created': lecturer_answer['created'],
                    'deadline': lecturer_answer['deadline'],
                    'status': status,
                    'no_submisison': collection.count_documents({})
                })
    return response