import re

p = re.compile("(\S+)")
A = ord('A')
Z = ord('Z')

def tokenize(s):
    t = re.sub("\(\(([^\)]*)\)\)", r"  \1  ", s)
    t = re.sub("\b--\b","  ",t)
    t = t.replace("{cough}", "       ")
    t = t.replace("{laugh}", "       ")
    t = t.replace("{lipsmack}", "          ")
    t = t.replace("{sneeze}", "        ")
    t = t.replace("[[NS]]", "      ")

    i = 0
    m = p.search(t)
    L = []
    while m:
        i,j = h,k = m.span()
        tag = desc = ""
        c = t[i]
        if c == "~":
            n = ord(t[i+1])
            if n < A or n > Z or j != i+2:
                tag = "err"
                desc = "invalid individual letter"
            else:
                tag = "nospell"
                h = i+1
        elif c == "+":
            h = i+1
        elif c in '*-':
            tag = "nospell"
            h = i+1

        if h == k and tag!="err":
            tag = "err"
            desc = "isolated markup"

        c = t[j-1]
        if c in '?.,':
            k = j-1
        elif c == '-':
            k -= 1
            tag = "nospell"

        if h >= k and tag!="err":
            tag = "err"
            desc = "isolated markup"
                
        L.append([i,j,h,k,tag,desc])
            
        m = p.search(t,j)

    return L


if __name__ == "__main__":
    tokenize("abd +def *adf asdf -a ~s . ad ~A")
    
        
