from pydantic import BaseModel

class Answer(BaseModel):
    question_no: str
    student_id: str
    module_code: str
    python_code: str