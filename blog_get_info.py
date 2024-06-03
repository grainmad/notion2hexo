#! /usr/bin/python3
import os
import json
import re
from urllib.parse import unquote


"""
叶子节点可能含同名目录（资源文件夹），无同名目录一定是叶子
非叶子节点一定有同名目录，目录内一定有md
所以非叶子的md内有链接到同名目录内的md
"""
def check_leaf(path, hname):
    if not os.path.isdir(path[:-3]) : return True
    with open(path, "r", encoding="utf8") as f:
        text = f.read()
    pattern = r'\[(.*?)\]\((.*?)/(.*?)\.md\)'
    rt = re.search(pattern, text)
    if rt and unquote(rt.group(2)) == hname: # 检测到md链接，且md链接是在同名目录内，则不是叶子
        return False
    return True

def list_files(path, ancestor, ancestorhash):
    node = path.split("/")[-1]
    name, hash, type, leafmd = None, None, None, False

    if os.path.isdir(path):
        name = ' '.join(node.split(" ")[:-1])
        hash = node.split(" ")[-1]
        type = "dir"
    elif ".md" == node[-3:]:
        name = ' '.join(node[:-3].split(" ")[:-1])
        hash = node[:-3].split(" ")[-1]
        type = "markdown"
        leafmd = check_leaf(path, node[:-3])
    else :
        name = '.'.join(node.split(".")[:-1])
        type = node.split(".")[-1]
    rt = {
            "type": type,
            "leafmd": leafmd,
            "dirid": None,
            "name": name,
            "hash": hash,
            "ancestor":ancestor.copy(),
            "ancestorhash":ancestorhash.copy(),
            "fileson":[],
            "dirson":[]
        }
    ancestor.append(name)
    ancestorhash.append(hash)
    if os.path.isdir(path):
        dir = os.listdir(path)
        for i in dir:
            cur = path+"/"+i
            if os.path.isdir(cur):
                rt["dirson"].append(list_files(cur, ancestor, ancestorhash))
                ancestor.pop()
                ancestorhash.pop()
        for i in dir:
            cur = path+"/"+i
            if os.path.isfile(cur):
                rt["fileson"].append(list_files(cur, ancestor, ancestorhash))
                ancestor.pop()
                ancestorhash.pop()
        ds = rt["dirson"]
        for item in rt["fileson"]:
            if item["type"] == "markdown":
                pos = 0
                while pos < len(ds):
                    if ds[pos]["name"] == item["name"] and ds[pos]["hash"] == item["hash"]:
                        break
                    pos+=1
                if pos != len(ds):
                    item["dirid"] = pos
    return rt


if __name__ == '__main__':
    data = list_files("uploads/notion fe88dc165457", [], [])
    print(json.dumps(data))