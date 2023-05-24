def answer_serializer(answer) -> dict:
    return {
        "_id": str(answer["_id"]),
        "student_id": answer["student_id"],
        "tokenized_code": answer["tokenized_code"]
    }
    
def answers_serializer(answers) -> list:
    return [answer_serializer(answer) for answer in answers] 