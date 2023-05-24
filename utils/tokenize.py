
#tokenize string
import io
from tokenize import generate_tokens, TokenInfo

def to_words(python_code):
    tokenized_code = io.StringIO()
    l = {0: "(EOF)", 4: "(NEWLINE)", 5: "(INDENT)", 6: "(DEDENT)", 59: "(ERROR)"}
    code_lines = python_code.splitlines()
    for line in code_lines:
        tokens = generate_tokens(io.StringIO(line).readline)
        line_tokens = [l.get(token.type, token.string) if token.type != 3 else token.string.replace("\n", "\\n") for token in tokens if token.type < 60]
        tokenized_code.write("\n".join(line_tokens) + "\n")
    return tokenized_code.getvalue()  