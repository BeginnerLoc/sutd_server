import io
from tokenize import generate_tokens
from token import tok_name

def to_words(code_string):
    tokenized_code = io.StringIO()
    l = {0: "(EOF)", 4: "(NEWLINE)", 5: "(INDENT)", 6: "(DEDENT)", 59: "(ERROR)"}
    tokenized_code.write("\n".join((l.get(token.type, token.string) if token.type != 3 else token.string.replace("\n", "\\n") for token in generate_tokens(io.StringIO(code_string).readline) if token.type < 60)))
    return tokenized_code.getvalue()



