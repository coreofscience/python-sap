# python-sap
Python SAP

### Running examples

Installing

```
pip install -e .
```

#### SAP module

SAP module depends on have already graphml files generated using `tos` module.

Running the example

```
sap run-example <example_name>  # e.g. visj_export
```

#### ToS module

ToS module depends on have already isi file exported by using wos.

Running the example

```
tos run-example <example_name>  # e.g. isi_to_graphml
```
