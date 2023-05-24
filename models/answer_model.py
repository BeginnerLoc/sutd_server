from pydantic import BaseModel

class Answer(BaseModel):
    question_no: str
    student_id: str
    python_code: str