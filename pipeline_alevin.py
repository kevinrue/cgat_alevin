"""===========================
Pipeline template
===========================

.. Replace the documentation below with your own description of the
   pipeline's purpose

Overview
========

This pipeline computes the word frequencies in the configuration
files :file:``pipeline.yml` and :file:`conf.py`.

Usage
=====

See :ref:`PipelineSettingUp` and :ref:`PipelineRunning` on general
information how to use cgat pipelines.

Configuration
-------------

The pipeline requires a configured :file:`pipeline.yml` file.
cgatReport report requires a :file:`conf.py` and optionally a
:file:`cgatreport.yml` file (see :ref:`PipelineReporting`).

Default configuration files can be generated by executing:

   python <srcdir>/pipeline_@template@.py config

Input files
-----------

None required except the pipeline configuration files.

Requirements
------------

The pipeline requires the results from
:doc:`pipeline_annotations`. Set the configuration variable
:py:data:`annotations_database` and :py:data:`annotations_dir`.

Pipeline output
===============

.. Describe output files of the pipeline here

Glossary
========

.. glossary::


Code
====

"""

from ruffus import *
from cgatcore import pipeline as P

import sys
import os
import re
import pandas as pd
import glob


PARAMS = P.get_parameters(
    ["%s/pipeline.yml" % os.path.splitext(__file__)[0],
     "../pipeline.yml",
     "pipeline.yml"])


SAMPLES = pd.read_csv("samples.csv")
SAMPLES.set_index('name', inplace=True)


def get_gex_fastq(dir):
    '''Docstring'''
    fastq1_pattern = PARAMS["pattern"]["fastq1"]
    fastq1_glob = f"{dir}/*{fastq1_pattern}*"
    fastq1 = glob.glob(fastq1_glob)

    if len(fastq1) == 0:
        raise OSError(f"No file matched pattern: {fastq1_glob}")

    fastq2 = [file.replace(PARAMS["pattern"]["fastq1"], PARAMS["pattern"]["fastq2"]) for file in fastq1]

    for file in fastq2:
        if not os.path.exists(file):
            raise OSError(f"Paired file not found: {file}")

    return {'fastq1' : fastq1, 'fastq2' : fastq2 }


@follows(mkdir("alevin"))
@transform("data/*_fastqs",
           regex(r"data/([A-Za-z0-9_]*)_fastqs"),
           r"alevin/\1.done")
def salmon_alevin(infile, outfile):
    '''Docstring'''

    sample = re.search('data/(.*)_fastqs', infile).group(1)

    fastqs = get_gex_fastq(infile)
    fastq1s = " ".join(fastqs["fastq1"])
    fastq2s = " ".join(fastqs["fastq2"])

    outdir = os.path.join("alevin", sample)

    cells = SAMPLES['cells'][sample]

    chemistry = SAMPLES['chemistry'][sample]
    if chemistry == "SC3Pv2":
        chemistry_option = "--chromium"
    elif chemistry == "SC3Pv3":
        chemistry_option = "--chromiumV3"
    else:
        raise NameError('Invalid chemistry.')

    salmon_index = PARAMS["alevin"]["index"]

    tx2gene = PARAMS["alevin"]["tx2gene"]

    job_threads = PARAMS["alevin"]["threads"]
    job_memory = PARAMS["alevin"]["memory"]

    statement = """
    salmon alevin
        -l ISR
        -1 %(fastq1s)s
        -2 %(fastq2s)s
        %(chemistry_option)s
        -i %(salmon_index)s
        -p %(job_threads)s
        -o %(outdir)s
        --tgMap %(tx2gene)s
        --expectCells %(cells)s
    """

    P.run(statement)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    P.main(argv)


if __name__ == "__main__":
    sys.exit(P.main(sys.argv))
