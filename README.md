# python-sap

![Python package](https://github.com/coreofscience/python-wostools/workflows/Python%20package/badge.svg)

SAP Algorithm written in Python.

## Installing

First make sure you have the `igraph` library installed at system level:

```shell
# In Arch based linux distributions
sudo pacman -S igraph
# In Debian based linux distributions (Ubuntu, etc.)
sudo apt install libigraph0-dev
```

Then you can install all the python things with:

```
pip install -U python-sap
```

## Console script

After installing, you get access to some console scripts with which
you can start trying things around:

```bash
$ sap describe docs/jupyter-sap/savedrecs.txt
IGRAPH DN-- 90 343 --
+ attr: AU (v), BP (v), DI (v), J9 (v), PY (v), VL (v), _connections (v), _elaborate_sap (v), _leaf_connections (v), _raw_sap (v), _root_connections (v), extended_leaf (v), extended_root (v), label (v), leaf (v), name (v), root (v), sap (v), trunk (v)
```

This one describes all the collections you have,

```bash
$ sap root docs/jupyter-sap/savedrecs.txt
1.00 Skumryev V, 2003, NATURE, V423, P850, DOI 10.1038/nature01687 https://dx.doi.org/10.1038/nature01687
0.91 Ferrando R, 2008, CHEM REV, V108, P845, DOI 10.1021/cr040090g https://dx.doi.org/10.1021/cr040090g
0.89 Nogues J, 1999, J MAGN MAGN MATER, V192, P203, DOI 10.1016/S0304-8853(98)00266-2 https://dx.doi.org/10.1016/S0304-8853(98)00266-2
...
```

Shows the root of the topic in the bibliography collection you pass in, feel
free to:

```bash
sap --help
```

to explore all the commands and options you can use.

## Python API

The Python API is quite small, here's the minimal working example:

```python
from sap import load, Sap, CollectionLazy

sap = Sap()
graph = next(load(CollectionLazy(file1, file2, ...)))
tree = sap.tree()
```

then `tree` is an `igraph.Graph` labeled with all the things you would need
for analysis.

## Development

Check the `CONTRIBUTING` guide.
