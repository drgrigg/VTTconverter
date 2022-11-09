#! /usr/bin/env python3
from __future__ import annotations
import os
import sys
import regex
import datetime
from datetime import timedelta


class CueHeader:
	title = ""
	audiofile = ""
	cuefile = ""
	out_format = ""
	performer = ""
	# duration_in_frames = 0
	duration_in_seconds = 0.0


class CueTime:
	# no hours, just have minutes > 60
	minutes = 0
	seconds = 0
	frames = 0  # note each frame is 1/75th of a sec in cue sheets

	def __init__(self, tot_frames: int):
		self.minutes = int(tot_frames / (60 * 75))
		remainder = tot_frames - (self.minutes * 60 * 75)
		self.seconds = int(remainder / 75)
		remainder2 = tot_frames - (self.seconds * 75) - (self.minutes * 60 * 75)
		self.frames = int(remainder2)

	@property
	def in_frames(self) -> int:
		total = self.frames + (75 * self.seconds) + (75 * 60) * self.minutes
		return total
	@property
	def in_seconds(self) -> float:
		return float(self.in_frames) / 75.0

	def __sub__(self, other):  # calculate difference in seconds
		return self.in_seconds - other.in_seconds

	def output(self) -> str:
		return str(self.minutes).zfill(2) + ":" + str(self.seconds).zfill(2) + ":" + str(self.frames).zfill(2)



class CueTrack:
	order = 0
	title = ""
	start_time = CueTime(0)
	offset = ""
	color = ""
	level = 0
	url = ""
	# duration_in_frames = 0
	duration_in_seconds = 0.0
    
	def output(self, tracknum: int) -> str:
		outstr = ''
		outstr += f'  TRACK {str(tracknum).zfill(2)} AUDIO\n'
		outstr += f'    TITLE "{self.title}"\n'
		outstr += f'    INDEX 01 {self.start_time.output()}\n'
		outstr += f'    REM COLOR blue\n'
		return outstr


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
        diff:timedelta  = otherctime - self.the_time
        return abs(diff.total_seconds())
    def total_seconds(self) -> int:
        diff:timedelta  = self.the_time - datetime.datetime(2000,1,1,0,0,0,0 * 1000)
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
tracks = []

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



def write_cue(filename:str):
    global tracks
    caption: Caption = None
    for caption in captions:
        track = CueTrack()
        track.start_time = CueTime(caption.start_time.total_seconds() * 75)
        track.title = caption.text
        tracks.append(track)
            
    with open(filename, 'w') as cue:
        tracknum = 1
        # write cuefile header
        cue.write('TITLE "Dummy"\n')
        cue.write('FILE "dummy.wav" WAVE\n')
        cue.write('PERFORMER "David Grigg & Perry Middlemiss"\n')
        track: CueTrack = None
        for track in tracks:
            cue.write(track.output(tracknum))
            tracknum += 1
    cue.close()


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
        print("USAGE: VTT_to_Cue.py filename")
        exit(0)
    vttpath = sys.argv[1]
    if os.path.exists(vttpath):
        read_vtt(vttpath)
        head, tail = os.path.split(vttpath)
        cuename = regex.sub(r'\.vtt', '.cue', tail)
        cuepath = os.path.join(head, cuename)
        write_cue(cuepath)


if __name__ == "__main__":
    main()