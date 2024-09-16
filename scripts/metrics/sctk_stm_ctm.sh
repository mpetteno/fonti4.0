#!/usr/bin/env bash

#
# Script to computing SCLITE metrics for Google Speech-To-Text and AWS Transcribe services with reference file in STM
# format and hypothesis file in CTM format.
# More info in resources/sctk/doc/sclite.htm
#

reference_transcript_file="../../files/tei/stm/FCINI002b_TEI.stm"

echo "------------------------------------------------------------------------------------------------"
echo "SCLITE STM-CTM Metrics for Google STT"
google_hypothesis_file="../../files/transcriptions/google/ctm/FCINI002b.ctm"
../../resources/sctk/bin/sclite -r "${reference_transcript_file}" stm -h "${google_hypothesis_file}" ctm -m ref -o dtl

echo "------------------------------------------------------------------------------------------------"
echo "SCLITE STM-CTM Metrics for AWS Transcribe"
aws_hypothesis_file="../../files/transcriptions/aws/ctm/FCINI002b.ctm"
../../resources/sctk/bin/sclite -r "${reference_transcript_file}" stm -h "${aws_hypothesis_file}" ctm -m ref -o dtl