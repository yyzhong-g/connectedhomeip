#!/usr/bin/env python3
#
# Copyright (c) 2022 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Merge the trace files between commissioner and commissionee.
Use the gap between SendPBKDFParamRequest and HandlePBKDFParamRespnse,
and place commissionee's HandlePBKDFParamResponse in the middle.
Output file is called "output.json"
"""

import argparse
import json

def _parse_args():
  """Parse and return command line arguments."""

  parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--commissioner',
                      required='true',
                      help='commissioner trace json file.')
  parser.add_argument('--commissionee',
                      required='true',
                      help='commissioner trace json file.')
  return parser.parse_args()

def _main(args):
  with open(args.commissioner, "r") as file:
    commissioner_json = json.load(file)

  with open(args.commissionee, "r") as file:
    commissionee_json = json.load(file)

  for trace_event in commissioner_json["traceEvents"]:
    if trace_event["name"] == "SendPBKDFParamRequest":
      t1 = trace_event["ts"] + trace_event["dur"]
    
    if trace_event["name"] == "HandlePBKDFParamResponse":
      t2 = trace_event["ts"]

  for trace_event in commissionee_json:
    if "name" in trace_event:
      if trace_event["name"] == "HandlePBKDFParamRequest":
        if trace_event["ph"] == "B":
          t3 = trace_event["ts"]
        if trace_event["ph"] == "E":
          t4 = trace_event["ts"]
          break;


  # [SendPBKDFParamRequest]                               [HandlePBKDFParamResponse]
  #                           [HandlePBKDFParamRequest]
  #                       t1  t3                      t4  t2
  # delta1 = t2 - t1
  # delta2 = t4 - t3
  # offset = t1 + (delta2 - delta1) / 2
  print(t1, t2, t3, t4)
  offset = t1 + (t2 - t1 - t4 + t3) / 2;
  print(offset)

  for trace_event in commissionee_json:
    if "ts" in trace_event:
      trace_event["ts"] = trace_event["ts"] + offset
      commissioner_json["traceEvents"].append(trace_event)

  with open("output.json", "w") as json_file:
    json.dump(commissioner_json, json_file)

if __name__ == '__main__':
  _main(_parse_args())
