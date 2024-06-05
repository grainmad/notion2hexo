import os
import shutil
import blog_get_info
import datetime
import re
from urllib.parse import unquote
from dotenv import load_dotenv
import markdown
import zipUtil
from back_nohash_zip import copyfile, remove_hash, get_hash



load_dotenv()
HEXO_BLOG = os.getenv("HEXO_BLOG")

def gen_dscr(data, fdata):
    md = ""
    def dfs(data, fdata, space):
        nonlocal md
        md += f"{space}* {data['name']}\n"
        if not data["leafmd"]:
            fs = fdata["dirson"][data["dirid"]]
            # print(data['name'], fs['fileson'])
            for item in fs["fileson"]:
                if item["type"] == "markdown":
                    dfs(item, fs, space+"    ")
            

    dfs(data, fdata, "")
    html = markdown.markdown(md).replace("\n", "")
    html = f"\"{html[:3]} style='text-align: left;'{html[3:]}\""
    return html

def hexo_blog_cmp(newblog, postblog, data, fdata):
    curtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    blog_head = {
        "title": data["name"],  # string
        "date": curtime,  # time
        "updated": curtime,  # time
        "tag": data['ancestor'] if data['leafmd'] else ["index page"],  # list
        "categories": data["ancestor"][1] if len(data["ancestor"])>1 else data["name"],  # string
        "mathjax": True,  # true or false
        "comments": True,  # true or false
        # "description": '' if data['leafmd'] else gen_dscr(data, fdata),
        "description": gen_dscr(data, fdata)  
    }
    # print(blog_head)
    # print(postblog)
    
    # 生成新文章内容
    with open(newblog, 'r', encoding="utf8") as f:
        new_blog_file = f.readlines()
        
    # <!--more--> 在代码块中不生效 落在代码块内则延续到代码块结束
    # if data['leafmd'] and len(new_blog_file)>=20 : 
    #     def add_more(s):
    #         return f"{s[:-1]}<!--more-->\n"
    #     code_sign = 0
    #     for i in range(20):
    #         if "```" in new_blog_file[i]: code_sign+=1
    #     if code_sign % 2 == 1: # 落在第(code_sign+1)//2个代码块内
    #         for i in range(20, len(new_blog_file)):
    #             if "```" in new_blog_file[i]: 
    #                 new_blog_file[i] = add_more(new_blog_file[i])
    #                 break
    #     else:
    #         new_blog_file[19] = add_more(new_blog_file[19])
    
    # 旧文章存在，生成时间延续旧文章的，更新时间取决于内容是否一致
    if os.path.isfile(postblog): # 存在，获取创建时间
        with open(postblog, 'r', encoding="utf8") as f:
            old_blog_file = f.readlines()
            if len(old_blog_file) >= 2 and old_blog_file[2][:5] == "date:":
                blog_head['date'] = old_blog_file[2][6:-1]
            
            # 尝试找到文章头部结束位置
            head_pos = 1
            while old_blog_file[head_pos] != "---\n": head_pos+=1
            
            if old_blog_file[head_pos+1:] == new_blog_file: # 内容一致则不更新
                blog_head['updated'] = old_blog_file[3][9:-1]

    new_blog_head = [
        "---\n",
        # 注意title内不能有"
        f"title: \"{blog_head['title']}\"\n",
        f"date: {blog_head['date']}\n",
        f"updated: {blog_head['updated']}\n",
        f"tag: [{ ', '.join(blog_head['tag']) }]\n",
        f"categories: {blog_head['categories']}\n",
        f"mathjax: {'true' if blog_head['mathjax'] else 'false'}\n",
        f"comments: {'true' if blog_head['comments'] else 'false'}\n",
        # 注意description内不能有'
        f"description: {blog_head['description']}\n",
        "---\n",
    ]
    new_blog_file = new_blog_head + new_blog_file
    
    with open(newblog, 'w', encoding="utf8") as f:
        f.writelines(new_blog_file)



def replace_link(text):
    pattern = r'\[(.*?)\]\((.*?)\.md\)'
    pattern2 = r'!\[(.*?)\]\((.*?)/(.*?)\)'
    text = re.sub(pattern, lambda match: f"[{match.group(1)}]({match.group(2)[-12:]}/)", text)
    text = re.sub(pattern2, lambda match: f'{{% asset_img \'{unquote(match.group(3))}\' %}}', text)
    return text

def cr(src, dst, data):
    src += f"/{data['name']} {data['hash']}"
    dst += f"/{data['hash'][-12:]}"
    for item in data["dirson"]:
        cr(src, dst, item)
    for item in data["fileson"]:
        if item["type"] == "markdown":
            srcfile = f"{src}/{item['name']} {item['hash']}.md"
            dstfile = f"{dst}/{item['hash'][-12:]}.md"
            os.makedirs(os.path.dirname(dstfile), exist_ok=True)
            shutil.copy(srcfile, dstfile)
            with open(dstfile, "r", encoding="utf8") as f:
                text = f.read()
            text = replace_link(text)
            with open(dstfile, "w", encoding="utf8") as f:
                f.write(text)
            
            hexo_blog_cmp(dstfile, f"{HEXO_BLOG}/source/_posts/{'/'.join(i[-12:] for i in item['ancestorhash'])}/{item['hash'][-12:]}.md", item, data)
        else:
            srcfile = f"{src}/{item['name']}.{item['type']}"
            dstfile = f"{dst}/{item['name']}.{item['type']}"
            os.makedirs(os.path.dirname(dstfile), exist_ok=True)
            shutil.copy(srcfile, dstfile)


def process(workdir, filename):
    os.chdir(workdir) #修改当前工作目录
    print("cwd", os.getcwd()) #获取当前工作目录
    
    dirhash, unzipdir = None, filename.replace(".zip", "")

    # 解压
    zipUtil.unzip(filename)

    # # 备份无哈希结构的压缩包
    copyfile(unzipdir, unzipdir+"_bk")
    rec_h = get_hash(unzipdir)
    remove_hash(rec_h, unzipdir+"_bk")
    zipUtil.zip_dir(unzipdir+"_bk", unzipdir+"_bk.zip")
    shutil.rmtree(unzipdir+"_bk")

    # 修改目录名称
    for i in os.listdir(unzipdir):
        if os.path.isdir(f"{os.getcwd()}/{unzipdir}/{i}"):
            dirhash = i.split(" ")[-1][-12:]
            shutil.move(unzipdir, f"notion {dirhash}")
            unzipdir = f"notion {dirhash}"
            break
        
    try:
        data = blog_get_info.list_files(unzipdir, [], [])
        cr(os.getcwd(), os.getcwd(), data)
        oldblog = f"{HEXO_BLOG}/source/_posts/{dirhash}"
        if os.path.isdir(oldblog):
            shutil.rmtree(oldblog)
        shutil.copytree(dirhash, oldblog)
    except Exception as e:
        print(e)
    # 删除残留文件
    if os.path.isdir(dirhash):
        shutil.rmtree(dirhash)
    if os.path.isdir(unzipdir):
        shutil.rmtree(unzipdir)
    if os.path.isfile(filename):
        os.remove(filename)

# 没有替换博客文件夹，没有删除生成的文件
def process_local(workdir, filename):
    os.chdir(workdir) #修改当前工作目录
    print("cwd", os.getcwd()) #获取当前工作目录
    
    dirhash, unzipdir = None, filename.replace(".zip", "")

    # 解压
    zipUtil.unzip(filename)

    # # 备份无哈希结构的压缩包
    copyfile(unzipdir, unzipdir+"_bk")
    rec_h = get_hash(unzipdir)
    remove_hash(rec_h, unzipdir+"_bk")
    zipUtil.zip_dir(unzipdir+"_bk", unzipdir+"_bk.zip")
    shutil.rmtree(unzipdir+"_bk")

    # 修改目录名称
    for i in os.listdir(unzipdir):
        if os.path.isdir(f"{os.getcwd()}/{unzipdir}/{i}"):
            dirhash = i.split(" ")[-1][-12:]
            shutil.move(unzipdir, f"notion {dirhash}")
            unzipdir = f"notion {dirhash}"
            break

    data = blog_get_info.list_files(unzipdir, [], [])
    cr(os.getcwd(), os.getcwd(), data)

if __name__ == '__main__':
    process_local("uploads", "cfc660a8-dc20-4cd4-beb2-92ad66330fc0_Export-2046ac04-5f6f-4208-a321-7af39d5d30f1.zip")
