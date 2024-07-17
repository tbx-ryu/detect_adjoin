import re
import chardet
import pdb
import random
import time
import js2py
from functools import wraps
import matplotlib.pyplot as plt
from contextlib import closing
from bs4 import BeautifulSoup

def checkEncoding(htmlpath):
    chunk_size = 100
    with open(htmlpath, 'rb') as f, \
            closing(chardet.UniversalDetector()) as detector:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            detector.feed(chunk)
            if detector.done:
                break
    return detector.result['encoding']

def myshow(array):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for pos in ["top", "right", "left", "bottom"]:
        ax.spines[pos].set_visible(False)
    extent = (0, 192, 16, 0)
    ax.set_yticks(range(0,16))
    ax.set_xticks(range(0,192, 192//4))
    ax.grid(color="k", linewidth=0.1, linestyle="--")
    p = plt.hlines([8], 0, 192, "blue", linestyles='dashed')

    ax.imshow(array, aspect=10, extent=extent)
    return fig

def split_dict(org_dict, split_rate=0.8):
    keys = list(org_dict)
    random.seed(23)
    random.shuffle(keys)
    head_dict, tail_dict = {}, {}
    split_idx = int(len(keys) * split_rate)
    for key in keys[:split_idx]:
        head_dict[key] = org_dict[key]
    for key in keys[split_idx:]:
        tail_dict[key] = org_dict[key]
    return head_dict, tail_dict

def parsePHP(phppath, enc=None):
    if enc is None:
        enc = checkEncoding(phppath)
        if enc != "utf-8": enc = "shift_jis"
    with open(phppath, "r", encoding=str(enc)) as f:
        soup = BeautifulSoup(f, "lxml")
    return soup

def get_hoshi_and_uno(diff_str):
    if diff_str == "-":
        diff_hoshi, diff_uno = "-", "-"
    else:
        diff_hoshi, diff_uno = diff_str.split(" (")
        diff_hoshi, diff_uno = diff_hoshi[1:], diff_uno[:-1]
    return diff_hoshi, diff_uno

def stop_watch(func):
    @wraps(func)
    def wrapper(*args, **kargs):
        # 処理開始直前の時間
        start = time.time()

        # 処理実行
        result = func(*args, **kargs)

        # 処理終了直後の時間から処理時間を算出
        elapsed_time = time.time() - start

        # 処理時間を出力
        print("{} ms in {}".format(elapsed_time * 1000, func.__name__))
        return result
    return wrapper

def get_unofficial_diff(phppath):
    body = parsePHP(phppath, enc="utf-8")
    unofficial_diff = {}
    for line in body.table.find_all("tr"):
        if not line.find_all("td"): continue
        col = line.find_all("td")
        diff_h, diff_a, diff_l, title = col[0].get_text(), col[1].get_text(), col[2].get_text(), col[3].get_text()
        diff_h_hoshi, diff_h_uno = get_hoshi_and_uno(diff_h)
        diff_a_hoshi, diff_a_uno = get_hoshi_and_uno(diff_a)
        diff_l_hoshi, diff_l_uno = get_hoshi_and_uno(diff_l)
        unofficial_diff[title] = {"diff_a_hoshi":diff_a_hoshi, "diff_a_uno":diff_a_uno,
                                  "diff_h_hoshi":diff_h_hoshi, "diff_h_uno":diff_h_uno,
                                  "diff_l_hoshi":diff_l_hoshi, "diff_l_uno":diff_l_uno}
    return unofficial_diff

def get_tables(titletbl_path, actbl_path):
    with open(titletbl_path, "r", encoding="cp932") as f:
        jstxt = f.read()
    jstxt = re.sub(".fontcolor\(.*\)", "", jstxt)
    with open(actbl_path, "r", encoding="cp932") as f:
        jstxt += f.read()
    titletbl, actbl = {}, {}
    context = js2py.EvalJs({"titletbl":titletbl, "actbl":actbl})
    context.execute(jstxt)
    return context.titletbl, context.actbl

def get_keys(titletbl, actbl, difficulty, dp=True):
    ret_list = []
    for fbasename in list(titletbl):
        diffs = {}
        ver, numNotes, opt, genre, arist, title, *_ = titletbl[fbasename]
        try:
            if dp: # dp
                diffs["n"], diffs["h"], diffs["a"], diffs["l"] = list(actbl[fbasename])[15:22:2]
            else: # sp
                diffs["n"], diffs["h"], diffs["a"], diffs["l"] = list(actbl[fbasename])[5:12:2]
        except:
            continue
        for_add = [[fbasename, diffs[x], x, ver] for x in difficulty if diffs[x] > 0]
        ret_list.extend(for_add)
    return ret_list

if __name__ == "__main__":
    pdb.set_trace()
