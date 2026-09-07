import re
class Q(str): pass   # quoted string token
def parse(s):
    tok=re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()]+',s)
    stack=[[]]
    for t in tok:
        if t=='(': stack.append([])
        elif t==')':
            l=stack.pop(); stack[-1].append(l)
        else:
            stack[-1].append(Q(t[1:-1].replace('\\"','"')) if t.startswith('"') else t)
    return stack[0]
def q(s): return '"'+str(s).replace('\\','\\\\').replace('"','\\"')+'"'
def dump(e,ind=0):
    if isinstance(e,list):
        if all(not isinstance(x,list) for x in e): return '('+' '.join(dump(x) for x in e)+')'
        return '('+' '.join(dump(x) if not isinstance(x,list) else '\n'+'  '*(ind+1)+dump(x,ind+1) for x in e)+')'
    return q(e) if isinstance(e,Q) else e
def libsym(path,name):
    doc=parse(open(path).read())
    for e in doc[0]:
        if isinstance(e,list) and e[0]=='symbol' and e[1]==name: return e
    raise KeyError(name)
def pins(sym):
    out=[]
    for e in sym:
        if isinstance(e,list) and e[0]=='symbol':
            for p in e:
                if isinstance(p,list) and p[0]=='pin':
                    at=[x for x in p if isinstance(x,list) and x[0]=='at'][0]
                    nm=[x for x in p if isinstance(x,list) and x[0]=='name'][0][1]
                    num=[x for x in p if isinstance(x,list) and x[0]=='number'][0][1]
                    ln=[x for x in p if isinstance(x,list) and x[0]=='length'][0][1]
                    out.append((e[1].split('_')[-2],num,nm,p[1],float(at[1]),float(at[2]),float(at[3]),float(ln)))
    return out
