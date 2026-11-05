#!/usr/bin/env python3
"""Eight independently authored build examples; never reads evaluation inputs."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extract
import redflags

EXAMPLES = [
    ('P1', 'Main purush hoon, umar sixty eight saal.'),
    ('P1', 'Mujhe apni umar nahi batani.'),
    ('P5', 'Is sawaal ka jawab dena zaroori hai kya?'),
    ('P2', 'Umm... hmm... bas...'),
    ('P3', 'Pichhle hafte se pet mein jalan ho rahi hai.'),
    ('P2', 'Kal dopahar se baaye kaan mein dard hai, sunai bhi kam de raha hai.'),
    ('P4', 'Seene mein dard nahi, saans bhi theek hai; halka sar bhaari hai.'),
    ('P4', 'Behosh nahi hua, lekin saans lene mein bahut takleef hai.'),
]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real',action='store_true',help='Allow Groq calls for uncached examples')
    args=parser.parse_args()
    rows=[]
    for question,transcript in EXAMPLES:
        result=extract.extract(question,transcript,allow_real=args.real)
        flags=redflags.detect(transcript,result)
        row={'question':question,'transcript':transcript,'extracted':result,'red_flags':flags}
        rows.append(row)
        print(json.dumps(row,ensure_ascii=False,indent=2),flush=True)
    output=extract.ROOT/'examples/step1_outputs.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Saved eight independently authored examples to '+str(output),flush=True)


if __name__=='__main__': main()
