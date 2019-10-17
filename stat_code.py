import os
from collections import Counter, OrderedDict
import re
import pandas as pd
import numpy as np
from prettytable import PrettyTable
import argparse
from colorama import Fore, init, Style

init(autoreset=True)


def check_path(path):
    if os.path.isdir(path):
        return
    else:
        raise ValueError(f"{path} don't exist. Please check!")


class Model(object):
    data = {}


class FilesStatistics(Model):
    def __init__(self, file):
        self.file = file
        self.total = 0
        self.docstring = 0
        self.comments = 0
        self.none = 0
        self.code = 0
        self.multilines_mode = False  # 是否在多行字符串中
        self.checked = True  # 是否已经遍历过该行

    def comments_add(self, line):
        if not self.multilines_mode and line.startswith('#'):
            self.comments += 1
            self.checked = True

    def docstring_in_oneline(self, line):
        # docstring 在同一行
        if not self.multilines_mode and (re.match(r'^("{3}|\'{3}).+("{3}|\'{3})$', line) or
                                         re.match(r'^("{1}|\'{1})[^(\'|").]+("{1}|\'{1})$', line)):
            self.docstring += 1
            self.checked = True

    def none_add(self, line):
        if not self.multilines_mode and line == '':
            self.none += 1
            self.checked = True

    def total_add(self, ):
        self.total += 1

    def check_last_line(self, line):
        # 最后一行是空行，总行数和空行数需加 1
        if line.endswith('\n'):
            self.none += 1
            self.total += 1

    def parse_file(self):
        with open(self.file, encoding='utf-8') as f:
            for l in f:
                line, self.checked = l.strip(), False
                self.total_add()
                self.comments_add(line)
                self.docstring_in_oneline(line)
                self.none_add(line)

                # 多行字符串开始
                if not self.checked and not self.multilines_mode and (re.match(r'(^"{3}\w*|^\'{3}\w*)', line)):
                    self.docstring += 1
                    self.multilines_mode = True
                    self.checked = True
                # 多行字符串结束
                elif self.multilines_mode and (re.match(r'(\w*"""$|\w*\'\'\'$)', line)):
                    self.docstring += 1
                    self.multilines_mode = False
                    self.checked = True
                # 多行字符串
                elif self.multilines_mode:
                    self.docstring += 1
                    self.checked = True
                # code 行
                elif not self.checked:
                    self.code += 1
                # print('start line', line, self.in_multilines, self.docstring)
            # 最后一行是否为空行
            try:
                self.check_last_line(l)
            except UnboundLocalError:
                print('{} is an empty file'.format(self.file))
        return self.stat()

    def stat(self):
        attrs = ['total', 'docstring', 'comments', 'none', 'code']
        d = OrderedDict()
        for k, v in self.__dict__.items():
            if k in attrs:
                d[k] = v
        Model.data[self.file] = d


class RootStatistics(Model):
    def __init__(self, args):
        self.root = os.path.abspath(args.path)
        check_path(self.root)
        self.depth = args.k
        self._print = args.print
        self.excludes = [] if args.excludes is None else args.excludes
        self.max_k = 0
        self.subpath_data = {}
        self.count = {}

    def path_depth(self, path, files):
        if any([i.endswith('.py') for i in files]):
            replaced = path.replace(self.root, '')
            c = Counter(replaced)
            return c['\\'] + c['/'] + 1
        else:
            return 1

    def parse_current(self, curpath, files):
        contained = any([i in curpath for i in self.excludes])
        for f in files:
            if f.endswith('.py') and not contained:
                file = os.path.join(curpath, f)
                fs = FilesStatistics(file)
                fs.parse_file()

    def parse_index(self, row):
        line = [0] * (self.depth + 1)
        line[0] = self.root
        row = row.replace(self.root, '')
        splitrow = re.split(r'\\|/', row)
        for i, v in enumerate(splitrow[:-1]):
            if v:
                line[i] = v
        line[-1] = splitrow[-1]
        return line

    def to_dataframe(self):
        df = pd.DataFrame(Model.data).T
        df.reset_index(inplace=True)
        full_cols = ['subpath_{}'.format(str(i + 1)) for i in range(self.depth)]
        full_cols[0] = 'root'
        full_cols.append('file')

        full_df = pd.DataFrame(df['index'].apply(lambda r: self.parse_index(r)).values.tolist(),
                               columns=full_cols)
        # depth 不超过最大深度 max_k
        subpath_df = full_df.iloc[:, :-1].iloc[:, :self.max_k]
        subpath_df['file'] = full_df['file']
        subpath_df.replace(0, np.nan, inplace=True)
        df = pd.concat([subpath_df, df], axis=1)
        print('非空代码行数: ', df['code'].sum())
        print('总行数: ', df['total'].sum())
        df.to_csv('code_statistics.csv', index=False)

    def print_df(self):
        df = pd.read_csv('code_statistics.csv')
        df.drop('index', axis=1, inplace=True)
        df = df.sort_values(by='total', ascending=False)[:10]
        table = PrettyTable()
        for col in df.columns:
            # RESET_ALL 还原至初始设置
            table.add_column(Fore.CYAN + col, [Style.RESET_ALL + str(i) for i in df[col]])
        print(table, flush=True)

    def parse_root(self):
        for root, dirs, files in os.walk(self.root, topdown=True):
            depth = self.path_depth(root, files)
            # get max k
            if depth > self.max_k:
                self.max_k = depth

            if depth <= self.depth:
                self.parse_current(root, files)

        self.to_dataframe()
        if self._print:
            self.print_df()


def arguements():
    parser = argparse.ArgumentParser(
        description='Statistics for .py file from the path',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-p', "--path", help="the input path", required=True)
    parser.add_argument("-k", help="the max depth in the path. If exceed the max depth, it will be ignored.",
                        type=int, default=10)
    parser.add_argument("--print", help="print the 10 largest results sorted by total rows.", action='store_true')
    parser.add_argument("--excludes", help="excludes folders", nargs='*')

    args = parser.parse_args()
    return args


def main():
    args = arguements()
    cs = RootStatistics(args)
    cs.parse_root()


def test():
    path = './test'
    k = 3
    _print = True
    cs = RootStatistics(path, k, _print)
    cs.parse_root()


if __name__ == '__main__':
    main()
    # test()
    # f = 'test/allmaps.py'
    # fs = FilesStatistics(f)
    # print(fs.parse_file())
