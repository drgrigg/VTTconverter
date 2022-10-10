#! /usr/bin/env python3
from __future__ import annotations
import os
import sys
import regex
import datetime
from datetime import timedelta

# MAX_DURATION = 10

class CaptionTime():
    the_time: datetime.datetime = None
    def __init__(self, h: int, m: int, s: int, f: int):
        self.the_time = datetime.datetime(2000,1,1,h,m,s,f * 1000)  # f is millisecs, we need microsecs
    def output(self) -> str:
        temp = self.the_time.strftime('%f') # this is microseconds, we want millisecs
        milli = temp[0:3]  # so just take first three digits
        retval = f'{str(self.the_time.hour).zfill(2)}:{str(self.the_time.minute).zfill(2)}:{str(self.the_time.second).zfill(2)},{milli}'
        return retval
    def diff_between(self, otherctime: CaptionTime) -> int:  # this will be seconds
        diff:timedelta  = otherctime.the_time - self.the_time
        return diff.total_seconds()


class Caption():
    start_time: CaptionTime = None
    end_time: CaptionTime = None
    text = ""
    def __init__(self, start: CaptionTime, end: CaptionTime, text: str):
        self.start_time = start
        self.end_time = end
        # # only want caption to remain visible for MAX_DURATION seconds
        # duration = self.start_time.diff_between(self.end_time)
        # # print(self.start_time.output(), self.end_time.output(), d)
        # if duration > MAX_DURATION:
        #     self.end_time.the_time = self.start_time.the_time + timedelta(seconds=MAX_DURATION)
        self.text = text

    @property
    def duration(self) -> int:  # seconds
        return self.start_time.diff_between(self.end_time)

    def output(self) -> str:
        startstr = self.start_time.output()
        endstr = self.end_time.output()
        return f'{startstr} --> {endstr}\n{self.text}\n'


captions = []

def read_vtt(filename:str):
    global captions
    vtt_pattern = r'(\d?\d?):?(\d\d):(\d\d).(\d\d\d) --> (\d?\d?):?(\d\d):(\d\d).(\d\d\d)'
    with open(filename, "r") as vtt:
        lines = vtt.readlines()
        vtt.close()
    
    line_num = 0
    tot_lines = len(lines) - 1
    while line_num < tot_lines:
        line = lines[line_num]
        match = regex.search(vtt_pattern, line)
        if match:
            print(line)
            starttime = get_time(match, start_count=1)
            endtime = get_time(match, start_count=5)
            line_num += 1  # advance to next line
            text = lines[line_num].strip()
            caption = Caption(start=starttime, end=endtime, text=text)
            captions.append(caption)
        line_num += 1


def write_srt(filename:str):
    with open(filename, 'w') as srt:
        capnum = 1
        for caption in captions:
            srt.write(f'{capnum}\n')
            capnum += 1
            srt.write(f'{caption.output()}\n')
        srt.close()


def get_time(match, start_count: int = 1):
    temp = match.group(start_count)
    if not temp:
        h = 0
    else:
        h = int(temp)
    m = int(match.group(start_count + 1))
    s = int(match.group(start_count + 2))
    f = int(match.group(start_count + 3)) 
    return CaptionTime(h,m,s,f)


def main() -> None:
    if len(sys.argv) < 2:
        print("USAGE: VTT_to_SRT.py filename")
        exit(0)
    vttpath = sys.argv[1]
    if os.path.exists(vttpath):
        read_vtt(vttpath)
        head, tail = os.path.split(vttpath)
        srtname = regex.sub(r'\.vtt', '.srt', tail)
        srtpath = os.path.join(head, srtname)
        write_srt(srtpath)


if __name__ == "__main__":
    main()
