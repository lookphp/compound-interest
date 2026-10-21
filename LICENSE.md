# 许可

本书采用**双许可**：文字与代码分开授权。README 里那句 `Text CC BY-NC 4.0, code MIT` 指的就是这份文件。

## 文字部分 —— CC BY-NC 4.0

适用范围：`book/` 目录下的全部内容（含 `book/figures/` 里的图表），以及 `README.md` 的正文。

你可以：

- **共享** —— 以任何媒介或格式复制、发行本书
- **演绎** —— 修改、转换、以本书为基础进行创作

但必须遵守：

- **署名** —— 标注来源，并说明是否作了修改
- **非商业性** —— 不得用于商业目的
- **不得增加额外限制** —— 不得用法律条款或技术手段限制他人做上述许可允许的事

许可全文：<https://creativecommons.org/licenses/by-nc/4.0/legalcode.zh-hans>

## 代码部分 —— MIT

适用范围：`tools/` 目录下的全部脚本，以及 `index.html` 的构建逻辑。

```
MIT License

Copyright (c) 2026 《没有一种复利叫坚持》作者

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 为什么分开

脚本是工具，用 MIT 是为了让人随便拿走、改成自己的检查器，包括商用。

文字是观点，用非商业是为了防止有人把这本书包装成课程或付费专栏去卖——**书里每一个数字都可以被你自己复算一遍，这件事本身不该被谁拿去当卖点。**

## 数据

`tools/data/spx_monthly.csv` 是 [datasets/s-and-p-500](https://github.com/datasets/s-and-p-500) 的固定快照（原始数据来自 Robert Shiller 的公开数据集）。数据本身的权利状态以原始来源为准，本仓库只声明自己的整理工作。
