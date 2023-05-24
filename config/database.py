from pymongo import MongoClient

client = MongoClient('mongodb+srv://loctientran235:XUcVn1NKm1N7u6P9@sutd.wuuycxy.mongodb.net/?retryWrites=true&w=majority')
db = client['sutd']