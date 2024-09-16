#!/usr/bin/env bash

#
# Script to computing SCLITE metrics for Google Speech-To-Text and AWS Transcribe services with reference and hypothesis
# files in TRN format.
# More info in resources/sctk/doc/sclite.htm
#

reference_transcript_file="../../files/tei/trn/FCINI002b_TEI.trn"

echo "------------------------------------------------------------------------------------------------"
echo "SCLITE TRN-TRN Metrics for Google STT"
google_hypothesis_file="../../files/transcriptions/google/trn/FCINI002b.trn"
../../resources/sctk/bin/sclite -r "${reference_transcript_file}" trn -h "${google_hypothesis_file}" trn -i rm -o dtl

echo "------------------------------------------------------------------------------------------------"
echo "SCLITE Metrics for AWS Transcribe"
aws_hypothesis_file="../../files/transcriptions/aws/trn/FCINI002b.trn"
../../resources/sctk/bin/sclite -r "${reference_transcript_file}" trn -h "${aws_hypothesis_file}" trn -i rm -o dtl