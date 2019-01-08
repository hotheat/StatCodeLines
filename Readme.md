统计一个目录中 py 文件的 code 行数，注释行数，docstring 行数和空格行数。

# 运行方法

```python
usage: stat_code.py [-h] -p PATH [-k K] [--print]

Statistics for .py file from the path

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  the input path (default: None)
  -k K                  the max depth in the path. If exceed the max depth, it
                        will be ignored (default: 3)
  --print               print the 10 largest results sorted by total rows.
                        (default: False)
```

```
python stat_code.py -p . -k 5 --print
```

# 输出结果

具体结果在 `code_statistics.csv` 中。

Github 上传后会自动将最后的空行删除，所以在 Github 上看到的行数与实际结果可能不匹配。

添加 --print 参数后，下面是不同 depth 的输出结果， test 目录层数只有 3 层，其中 PATH 参数的目录记为第一层（root），在 -k 设为 5 后，仍只输出 3 层。

![mark](http://qnpic.sijihaiyang.top/blog/20190109/oM3ra0rxjxPv.png?imageslim)

# Docstring 的判定

代码中如果出现以下形式，都会被认为是 Docstring.

```
"""
test
test
test
"""
```

```
"""test"""
```

```
'''test'''
```

```
"test"
```

```
'test'
```

```
"""
test"""
```

```
"""test
"""
```

```
'''test
'''
```

```
'''
test'''
```

而下面这种形式不会被认为是 docstring，这种形式在 Python 中是错误的语法，程序不会识别错误，会识别为 code。

```
"......
"
```