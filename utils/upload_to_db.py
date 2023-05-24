from pymongo import MongoClient
from os import listdir, path
from tqdm import tqdm
from multiprocessing import Pool

# Connect to the MongoDB server
client = MongoClient('mongodb+srv://loctientran235:XUcVn1NKm1N7u6P9@sutd.wuuycxy.mongodb.net/?retryWrites=true&w=majority')
db = client['sutd']
collection_name = '2018MidtermQ7'
collection = db[collection_name]

from tokenize import generate_tokens
import io

def to_words(filename, studentid):
    with open(filename) as f:
        tokenized_code = io.StringIO()
        l = {0: "(EOF)", 4: "(NEWLINE)", 5: "(INDENT)", 6: "(DEDENT)", 59: "(ERROR)"}
        tokenized_code.write("\n".join((l.get(token.type, token.string) if token.type != 3 else token.string.replace("\n", "\\n") for token in generate_tokens(f.readline) if token.type < 60)))
    upload_to_db([tokenized_code.getvalue(), studentid])

def upload_to_db(to_upload):
    try:
        data = {
            'student_id': to_upload[1],
            'tokenized_code': to_upload[0]
        }
        collection.insert_one(data)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    

def translate(args):
    j, s, folder, prefix, suffix = args
    tmp_dir = "".join((folder,j,prefix,s,suffix))
    args_list = []
    dumps = []
    if path.exists(tmp_dir):
        c = 0
        for k in listdir(tmp_dir):
            if k[-3:] == ".py":
                c += 1
                try:
                    args_list.append(to_words(tmp_dir+k, j))
                except:
                    dumps.append(f"Error: Tokenization failed on file {tmp_dir+k}.")
        if c != 1:
            dumps.append(f"Warning: Folder {tmp_dir} has {c} python files.")
    return (args_list, dumps)

if __name__ ==  '__main__':
    folder = "midterm/midterm/midterm/"
    dirc = "midterm/Q"
    lambd = 0.9
    prefix = "/Q"
    suffix = "/submission_1/"
    start = 7
    stop = 8
    pool = Pool()
    
    l = listdir(folder)

    for i in range(start, stop):
        args_list = []
        s = str(i)
        dumps = []
        dirk = dirc+s
        tqdm.write(f"Codedist1.3.2:"+dirk)
        args = [(j, s, folder, prefix, suffix) for j in l]
        for j in tqdm(pool.imap_unordered(translate, args, chunksize=100), desc="Reading files:", total=len(args)):
            args_list.extend(j[0])
            dumps.extend(j[1])