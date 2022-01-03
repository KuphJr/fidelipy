import sys

sys.path.append("../src")

project = "fidelipy"
copyright = "2022 Darik Harter"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
]

intersphinx_mapping = {"python": ("https://docs.python.org/3/", None)}
