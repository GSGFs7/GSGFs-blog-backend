from markdown_it_rs_py import MarkdownIt


class Markdown:
    def __init__(self, html: bool = False, linkify: bool = False):
        self.md = MarkdownIt(html=html, linkify=linkify)

    def render(self, markdown: str) -> str:
        return self.md.render(markdown)


if __name__ == "__main__":
    test_md = """---
title: Test Markdown
description: This is a test markdown file.
tags: [test, markdown]
datatime: 2025-07-23 14:34:00
math: true
keywords: 
  - test
  - markdown
---

# heading

content

$$
E = mc^2
$$

<a herf="https://a.com">inline html</a>
"""

    print(Markdown(html=True, linkify=True).render(test_md))
