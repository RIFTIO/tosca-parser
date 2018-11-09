=====
Usage
=====

The TOSCA Parser can be used as a library by any client program.

For an easy reference on how TOSCA Parser can be used programmatically or to
test that the a TOSCA template passes validation, refer to the tosca_parser.py
test program which is located at the root level of the project.

Alternatively, use the parser via CLI
entry point as::
    tosca-parser --template-file=toscaparser/tests/data/tosca_helloworld.yaml
The value to the --template-file is required to be a relative or an absolute path.

For help, use:
    tosca-parser --help

Sample ETSI SOL001 v0.10 package:
     tosca-parser --template-file=toscaparser/tests/spec_samples/etsi_sol001/sunshinedb/sunshinedb.yaml -nrpv

