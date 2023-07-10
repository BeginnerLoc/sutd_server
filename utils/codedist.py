from multiprocessing import Pool
from tqdm import tqdm

def closest(values):
    value = min(i for i in values if float(i) > 0)
    code_index = values.index(value)
    return value, code_index

#codedist1.3.2
def read(code):
    l = code.split("\n")
    return l

def minDist(len1, len2, c):
    #For two lists of lengths len1 and len2, the minimum distance between them (achieved when all list items are identical)
    #is not zero, but a small constant, due to how the metric is defined.
    #This functions finds that constant minimum value so that we can scale the distance to be between 0 and 1.
    return (c * (1 - c**min(len1, len2)) / (1 - c) + max(len1 - len2, 0) * c**len2) / len1

def codeDistW(args):
    c, l1, l2, l1Wt, l2Wt, row, iNum = args
    """w should be a dictionary of weights. The default weight is 1."""
    dist = [row.copy() for i in range(len(l1)+1)] #Have an extra row and columns filled with ones for convenience (out of bounds values)
    rowSelfDist = [[(1) for j in range(len(l1)+1)].copy() for i in range(len(l1)+1)]
    colSelfDist = [row.copy() for i in range(len(l2)+1)]
    rowVal = [1e100 for i in range(len(l1))]
    colVal = [1e100 for j in range(len(l2))]
    rowSelfVal = [1e100 for i in range(len(l1))]
    colSelfVal = [1e100 for j in range(len(l2))]    
    
    for i in range(len(l1)-1,-1,-1):
        for j in range(len(l2)-1,-1,-1):
            wt = l1Wt[i] * l2Wt[j]
            dist[i][j] = dist[i+1][j+1] * c**wt + (l1[i] != l2[j]) * (1 - c**wt)
            rowVal[i] = min(rowVal[i], dist[i][j])
            colVal[j] = min(colVal[j], dist[i][j])

    for i in range(len(l1)-1,-1,-1):
        for j in range(len(l1)-1,-1,-1):
            wt = l1Wt[i] * l1Wt[j]
            rowSelfDist[i][j] = rowSelfDist[i+1][j+1] * c**wt + (l1[i] != l1[j]) * (1 - c**wt)
            rowSelfVal[i] = min(rowSelfVal[i], rowSelfDist[i][j])
    
    for i in range(len(l2)-1,-1,-1):
        for j in range(len(l2)-1,-1,-1):
            wt = l2Wt[i] * l2Wt[j]
            colSelfDist[i][j] = colSelfDist[i+1][j+1] * c**wt + (l2[i] != l2[j]) * (1 - c**wt)
            colSelfVal[i] = min(colSelfVal[i], colSelfDist[i][j])
    
    for i in range(len(rowVal)):
        rowVal[i] *= l1Wt[i]
        rowSelfVal[i] *= l1Wt[i]
    rowAvg = sum(rowVal) / sum(l1Wt)
    md1 = sum(rowSelfVal) / sum(l1Wt)
    
    for i in range(len(colVal)):
        colVal[i] *= l2Wt[i]
        colSelfVal[i] *= l2Wt[i]
    colAvg = sum(colVal) / sum(l2Wt)
    md2 = sum(colSelfVal) / sum(l2Wt)
    
    #print(rowAvg,colAvg)
    
    # Scale between minDist and 1
    rowAvg = (rowAvg - md1) * (1 / (1 - md1))
    colAvg = (colAvg - md2) * (1 / (1 - md2))
    #print(rowVal,colVal)
    #print(rowAvg,colAvg)
    #print(allSameRowVal)
    #print(md1,md2)
    #print(rowAvg,colAvg)
    return (iNum, max(rowAvg,colAvg))

def calculate(ipt, discount):
    pool = Pool()

    f = open("utils/config.txt", "r")
    keywords = {}
    for line in f:
        l = line.strip().split(": ")
        keywords[l[0]] = float(l[1])  # assign weights to words

    numtexts = len(ipt)  # number of txt files to compare

    ret = []
    lWt = []
    rows = []
    output_values = []

    ref_code = read(ipt[0])  # Use the first code snippet as the reference code
    ret.append(ref_code)
    rows.append([(1) for j in range(len(ref_code) + 1)])
    lWt.append([keywords[ref_code[j]] if ref_code[j] in keywords else 1 for j in range(len(ref_code))])

    # Modification: Iterate from index 1 to exclude the reference code
    for i in range(1, numtexts):
        ret.append(read(ipt[i]))
        rows.append([(1) for j in range(len(ret[i]) + 1)])
        lWt.append([keywords[ret[i][j]] if ret[i][j] in keywords else 1 for j in range(len(ret[i]))])

    # Modification: Exclude the reference code from the arguments
    args = [(discount, ret[0], ret[j], lWt[0], lWt[j], rows[j], j) for j in range(1, numtexts)]
    ret = [0] * (numtexts + 1)  # Modify the list size to accommodate the distances

    for i in tqdm(pool.imap_unordered(codeDistW, args, chunksize=10), desc="Calculating distances", total=len(args)):
        ret[i[0] + 1] = i[1]

    output_values.append("0.000")  # Distance for the reference code
    for i in range(1, numtexts):
        output_values.append(f"{ret[i + 1]:.3f}")  # Distances for the rest of the codes

    return output_values


#main
# from pymongo import MongoClient

# if __name__ == '__main__':
#     lambd = 0.9
#     pool = Pool()
    
#     student_id = '2018001'
#     question = '2018MidtermQ3'
    
#     code = [] # contains all tokenized_code
#     student_id_list = [] # this list aligns with the code list

#     client = MongoClient('mongodb+srv://loctientran235:XUcVn1NKm1N7u6P9@sutd.wuuycxy.mongodb.net/?retryWrites=true&w=majority')
#     db = client['sutd']
#     collection = db[question]

#     documents = collection.find({'tokenized_code': {'$exists': True}})
#     for document in documents:
#         tokenized_code = document['tokenized_code']
#         if student_id == document['student_id']:
#             code.insert(0, tokenized_code)
#             student_id_list.insert(0, document['student_id'])
#             # tokenized_code with the matched student_id is always placed at index 0
#         else:
#             code.append(tokenized_code)
#             student_id_list.append(document['student_id'])

    
#     calculated_values = calculate(code, lambd)
#     value, code_index = closest(calculated_values)
    
#     print(calculated_values)
#     print(f"Closest file to Student's answer is {student_id_list[code_index]} with a distance of {value}.")


#list of code is inclusive of the student code to be compared
def calculate_code_distance(list_of_code, lambd = 0.9):
    calculated_values = calculate(list_of_code, lambd)
    value, code_index = closest(calculated_values)
    return value