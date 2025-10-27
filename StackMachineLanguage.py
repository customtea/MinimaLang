from collections import deque

class StackMachine:
    def __init__(self):
        self.stack = deque()
        self.words = {}
        self.labels = {}

    def run(self, code):
        tokens = code.split()
        ip = 0
        defining = False
        def_name = None
        def_body = []

        while ip < len(tokens):
            tok = tokens[ip]
            ip += 1

            # 数値 or 文字列 → スタックに積む
            if tok.replace('.', '', 1).isdigit() or tok.startswith('"'):
                self.stack.append(tok.strip('"'))
                continue

            # 関数定義の開始
            if tok == ':':
                def_name = tokens[ip]
                ip += 1
                defining = True
                def_body = []
                continue

            # 関数定義の終了
            if tok == ';' and defining:
                self.words[def_name] = list(def_body)
                defining = False
                def_name = None
                continue

            # 定義中なら命令をバッファに保存
            if defining:
                def_body.append(tok)
                continue

            # ラベル定義
            if tok == 'LABEL':
                label = self.stack.pop()
                self.labels[label] = ip
                continue

            # ジャンプ（スタックトップを参照）
            if tok == 'JMP':
                label = self.stack.pop()
                ip = self.labels[label]
                continue

            # 条件ジャンプ（スタックトップの条件を確認）
            if tok == 'JZ':
                label = self.stack.pop()
                cond = self.stack.pop()
                if cond == '0' or cond == 0:
                    ip = self.labels[label]
                continue

            # ビルトイン命令群
            if tok == 'ADD':
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(float(a) + float(b))
                continue
            if tok == 'MUL':
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(float(a) * float(b))
                continue
            if tok == 'SUB':
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(float(a) - float(b))
                continue
            if tok == 'DIV':
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(float(a) / float(b))
                continue
            if tok == 'DUP':
                self.stack.append(self.stack[-1])
                continue
            if tok == 'SWAP':
                a, b = self.stack.pop(), self.stack.pop()
                self.stack.append(a)
                self.stack.append(b)
                continue
            if tok == 'DROP':
                self.stack.pop()
                continue
            if tok == 'PRINT':
                print(self.stack.pop())
                continue

            # ユーザー定義関数呼び出し
            if tok in self.words:
                self.run(' '.join(self.words[tok]))
                continue

            raise ValueError(f"Unknown token: {tok}")
