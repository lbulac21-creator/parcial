import re, sys

# ---------------- Lexer ----------------
TOKENS = [
    ('FUNC', r'func\b'), ('PRINT', r'print\b'),
    ('NUM', r'\d+'), ('ID', r'[a-zA-Z_]\w*'),
    ('OP', r'[\+\-\*\/\^]'), ('LP', r'\('), ('RP', r'\)'),
    ('COMMA', r','), ('EQ', r'='), ('SEMI', r';'),
    ('SKIP', r'[ \t\r\n]+'), ('MISMATCH', r'.')
]
regex = '|'.join(f'(?P<{n}>{p})' for n,p in TOKENS)

def lexer(code):
    out=[]
    for m in re.finditer(regex, code):
        k,v=m.lastgroup,m.group()
        if k=='NUM': v=int(v)
        if k=='SKIP': continue
        if k=='MISMATCH': raise Exception(f"Error léxico: '{v}'")
        out.append((k,v))
    out.append(('EOF','EOF'))
    return out

# ---------------- Parser ----------------
class Parser:
    def __init__(s,t): s.t,tok=t,0
    def pk(s): return s.t[s.tok][0]
    def pv(s): return s.t[s.tok][1]
    def eat(s,k):
        if s.pk()==k: v=s.pv();s.tok+=1;return v
        raise Exception(f"Error sintáctico en '{s.pv()}'")
    def program(s):
        defs=[]; prints=[]
        while s.pk()=='FUNC': defs.append(s.fdef())
        while s.pk()=='PRINT': prints.append(s.pr())
        if s.pk()!='EOF': raise Exception("Error sintáctico final")
        return defs,prints
    def fdef(s):
        s.eat('FUNC'); name=s.eat('ID'); s.eat('LP')
        ps=[]
        if s.pk()=='ID':
            ps.append(s.eat('ID'))
            while s.pk()=='COMMA': s.eat('COMMA'); ps.append(s.eat('ID'))
        s.eat('RP'); s.eat('EQ')
        e=s.expr(); s.eat('SEMI')
        return (name,ps,e)
    def pr(s):
        s.eat('PRINT'); c=s.call(); s.eat('SEMI'); return c
    def call(s):
        name=s.eat('ID'); s.eat('LP'); args=[]
        if s.pk() in ('NUM','ID','LP'): args.append(s.expr())
        while s.pk()=='COMMA': s.eat('COMMA'); args.append(s.expr())
        s.eat('RP'); return ('call',name,args)
    def expr(s):
        n=s.term()
        while s.pk()=='OP' and s.pv() in '+-':
            op=s.eat('OP'); n=('bin',op,n,s.term())
        return n
    def term(s):
        n=s.power()
        while s.pk()=='OP' and s.pv() in '*/':
            op=s.eat('OP'); n=('bin',op,n,s.power())
        return n
    def power(s):
        n=s.atom()
        if s.pk()=='OP' and s.pv()=='^':
            op=s.eat('OP'); n=('bin',op,n,s.power())
        return n
    def atom(s):
        if s.pk()=='NUM': return ('num',s.eat('NUM'))
        if s.pk()=='ID':
            v=s.eat('ID')
            if s.pk()=='LP': s.tok-=1; return s.call()
            return ('var',v)
        if s.pk()=='LP':
            s.eat('LP'); e=s.expr(); s.eat('RP'); return e
        raise Exception(f"Error sintáctico en '{s.pv()}'")

# ---------------- Interpreter ----------------
class Interpreter:
    def __init__(s,defs,prints): s.funcs={n:(ps,e) for n,ps,e in defs}; s.prints=prints
    def run(s):
        for c in s.prints:
            try: print(s.eval(c,{}))
            except Exception as e: print(e)
    def eval(s,node,env):
        t=node[0]
        if t=='num': return node[1]
        if t=='var':
            if node[1] in env: return env[node[1]]
            raise Exception(f"Error: variable no definida '{node[1]}'")
        if t=='bin':
            l=s.eval(node[2],env); r=s.eval(node[3],env)
            if node[1]=='+': return l+r
            if node[1]=='-': return l-r
            if node[1]=='*': return l*r
            if node[1]=='/':
                if r==0: raise Exception("Error: división por cero")
                return l//r if isinstance(l,int) and isinstance(r,int) else l/r
            if node[1]=='^': return l**r
        if t=='call':
            if node[1] not in s.funcs: raise Exception(f"Error: función no definida '{node[1]}'")
            ps,body=s.funcs[node[1]]
            if len(ps)!=len(node[2]): raise Exception(f"Error: número incorrecto de parámetros en {node[1]} (esperado {len(ps)}, recibido {len(node[2])})")
            args=[s.eval(a,env) for a in node[2]]
            return s.eval(body,dict(zip(ps,args)))
        raise Exception("Error semántico")

# ---------------- Runner ----------------
def run_file(fn="codigo.txt"):
    code=open(fn,encoding="utf-8").read()
    toks=lexer(code); defs,prints=Parser(toks).program()
    Interpreter(defs,prints).run()

if __name__=="__main__":
    run_file(sys.argv[1] if len(sys.argv)>1 else "codigo.txt")