detect_adjoin
====
IIDX DPにおける隣接皿系譜面（隣接皿 / 無理皿 / 無茶皿）の抽出および，それらの配置を集計するツール  
集計結果は<a href="https://tbx-ryu.github.io/detect_adjoin/">Github Pages</a>にて公開  
譜面の抽出および配置の集計に用いた譜面データは<a href=https://textage.cc/>TexTage</a>様より拝借

## Description
本ツールは以下2つのモジュールで構成される．  
* notes.py  
  TexTageの譜面データをnumpy配列として読み込むモジュール．
* check_adjoin.ipynb  
  numpy配列の譜面データから隣接皿を持つ譜面の抽出・配置の集計を行い，結果をindex.htmlへ出力するモジュール
