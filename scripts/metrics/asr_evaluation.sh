#!/usr/bin/env bash

#
# Script to computing ASR-Evaluation metrics for Google Speech-To-Text and AWS Transcribe services.
# More info at https://github.com/belambert/asr-evaluation
#

reference_transcript_file="../../files/tei/txt/FCINI002b_TEI.txt"

echo "------------------------------------------------------------------------------------------------"
echo "ASR-Evaluation Metrics for Google STT"
google_hypothesis_file="../../files/transcriptions/google/txt/FCINI002b.txt"
wer "${reference_transcript_file}" "${google_hypothesis_file}"

echo "------------------------------------------------------------------------------------------------"
echo "ASR-Evaluation Metrics for AWS Transcribe"
aws_hypothesis_file="../../files/transcriptions/aws/txt/FCINI002b.txt"
wer "${reference_transcript_file}" "${aws_hypothesis_file}"