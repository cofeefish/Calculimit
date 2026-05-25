#  compiles tex to a python ast
#  I believe this part of the program is not relavent to calculus, so this was made with LLM assistance
import re, math
from decimal import Decimal

def error_pointer(tex: str, location: int) -> str:
    pointer_line = ' ' * location + '^'
    return f"\n{tex}\n{pointer_line}"

token_dict = {
    'COMMAND': r'\\[a-zA-Z]+',
    'LBRACE': r'\{|\(',
    'RBRACE': r'\}|\)',
    'WHITESPACE': r'\s+',
    'IDENTIFIER': r'[a-zA-Z][a-zA-Z0-9]*',
    # Support numbers like .1, 1., 1.0, 0.1
    'CONSTANT': r'(\d+\.\d*|\.\d+|\d+)',
    'OPERATOR': r'[+\-*/^=_]',
}

non_terminals = {
    'EXPRESSION': ['TERM', 'EXPRESSION OPERATOR TERM'],
    'TERM': ['FACTOR', 'TERM OPERATOR FACTOR'],
    'FACTOR': ['CONSTANT', 'IDENTIFIER', 'COMMAND LBRACE EXPRESSION RBRACE'],
}

class Token:
    def __init__(self, type: str, value: str, location: int ):
        self.type = type
        self.value = value
        self.location = location

    def __repr__(self, full=True) -> str:
        s = ''
        if full:
            s=f"Token(type={self.type}, value={self.value}, location={self.location})"
        else:
            s=f"{self.type}({self.value})"
        return s

def lexer(tex: str) -> list:
    tokens = []
    index = 0
    #remove extra whitespace
    tex = re.sub(r'\s+', ' ', tex)
    #remove formatting newlines and ampersands
    tex = tex.replace('\n', '').replace('&', '')
    #add implied multiplication between variables and numbers (e.g. 2x -> 2*x)
    tex = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', tex)
    tex = re.sub(r'([a-zA-Z])(\d)', r'\1*\2', tex)

    #tokenize input
    while index < len(tex):
        match = None
        for token_type, pattern in token_dict.items():
            regex = re.compile(pattern)
            match = regex.match(tex, index)
            if match:
                tokens.append(Token(token_type, match.group(), index))
                index = match.end()
                break
        if not match:
            raise SyntaxError(f"Unexpected character: {tex[index]}")
    #error handling for mismatched braces
    brace_stack = []
    for token in tokens:
        if token.type == 'LBRACE':
            brace_stack.append(token)
        elif token.type == 'RBRACE':
            try:
                brace_stack.pop()
            except IndexError:
                 raise SyntaxError(f"Unmatched closing brace at position {token.location}{error_pointer(tex,token.location)}")
    if brace_stack:
        raise SyntaxError(f"Unmatched opening brace at position {brace_stack[-1].location}{error_pointer(tex,brace_stack[-1].location)}")
    return tokens

class ASTNode:
    def __init__(self, type: str, value: str = "", children: list = []):
        self.type = type
        self.value = value
        self.children = children or []

    def vizualize(self):
        '''print full tex tree'''
        #find longest (by str len) level
        #traverse tree
        tree_dict = {}# level: nodes
        padding = 2
        def traverse(node, level=0):
            if level not in tree_dict:
                tree_dict[level] = []
            tree_dict[level].append(node)

            if type(node) == Token:
                return
            for child in node.children:
                traverse(child, level+1)
        traverse(self)
        longest = 0

        for level, node_list in sorted(tree_dict.items()):
            length = sum([len(node.__repr__(False))+padding for node in node_list])
            if length >= longest:
                longest = length

        for level, node_list in sorted(tree_dict.items()):
            length = sum([len(node.__repr__(False))+padding for node in node_list])
            margin = (longest - length)//2
            level_str = ' '*margin+''.join([node.__repr__(False) + ' '*padding for node in node_list])+' '*margin
            print(level, level_str)

    def __repr__(self, full=True) -> str:
        s = ''
        if full:
            s=f"ASTNode(type={self.type}, value={self.value}, children={self.children})"
        else:
            s=f"{self.type}({self.value})"
        return s

def parser(tokens: list):
    # Improved parser: builds AST for all tokens, not just commands
    S = 8  # number of tokens to look ahead
    root = ASTNode("ROOT")
    i = 0
    n = len(tokens)
    while i < n:
        token = tokens[i]
        if token.type == 'COMMAND':
            node = ASTNode("COMMAND", token.value)
            # Look ahead for arguments in braces
            j = i + 1
            while j < n and tokens[j].type == 'WHITESPACE':
                j += 1
            # Only process if next is LBRACE
            while j < n and tokens[j].type == 'LBRACE':
                # Find matching RBRACE
                brace_count = 1
                arg_tokens = []
                k = j + 1
                while k < n and brace_count > 0:
                    if tokens[k].type == 'LBRACE':
                        brace_count += 1
                    elif tokens[k].type == 'RBRACE':
                        brace_count -= 1
                        if brace_count == 0:
                            break
                    if brace_count > 0:
                        arg_tokens.append(tokens[k])
                    k += 1
                if arg_tokens:
                    arg_ast = parser(arg_tokens)
                    node.children.append(arg_ast)
                j = k + 1
                while j < n and tokens[j].type == 'WHITESPACE':
                    j += 1
            root.children.append(node)
            i = j if j > i else i + 1
        elif token.type in ('IDENTIFIER', 'CONSTANT', 'OPERATOR'):
            root.children.append(ASTNode(token.type, token.value))
            i += 1
        elif token.type == 'WHITESPACE':
            i += 1
        else:
            # Ignore braces at this level
            i += 1

    # Remove helper nodes to create an abstract syntax tree
    def clean(node):
        if isinstance(node, ASTNode):
            # Remove nodes with no children
            if node.type == 'ROOT' and len(node.children) == 1:
                return clean(node.children[0])
            # Flatten nodes with only one child (for ARG-like nodes)
            if node.type not in ('COMMAND', 'ROOT') and len(node.children) == 1:
                return clean(node.children[0])
            # Clean children recursively
            cleaned_children = [clean(child) for child in node.children if child is not None]
            return ASTNode(node.type, node.value, cleaned_children)
        else:
            return node
    cleaned = clean(root)
    assert isinstance(cleaned, ASTNode)
    return cleaned

command_translation_dict = { #command value : (arg_count, python_repr, comment, restrictions (ex. V2 in \frac != 0)
    r'\frac'  : (2, r'V1/V2', None, 'V2 != 0'),
    r'\sqrt'  : (1, r'V1', None, 'V1 >= 0'),
    r'\log'   : (1, r'math.log(V1)', "assuming log base e", 'V1 > 0'),
    r'\ln'    : (1, r'math.log(V1)', None, 'V1 > 0'),
    r'\sin'   : (1, r'math.sin(V1)', 'assuming radians', None),
    r'\cos'   : (1, r'math.cos(V1)', 'assuming radians', None),
    r'\tan'   : (1, r'math.tan(V1)', 'assuming radians', None),
    r'\csc'   : (1, r'1/math.sin(V1)', 'assuming radians', None),
    r'\sec'   : (1, r'1/math.cos(V1)', 'assuming radians', None),
    r'\cot'   : (1, r'1/math.tan(V1)', 'assuming radians', None),
    r'\exp'   : (1, r'math.exp(V1)', None, None)
}

def ast_to_python(ast: ASTNode) -> str:
    # Operator precedence for Python
    precedence = {
        '^': 4,
        '*': 3,
        '/': 3,
        '+': 2,
        '-': 2,
        '=': 1
    }

    def to_expr(nodes):
        # Shunting-yard algorithm to handle precedence and associativity
        output = []
        ops = []
        i = 0
        n = len(nodes)
        while i < n:
            node = nodes[i]
            if node.type in ('IDENTIFIER', 'CONSTANT', 'COMMAND', 'ROOT'):
                output.append(ast_to_python(node))
            elif node.type == 'OPERATOR':
                # Handle leading unary minus or plus
                if (i == 0 or nodes[i-1].type == 'OPERATOR') and node.value in ('-', '+'):
                    # Unary operator
                    # Attach to next operand
                    if i+1 < n:
                        operand = ast_to_python(nodes[i+1])
                        output.append(f"({node.value}{operand})")
                        i += 1
                else:
                    while (ops and ops[-1] != '(' and
                           precedence.get(ops[-1], 0) >= precedence.get(node.value, 0)):
                        op = ops.pop()
                        right = output.pop()
                        left = output.pop()
                        output.append(f"({left}{op}{right})")
                    ops.append(node.value)
            elif node.type == 'LBRACE':
                ops.append('(')
            elif node.type == 'RBRACE':
                while ops and ops[-1] != '(': 
                    op = ops.pop()
                    right = output.pop()
                    left = output.pop()
                    output.append(f"({left}{op}{right})")
                ops.pop()  # Remove '('
            i += 1
        while ops:
            op = ops.pop()
            right = output.pop()
            left = output.pop()
            output.append(f"({left}{op}{right})")
        return output[0] if output else ''

    if ast.type == 'COMMAND':
        if ast.value not in command_translation_dict.keys():
            raise NotImplementedError(f"Command {ast.value} not implemented")

        arg_count, python_repr, comment, restrictions = command_translation_dict[ast.value]
        if len(ast.children) != arg_count:
            raise SyntaxError(f"{ast.value} requires exactly {arg_count} arguments, got {len(ast.children)}")
        if comment != None: print(comment)
        #replace vars (Vx) in python_repr with ast.children
        for i in range(arg_count):
            python_repr = python_repr.replace(f'V{i+1}', f"({ast_to_python(ast.children[i])})")
        #check restrictions
        if restrictions != None:
            #replace Vx in restrictions with ast.children
            for i in range(arg_count):
                restrictions = restrictions.replace(f'V{i+1}', f"({ast_to_python(ast.children[i])})")
            #evaluate restrictions
            if not eval(restrictions):
                raise ValueError(f"Restrictions not met for {ast.value}: {restrictions}")
        return python_repr
        
    elif ast.type == 'ROOT':
        return to_expr(ast.children)
    elif ast.type == 'IDENTIFIER':
        replacment = f'var_{ast.value}'
        return replacment
    elif ast.type == 'CONSTANT':
        # Handle leading dot (e.g. .1)
        if ast.value.startswith('.'):
            return '0' + ast.value
        return ast.value
    else:
        raise NotImplementedError(f"AST node type {ast.type} not implemented")

#test
if __name__ == "__main__":
    tex = r"""\log(\frac{x}{0})"""
    tokens = lexer(tex)
    ast = parser(tokens)
    ast.vizualize()
    py_code = ast_to_python(ast)
    print("Python code:", py_code)