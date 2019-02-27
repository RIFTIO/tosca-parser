=====
Usage
=====

The TOSCA Parser can be used as a library by any client program.

For an easy reference on how TOSCA Parser can be used programmatically or to
test that the a TOSCA template passes validation, refer to the tosca_parser.py
test program which is located at the root level of the project.

Alternatively, use the parser via CLI entry point as::
    tosca-parser --template-file=toscaparser/tests/data/tosca_helloworld.yaml

You can also provide a csar file as the template-file. In case of CSAR file, all the
referenced artifiacts must be present in the archive file, else the parser will
show these errors and not the SOL001 TOSCA errors.

###
CLI
###

usage: tosca-parser [-h] -f <filename> [-nrpv] [--debug] [--verbose]

Arguments:

  -f <filename>, --template-file <filename>
                        YAML template or CSAR file to parse.
optional arguments:
  -h, --help            show this help message and exit
  -nrpv                 Ignore input parameter validation when parse template.
  --debug               debug mode for print more details other than raise
                        exceptions when errors happen as possible
  --verbose             verbose mode for print more details when raising
                        exceptions as errors happen.


Sample ETSI SOL001 v0.10.0 package:
     tosca-parser --template-file=toscaparser/tests/spec_samples/etsi_sol001/sunshinedb/Definitions/sunshinedb.yaml -nrpv
