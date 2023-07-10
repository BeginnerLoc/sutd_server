from os import listdir, path, makedirs
from multiprocessing import Pool
from tqdm import tqdm
import tokenize
from io import StringIO
import time

def closest(values):
    value = min(i for i in values if float(i) > 0)
    file_index = values.index(value)
    return value, file_index

def remove_comments_and_docstrings(source):
    """
    Returns 'source' minus comments and docstrings.
    """
    io_obj = StringIO(source)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type = tok[0]
        token_string = tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]
        ltext = tok[4]
        # The following two conditionals preserve indentation.
        # This is necessary because we're not using tokenize.untokenize()
        # (because it spits out code with copious amounts of oddly-placed
        # whitespace).
        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            out += (" " * (start_col - last_col))
        # Remove comments:
        if token_type == tokenize.COMMENT:
            pass
        # This series of conditionals removes docstrings:
        elif token_type == tokenize.STRING:
            if prev_toktype != tokenize.INDENT:
        # This is likely a docstring; double-check we're not inside an operator:
                if prev_toktype != tokenize.NEWLINE:
                    # Note regarding NEWLINE vs NL: The tokenize module
                    # differentiates between newlines that start a new statement
                    # and newlines inside of operators such as parens, brackes,
                    # and curly braces.  Newlines inside of operators are
                    # NEWLINE and newlines that start new code are NL.
                    # Catch whole-module docstrings:
                    if start_col > 0:
                        # Unlabelled indentation means we're inside an operator
                        out += token_string
                    # Note regarding the INDENT token: The tokenize module does
                    # not label indentation inside of an operator (parens,
                    # brackets, and curly braces) as actual indentation.
                    # For example:
                    # def foo():
                    #     "The spaces before this docstring are tokenize.INDENT"
                    #     test = [
                    #         "The spaces before this string do not get a token"
                    #     ]
        else:
            out += token_string
        prev_toktype = token_type
        last_col = end_col
        last_lineno = end_line
    return out


#codedist1.3.2
def read(filename):
    '''Reads a tokenised python file and returns a list of the tokens'''
    f = open(filename, "r")
    s = f.read()
    f.close()
    s = remove_comments_and_docstrings(s)
    
    s = s.replace("    ","\t")
    s = s.replace("\t","(INDENT)")
    # s = s.replace("\n\n\n","\n(NEWLINE)\n")
    while s.find("\n\n") != -1:
        s = s.replace("\n\n","\n")
    # print(s)
    # print("--------- next --------")
    l = s.split("\n")
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
    f = open("config.txt","r")
    keywords = {}
    for line in f:
        l = line.strip().split(": ")
        keywords[l[0]] = float(l[1]) #assign weights to words

    numtexts = len(ipt) #number of txt files to compare

    ret = []
    lWt = []
    rows = []
    output_values = []
    for i in range(numtexts):
        ret.append(read(ipt[i]))
        rows.append([(1) for j in range(len(ret[i])+1)])
        lWt.append([keywords[ret[i][j]] if ret[i][j] in keywords else 1 for j in range(len(ret[i]))])
    args = [(discount,ret[numtexts-1],ret[j],lWt[numtexts-1],lWt[j],rows[j],j)for j in range(numtexts)]
    ret = [[0]*numtexts for i in range(numtexts)]
    for i in tqdm(pool.imap_unordered(codeDistW, args, chunksize=10), desc="Calculating distances", total=len(args)):
        ret[i[0]] = i[1] 
        # print(i)
    dirlen = len(folder)
    fnames = [i[dirlen:] for i in ipt]
    # outfilelist = [f'{folder},{",".join(fnames)}']
    for i in range(numtexts-1):
        # out_tmp = [fnames[i]]
        output_values.append(f"{ret[i]:.3f}")
    output_values.append(0.00)
    # print(lWt)
    # print(ret)
    # print(output_values)
    return (fnames, output_values)


#python_in_words
from tokenize import generate_tokens, open as topen

def to_words(filename):
    with topen(filename) as f:
        filename = filename[:-3]+"_out.txt"
        with open(filename, "w") as of:
            l = {0: "(EOF)", 4: "(NEWLINE)", 5: "(INDENT)", 6: "(DEDENT)", 59: "(ERROR)"}
            of.write("\n".join((l.get(token.type, token.string) if token.type != 3 else token.string.replace("\n", "\\n") for token in generate_tokens(f.readline) if token.type < 60)))
    return filename

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
                    args_list.append(to_words(tmp_dir+k))
                except:
                    dumps.append(f"Error: Tokenization failed on file {tmp_dir+k}.")
        if c != 1:
            dumps.append(f"Warning: Folder {tmp_dir} has {c} python files.")
    return (args_list, dumps)

def explain(file_name):
    file_name = "counting/counting/"+file_name.rstrip("_out.txt")+".py"
    file1 = open(file_name)
    answer = file1.read()
    prompt = "#Python3\n"+answer+"\n#How can a similar code can be written in 3 hints of increasing detail. For the first 2 hints, only answer in natural language. Hint 3 should be the entire code and the explanation on how it works."
    print(prompt)
#main
if __name__ ==  '__main__':
    folder = "counting/counting/"
    dirc = "counting/updated"
    lambd = 0.9
    prefix = "/Q"
    suffix = "/submission_1/"
    start = 3
    stop = 4
    pool = Pool() #To allow running multiple jobs per process
    try:
        l = listdir(folder)
    except:
        folder = "./"+folder
        makedirs(folder)
        l = listdir(folder)

    for i in range(start, stop):
        args_list = []
        s = str(i)
        dumps = []
        dirk = dirc+s
        args = [(j, s, folder, prefix, suffix) for j in l]
        args.append(("student_ans",s,folder,prefix,suffix)) #Remove hardcode

        tqdm.write(f"Codedist1.3.2:"+dirk)
        for j in tqdm(pool.imap_unordered(translate, args, chunksize=100), desc="Reading files", total=len(args)):
            args_list.extend(j[0])
            dumps.extend(j[1])
        if not path.exists(dirk):
            makedirs(dirk)
        outfile = open(f"{dirk}/log.txt", "w")
        outfile.write("\n".join(dumps))
        outfile.close()
        file_name, calculated_values = calculate(args_list, lambd)
        value, file_index = closest(calculated_values)
        print(f"Closest file to Student's answer is {file_name[file_index]} with a distance of {value}.")
        explanation = explain(file_name[file_index])


