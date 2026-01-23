#!/usr/bin/env python


"""
**For nvidia GPU!**
The scripts are used to generate requirements.txt for docker.
"""

import re
import subprocess

if __name__ == "__main__":
    result = subprocess.run(
        "uv pip freeze",
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    packages = result.stdout.split()

    # Exclude all dependencies of sentence-transformers
    disabled = [
        re.compile("^filelock=="),
        re.compile("^fsspec=="),
        re.compile("^hf-xet=="),
        re.compile("^huggingface-hub=="),
        re.compile("^jinja2=="),
        re.compile("^joblib=="),
        re.compile("^markupsafe=="),
        re.compile("^mpmath=="),
        re.compile("^networkx=="),
        re.compile("^numpy=="),
        re.compile("^nvidia-"),
        re.compile("^regex=="),
        re.compile("^safetensors=="),
        re.compile("^scikit-learn=="),
        re.compile("^scipy=="),
        re.compile("^setuptools=="),
        re.compile("^sympy=="),
        re.compile("^threadpoolctl=="),
        re.compile("^tokenizers=="),
        re.compile("^torch=="),
        re.compile("^tqdm=="),
        re.compile("^transformers=="),
        re.compile("^triton=="),
    ]

    res = []
    for pac in packages:
        need_to_disable = False
        for r in disabled:
            if r.match(pac) is not None:
                need_to_disable = True
                break
        # comment out
        if need_to_disable:
            res.append("#" + pac)
        else:
            res.append(pac)

    with open("requirements.txt", "w") as file:
        file.write("torch  --index-url https://download.pytorch.org/whl/cpu\n")
        for pac in res:
            file.write(pac + "\n")
