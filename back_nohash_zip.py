import re
import os
import shutil

def cut_suffix(s):
    return ' '.join(s.split(" ")[:-1])

def cp(src, dst):
    dir = os.listdir(src)
    for i in dir:
        cur = src+"/"+i
        if os.path.isdir(cur):
            # print(cur, "isdir")
            cp(cur, dst+"/"+cut_suffix(i))
        if os.path.isfile(cur):
            file = dst+"/"+cut_suffix(i)+".md" if '.' in cur and cur.rsplit('.', 1)[1] == "md" else dst+"/"+i 
            # print(cur, file)
            os.makedirs(os.path.dirname(file), exist_ok=True)
            shutil.copy(cur, file)
            

def copyfile(src, dst):
    cp(src, dst)

"""
修改文件内容
链接的哈希
链接中的非法字符 # 转为 %23
"""

def illegal_char_filter(s):
    pattern = r'\[(.*?)\]\((.*?)\)'
    return re.sub(pattern, lambda match: '[' + match.group(1) + '](' + match.group(2).replace('#', '%23') + ')', s)

def get_suffix(s):
    return s.split(" ")[-1]

def get_hash(src):
    rec_h = set()
    def rc(src):
        rec_h.add("%20"+get_suffix(src))
        dir = os.listdir(src)
        for i in dir:
            cur = src+"/"+i
            if os.path.isdir(cur):
                # print(cur, "isdir")
                rc(cur)
            if os.path.isfile(cur):
                if cur.rsplit('.', 1)[1] == "md":
                    rec_h.add("%20"+get_suffix(cur[:-3]))
    rc(src)
    return rec_h



def remove_hash(rec_h, src):
    def dfs(src):
        dir = os.listdir(src)
        for i in dir:
            cur = src+"/"+i
            if os.path.isdir(cur):
                # print(cur, "isdir")
                dfs(cur)
            if os.path.isfile(cur):
                if cur.rsplit('.', 1)[1] == "md":
                    with open(cur, "r") as f:
                        text = f.read()
                    pos, sz = 35, len(text)
                    mtext = ""
                    while pos < sz:
                        if text[pos-35:pos] in rec_h:
                            pos+=35
                        else :
                            mtext += text[pos-35]
                            pos+=1
                    if pos-35<sz : mtext += text[pos-35:]
                    mtext = illegal_char_filter(mtext)
                    with open(cur, "w", encoding="utf8") as f:
                        f.write(mtext)
    dfs(src)


if __name__ == '__main__':
    copyfile("uploads/unz/", "uploads/umz")
    rec_h = get_hash("uploads/unz")
    remove_hash(rec_h, "uploads/umz")
