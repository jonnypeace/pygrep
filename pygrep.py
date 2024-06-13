#!/usr/bin/python3

r"""
PYGREP - Python string and regex search
=======================================

SYNOPSIS
========
./pygrep.py [-s keyword/character [position]] | [-p regex [position|all]] [-e keyword/character position] [-i] [-l int|$|$-int|int-int] [-of] [-ol] [-f /path/to/file]

Author and Github
=================
Author: Jonny Peace, email: jonnypeace@outlook.com
Link for further information can be found here...
https://github.com/jonnypeace/pygrep/blob/main/README.md

Description
===========
Python string and regex search made easy. Select characters/keywords from and to sections of a line, further enhance with python regex, and specific lines.
Can accept stdin from a pipe or using the -f|--file flag

OPTIONS
=======
-s  | --start       can be used standlone (without --pyreg) or with --pyreg. [keyword/character [position]]
-e  | --end         is optional. Provides an end to the line you are searching for. [keyword/character position]
-of | --omitfirst   is optional for deleting the first characters of your match. Only works with --start
-ol | --omitlast    is optional and same as --omitfirst. Only works with --end
-l  | --lines       is optional and to save piping using tail, head or sed. [int|$|$-int|int-int|int-$]
-p  | --pyreg       can be used standlone (without --start) or with --start. [regex [position|all]]
-i  | --insensitive When used, case insensitive search is used. No args required.
-O  | --omitall     Optional, combination of -ol and -of
-u  | --unique      Optional, filters out lines which are the same, no further args necessary
-S  | --sort        Optional, currently sorts, but no reverse option supported yet, no further args necessary.
-c  | --counts      Optional, counts the number of lines which are the same, no further args necessary. Created unique output.
-f  | --file        /path/to/file.

Examples
========
 -s can be run with position being equal to all, to capture the start of the line
 ./pygrep.py -s root all -f /etc/passwd                 ## output: root:x:0:0::/root:/bin/bash
 ./pygrep.py -s root 1 -e \: 4 -f /etc/passwd           ## output: root:x:0:0:
 ./pygrep.py -s CRON 1 -e \) 2 -f /var/log/syslog       ## Output: CRON[108490]: (root) CMD (command -v debian-sa1 > /dev/null && debian-sa1 1 1)
 ./pygrep.py -s jonny 2 -f /etc/passwd                  ## output: jonny:/bin/bash

 without -of -ol -O
 ./pygrep.py -s \( 1 -e \) 1 -f testfile                ## output: (2nd line, 1st bracket)
 with -of -ol
 ./pygrep.py -s \( 1 -e \) 1 -of -ol -f testfile        ## output:  2nd line, 1st bracket

-p or --pyreg | I recommend consulting the python documentation for python regex using re.
 with -s & -p

 ./pygrep.py -s Feb -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test

 with -p
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test
"""

import argparse, re, sys, gc, mmap
from pathlib import Path
from multiprocessing import cpu_count
from typing import Iterable, Generator, Literal, TypedDict
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor

def print_err(msg):
    '''
    Print error messages, to std error and exit with exit code 1.
    '''
    colours = {'fail': '\033[91m', 'end': '\033[0m'}
    print(f'{colours["fail"]}{msg}{colours["end"]}', file=sys.stderr)
    exit(1)

# sense checking commandline input.
def sense_check(args,
                argTty: bool=False):
    '''
    Check args are sufficient for processing.
    '''

    # if not stdin or file, error
    if not args.file and argTty:
        print_err('Requires stdin from somewhere, either from --file or pipe')

    # Removed the required field for start, with the intention to use either start or pyreg, and build a pyreg function
    if not args.start and not args.pyreg:
        print_err('This programme requires the --start or --pyreg flag to work properly')

    if args.pyreg and len(args.pyreg) > 2:
        print_err('--pyreg can only have 2 args... search pattern and option')

    if args.start and len(args.start) > 2:
        print_err('--start has too many arguments, character or word followed by occurent number')

    if not args.start and args.pyreg and (args.omitall or args.omitfirst or args.omitlast):
        print_err('error, --pyreg not supported with --omitfirst or --omitlast or --omitall')

    if args.omitfirst and args.start == None:
        print_err('error, --omitfirst without --start')

    if args.omitlast and args.end == None:
        print_err('error, --omitlast without --end')

    if (args.omitall and args.omitfirst) or (args.omitall and args.omitlast):
        print_err('error, --omitfirst or --omitlast cant be used with --omitall')
    
    if args.start:
        if not len(args.start) > 1 and ( args.omitall or args.omitfirst or args.omitlast):
            print_err('error, --start requires numerical index or "all" with --omitfirst or --omitlast or --omitall')

    if args.file and not args.file.is_file():
        print_err(f'error, --file {args.file} does not exist')

def lower_search(file_list: Generator,
                 args,
                 checkFirst: int=0,
                 checkLast: int=0)-> list:
    '''Lower start seach is case insensitive'''
    # If positional number value not set, default to all.
    if len(args.start) < 2:
        args.start.append('all')
    try:
        if len(args.end) < 2:
            args.end.append('all')
    except TypeError:
        pass # args.end is not mandatory, returns None when not called, so just pass.
    # If arg.start[1] does not equal 'all'...
    # Change arg.start[1] to int, since it will be a string.
    if args.start[1] != 'all':
        try:
            iter_start = int(args.start[1])
        except ValueError:
            print_err('Incorrect input for -s | --start - only string allowed to be used with start is "all", or integars. Check args')

    # Sense check args.end and ensure 2nd arg is an int
    if args.end and args.end[1] != 'all':
        try:
            iter_end = int(args.end[1])
            if args.start[0] == args.end[0]:
                iter_end += 1
        except ValueError:
            print_err('ValueError: -e / --end only accepts number values')
    start_end: list= []
    # variables from the optional argument of excluding one character
    for line in file_list:
        lower_line = line.casefold()
        lower_str = args.start[0].casefold()
        if args.end:
            lower_end = args.end[0].casefold()
        if lower_str in lower_line:
            try:
                new_str = line
                # Start Arg position and initial string creation.
                if args.start[1] != 'all':
                    init_start = lower_line.index(lower_str)
                    new_str = line[init_start:]
                    new_index = new_str.casefold().index(lower_str)
                    for _ in range(iter_start -1):
                        new_index = new_str.casefold().index(lower_str, new_index + 1)
                    new_str = new_str[new_index:]
                # End Arg positions and final string creation
                if args.end and args.end[1] != 'all':
                    new_index = new_str.casefold().index(lower_end)
                    length_end = len(args.end[0])
                    for _ in range(iter_end -1):
                        new_index = new_str.casefold().index(lower_end, new_index + 1)
                    new_str = new_str[:new_index + length_end]
                start_end.append(new_str[checkFirst:checkLast])
                # ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
                # ValueError will probably occur also if you want an instance number from the start search, which does not exist,
                # so we would want to pass those as well.
            except ValueError:
                pass
    return start_end

def normal_search(file_list: Generator,
                  args,
                  checkFirst: int=0,
                  checkLast: int=0)-> list:
    '''Normal start search, case sensitive'''
    # If positional number value not set, default to all.
    if len(args.start) < 2:
        args.start.append('all')
    try:
        if len(args.end) < 2:
            args.end.append('all')
    except TypeError:
        pass # args.end is not mandatory, returns None when not called, so just pass.
    # If arg.start[1] does not equal 'all'...
    # Change arg.start[1] to int, since it will be a string.
    if args.start[1] != 'all':
        try:
            iter_start = int(args.start[1])
        except ValueError:
            print_err('Incorrect input for -s | --start - only string allowed to be used with start is "all", or integars. Check args')

    # Sense check args.end and ensure 2nd arg is an int
    if args.end and args.end[1] != 'all':
        try:
            iter_end = int(args.end[1])
            if args.start[0] == args.end[0]:
                iter_end += 1
        except ValueError:
            print_err('ValueError: -e / --end only accepts number values or "all"')
    start_end: list= []
    # variables from the optional argument of excluding one character
    for line in file_list:
        if args.start[0] in line:
            try:
                new_str = line
                # Start Arg position and initial string creation.
                if args.start[1] != 'all':
                    init_start = line.index(args.start[0])
                    new_str = line[init_start:]
                    new_index = new_str.index(args.start[0])
                    for _ in range(iter_start -1):
                        new_index = new_str.index(args.start[0], new_index + 1)
                    new_str = new_str[new_index:]
                # End Arg positions and final string creation
                if args.end and args.end[1] != 'all':
                    new_index = new_str.index(args.end[0])
                    length_end = len(args.end[0])
                    for _ in range(iter_end -1):
                        new_index = new_str.index(args.end[0], new_index + 1)
                    new_str = new_str[:new_index + length_end]
                start_end.append(new_str[checkFirst:checkLast])
                # ValueError occurs when the end string does not match, so we want to ignore those lines, hence pass.
                # ValueError will probably occur also if you want an instance number from the start search, which does not exist,
                # so we would want to pass those as well.
            except ValueError:
                pass
    return start_end

def grouped_iter(file_data: Iterable[str],test_reg: re.Pattern, int_list=None):
    temp_list: list = []
    for line in file_data:
        reg_match = test_reg.findall(line)
        if reg_match:
            all_group = ''
            if int_list:
                for i in int_list:
                    all_group = all_group + ' ' + reg_match[0][i-1]
            else:
                for i in reg_match[0]:
                    all_group = all_group + ' ' + i
            temp_list.append(all_group[1:])
    return temp_list

def pygrep_search(args=None, func_search: Iterable[str] = None,
                  pos_val: int=0)-> list:
    '''Python regex search using --pyreg, can be either case sensitive or insensitive'''
    parsed = pygrep_parser(args)
    
    if parsed.pygen_length == 1: # defaults to printing full line if regular expression matches
        for line in func_search:
            reg_match = parsed.test_reg.findall(line)
            if reg_match:
                parsed.pyreg_last_list.append(line)

    elif parsed.pygen_length == 2:
        if args.pyreg[1] == 'all':
            if parsed.group_num > 1:
                parsed.pyreg_last_list = grouped_iter(file_data=func_search, test_reg=parsed.test_reg)
            if parsed.group_num == 1:
                for line in func_search:
                    reg_match = parsed.test_reg.findall(line)
                    if reg_match:
                        parsed.pyreg_last_list.append(reg_match[0])
        elif len(parsed.split_str) == 1:
            try:
                pos_val = int(parsed.split_str[0])
            except ValueError: #valueError due to pos_val being a string
                print_err(f'only string allowed to be used with pyreg is "all", check args {parsed.split_str}')
            for line in func_search:
                reg_match = parsed.test_reg.findall(line)
                if reg_match:
                    try:
                        parsed.pyreg_last_list.append(reg_match[0][pos_val - 1]) if parsed.group_num > 1 else parsed.pyreg_last_list.append(reg_match[pos_val - 1])
                    #indexerror when list exceeds index available
                    except (IndexError):
                        print_err(f'Error. Index chosen {parsed.split_str} is out of range. Check capture groups')
        elif len(parsed.split_str) > 1:
            try:
                # Create an int list for regex match iteration.
                int_list: list[int] = [int(i) for i in parsed.split_str]
            except ValueError: # Value error when incorrect values for args.
                print_err(f'Error. Index chosen {parsed.split_str} are incorrect. Options are "all" or number value, i.e. "1 2 3" ')
            try:
                parsed.pyreg_last_list = grouped_iter(func_search,parsed.test_reg, int_list)
            except IndexError:
                print_err(f'Error. Index chosen {parsed.split_str} is out of range. Check capture groups')

    gc.collect()
    return parsed.pyreg_last_list

def line_func(start_end: list | dict, args)-> tuple:
    ''''Similar idea from using head and tail, requires --line'''

    # args for args.line
    line_num_split = []
    line_num = args.lines[0]
    # Run some tests, set some variables..
    if '-' in line_num:
        line_range = True
        line_num_split = line_num.split('-')
        # If there is only one string in the list, there will be no range, so just output the line, we need get_int to get the int first
        try:
            if not '$' in line_num_split[0]:
                get_int = int(line_num_split[0])
            if not '$' in line_num_split[1]:
                get_int = int(line_num_split[1])
        except ValueError: # Value error if '$' in index
            print_err('error, --line arg examples:\n--line "$-10"\n--line "10-$"\n--line "$"\n--line "1-10"\n--line "10"')    
        # after passing previous try test, extract two number values if they exist
        try:
            num1, num2 = int(line_num_split[0]),int(line_num_split[1])
        except ValueError:
            pass # if this fails, it'll be because one of the indexes is '$'
        if '$' in line_num:
            # Check if range is too high, and return if it is.
            if len(start_end) <= get_int:
                return start_end, line_range
        else:
            # First calculate whether enough lines have been found, and return what we have if not.
            num_diff = max(num1,num2) - min(num1,num2)
            if len(start_end) <= num_diff:
                return start_end, line_range
    else:
        try:
            get_int = int(line_num)
            if len(start_end) < get_int:
                print_err('error, not enough lines in file. Try reducing line numbers')
        except ValueError:
            if line_num != '$':
                print_err('error, --line arg examples:\n--line "$-10"\n--line "10-$"\n--line "$"\n--line "1-10"\n--line "10"')

    # Conditional for lines using the counts arg
    if isinstance(start_end, dict):
        start_end_line = dict()
        if '-' in line_num:
            if '$' in line_num:
                if line_num_split[0] == '$':
                    max_num = int(line_num_split[1])
                    for num, key in enumerate(reversed(start_end), 1):
                        start_end_line[key] = start_end[key]
                        if num >= max_num:
                            return start_end_line, line_range
                elif line_num_split[1] == '$':
                    line_count = len(start_end) - int(line_num_split[0]) + 1
                    for num, key in enumerate(reversed(start_end), 1):
                        start_end_line[key] = start_end[key]
                        if num >= line_count:
                            return start_end_line, line_range
            else:
                line_count = len(start_end) + 1
                low_num = line_count - max(int(line_num_split[0]),int(line_num_split[1]))
                high_num = line_count - min(int(line_num_split[0]),int(line_num_split[1]))                
                for num, key in enumerate(reversed(start_end), 1):
                    if num >= low_num:
                        start_end_line[key] = start_end[key]
                    if num >= high_num:
                        return start_end_line, line_range
        else: # no range
            # if last line
            line_range = False
            if line_num == '$':
                line_count = len(start_end)
                for key in reversed(start_end):
                    start_end_line[key] = start_end[key]
                    return start_end_line, line_range
            else: # specific line
                line_num = int(line_num)
                for num, key in enumerate(start_end, 1):
                    if num == line_num:
                        start_end_line[key] = start_end[key]
                        return start_end_line, line_range
    # For everything else but not including the counts arg.
    start_end_line_list: list = []
    if '-' in line_num:
        if '$' in line_num:
            if line_num_split[0] == '$':
                for rev_count in range(int(line_num_split[1]), 0, -1):
                    start_end_line_list.append(start_end[-rev_count])
            elif line_num_split[1] == '$':
                line_count = len(start_end) - int(line_num_split[0]) + 2
                for rev_count in range(line_count, 0, -1):
                    start_end_line_list.append(start_end[-rev_count])
        else:
            low_num, high_num = min(num1,num2), max(num1,num2)
            for rev_count in range(1, high_num + 1, 1):
                if rev_count >= low_num:
                    start_end_line_list.append(start_end[rev_count - 1])
    else: # no range
        # if last line
        line_range = False
        if line_num == '$':
            start_end_line_list = start_end[-1]
        else:
            line_num = int(line_num)
            start_end_line_list = start_end[line_num - 1]
    return start_end_line_list, line_range

def omit_check(first=None, last=None, args=None)-> tuple:
    '''Omit characters for --start and --end args'''
    if args.omitall:
        try:
            first = len(args.start[0])
            last = - len(args.end[0])
        except TypeError:
            print_err('--start and --end required for omitall, and will automatically reduce by length of word')
        return first, last

    if args.omitfirst and isinstance(args.omitfirst[0], int):
        first = int(args.omitfirst[0])

    if args.omitlast and isinstance(args.omitlast[0], int):
        last = - int(args.omitlast[0])
    return first, last

def counts(count_search: list, args):
    '''Counts the number of times a line is present and outputs a count, uses the --counts arg'''
    from collections import Counter
    pattern_search = Counter(count_search)
    padding = max([len(z) for z in pattern_search]) + 4
    if args.sort:
        pattern_search = dict(pattern_search.most_common()) # type: ignore
            
    def rev_print(pattern_search: dict, padding: int):
        '''Reverse print based on counts'''
        #for key in reversed(pattern_search):
            # print(f'{key:{padding}}Line-Counts = {pattern_search[key]}')
        return [f'{key:{padding}}Line-Counts = {pattern_search[key]}' for key in reversed(pattern_search)]

    if args.lines:
        if args.rev:
            pattern_search = dict(reversed(list(pattern_search.items()))) # type: ignore
        pattern_search, _ = line_func(start_end=pattern_search,
                                            args=args)
        return rev_print(pattern_search = pattern_search, padding = padding)
    else:
        if args.rev:
            return rev_print(pattern_search = pattern_search, padding = padding)
        else:
            # for key in pattern_search:
                # print(f'{key:{padding}}Line-Counts = {pattern_search[key]}')
            return [ f'{key:{padding}}Line-Counts = {pattern_search[key]}' for key in pattern_search]
    # exit(0)

def get_args():
    '''Setting arg parser args'''
    pk = argparse.ArgumentParser(prog='pygrep',description='Search files with keywords, characters or python regex')

    pk.add_argument('-s', '--start',
        help='This is the starting string search -s [keyword|character [position]]',
        type=str,
        required=False,
        nargs='+',
        )

    pk.add_argument('-e', '--end',
        help='end of string search -e [keyword|character [position]]',
        type=str,
        nargs='+',
        required=False)

    pk.add_argument('-f', '--file',
        help='filename to string search through',
        type=Path,
        required=False)

    pk.add_argument('-i', '--insensitive',
        help='This is just a flag for case insensitive for the start flag, no args required, just flag',
        action='store_true',
        required=False)

    pk.add_argument('-of', '--omitfirst',
        help='optional argument for --start. -of [int] - Removes characters from --start (left) side of ouput',
        type=int,
        nargs=1,
        required=False)

    pk.add_argument('-ol', '--omitlast',
        help='optional argument for --end. -ol [int] - Removes characters from --end (right) side of ouput',
        type=int,
        nargs=1,
        required=False)
    
    pk.add_argument('-O', '--omitall',
        help='optional argument for --start & --end. -O [int] - Removes characters from --start & --end of ouput',
        action='store_true',
        required=False)

    pk.add_argument('-p', '--pyreg',
        metavar="[regex [numerical value|all]]",
        help='python regular expression, use with -p "regex" or follow up with a numerical value for a capture group',
        type=str,
        nargs='+',
        required=False)

    pk.add_argument('-l', '--lines',
        metavar="'1-10' | '1' | '$-3'",
        help='optional argument to display specific lines, example= ./pygrep.py -s search -l \'$-2\' for last 2 lines. -l \'1-3\' for first 3 lines. -l 6 for the 6th line',
        type=str,
        nargs=1,
        default=None,
        required=False)

    pk.add_argument('-S', '--sort',
        help='Can be used standalone for normal sort, or combined with --rev for reverse',
        action='store_true',
        required=False)
    
    pk.add_argument('-r', '--rev',
        help='Can be used standalone or with --sort',
        action='store_true',
        required=False)
    
    pk.add_argument('-u', '--unique',
        help='This is just a flag for unique matches no args required, just flag',
        action='store_true',
        required=False)

    pk.add_argument('-c', '--counts',
        help='This is just a flag for counting matches no args required, just flag',
        action='store_true',
        required=False)

    pk.add_argument('-m', '--multi',
        help="optional argument to for multi processing example= ./pygrep.py -p search -m 4 -f file for 4 threads",
        nargs=1,
        type=int,
        required=False
        )
    
    # our variables args parses the function (argparse)
    args = pk.parse_args()

    return args

class PythonArgs:
    '''
    Class purely for parsing using python and portability.
    '''
    
    def __init__(self, **kwargs) -> None:

        self.start: str | list = kwargs.get('start')
        self.end: str | list = kwargs.get('end')
        self.insensitive: bool = kwargs.get('insensitive', False)

        # Omitfirst and Omitlast need list conditions for compatibility with the commandline syntax.
        # And I would rather not pass a omitfirst=list[int] for PythonArgs
        # And I would rather not enclose the False syntax in a list.
        # The reason for bool, is to make sure comparisons are made in sense check, instead of a list of None.
        self.omitfirst: list[int] | bool = [ kwargs.get('omitfirst', False) ] if kwargs.get('omitfirst', False) != False else False
        self.omitlast: list[int] | bool = [ kwargs.get('omitlast', False) ] if kwargs.get('omitlast', False) != False else False
        
        self.omitall: bool = kwargs.get('omitall', False)
        self.lines: list[str] =  [ kwargs.get('lines') ]
        self.sort: bool = kwargs.get('sort', False)
        self.rev: bool = kwargs.get('rev', False)
        self.unique: bool = kwargs.get('unique', False)
        self.counts: bool = kwargs.get('counts', False)
        self.pyreg: str | list = kwargs.get('pyreg')
        self.file: Path = Path(kwargs.get('file')) # type: ignore
        self.multi: int = kwargs.get('multi' )


def chunked_file_reader(chunk_size: int, file_path: str = None, stdin: sys.stdin = None) -> Iterable[list[str]]: # multi threaded
    '''Yields chunks of lines from a file or stdin'''
    chunk = []
    try:
        source = open(file_path, 'r') if file_path else stdin
        if not source:
            print_err('Input Error: Either file_path or stdin must be provided')
        for line in source:
            chunk.append(line.strip())
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk
    finally:
        if file_path:
            source.close()


def mmap_reader(file_path: str, regex_pattern: str, criteria: Literal['line', 'match'], insensitive: bool = False): # single threaded

    with open(file_path, 'rb', buffering=0) as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            # Compile the regular expression pattern
            pattern = re.compile(regex_pattern.encode('utf-8'), re.IGNORECASE) if insensitive else re.compile(regex_pattern.encode('utf-8'))
            # Search using the pattern, yielding match objects
            match criteria:
                case 'line':
                    for match in pattern.finditer(mm):
                        start = max(0, mm.rfind(b'\n', 0, match.start())+1)
                        end = mm.find(b'\n', match.end())
                        if end == -1:
                            end = len(mm)  # Handle case where the match is in the last line
                        # Append the whole line as a decoded string
                        yield mm[start:end].decode('utf-8')
                case 'match':
                    for match in pattern.finditer(mm):
                        yield match.groups()
                
                case _:
                    print_err('Internal error with criteria matching')

@dataclass
class ParserPyReg:
    test_reg: re.Pattern
    pygen_length: int
    group_num: int
    split_str: list = field(default_factory=list)
    pyreg_last_list: list = field(default_factory=list)

def pygrep_parser(args):

    test_reg: re.Pattern = re.compile(args.pyreg[0], re.IGNORECASE) if args.insensitive else re.compile(args.pyreg[0])
    # Splitting the arg for capture groups into a list
    try:
        split_str: list = args.pyreg[1].split(' ')
    # IndexError occurs when entire lines are required
    except IndexError:
        split_str = []

    return ParserPyReg(
        test_reg = test_reg,
        split_str = split_str,
        pygen_length = len(args.pyreg),
        group_num = test_reg.groups,
        pyreg_last_list = []
    )

class ReaderArgs(TypedDict):
    file_path: str
    regex_pattern: str
    criteria: Literal['line', 'match']
    insensitive: bool = False

def reader_args_parser(file_path, args):
    return ReaderArgs(
        file_path=file_path,
        regex_pattern=args.pyreg[0],
        criteria='match',
        insensitive=args.insensitive
    )


def pygrep_mmap(args, file_path, pos_val): # single threaded
    '''Python regex search using --pyreg, can be either case sensitive or insensitive'''
    parsed = pygrep_parser(args)
    reader_args: ReaderArgs = reader_args_parser(file_path, args)

    match parsed.pygen_length:
        case 1: # defaults to printing full line if regular expression matches
            reader_args['criteria'] = 'line'
            for line in mmap_reader(**reader_args):
                parsed.pyreg_last_list.append(line)
        case 2:
            if args.pyreg[1] == 'all':
                if parsed.group_num > 1:
                    for line in mmap_reader(**reader_args):
                        all_group: str = ''
                        for i in line:
                            all_group = all_group + ' ' + i.decode()
                        parsed.pyreg_last_list.append(all_group[1:])
                if parsed.group_num == 1:
                    for line in mmap_reader(**reader_args):
                        parsed.pyreg_last_list.append(line[0].decode())
            elif len(parsed.split_str) == 1:
                try:
                    pos_val = int(parsed.split_str[0])
                except ValueError: #valueError due to pos_val being a string
                    print_err(f'only string allowed to be used with pyreg is "all", check args {parsed.split_str}')
                for line in mmap_reader(**reader_args):
                    try:
                        parsed.pyreg_last_list.append(line[pos_val-1].decode())
                    #indexerror when list exceeds index available
                    except (IndexError):
                        print_err(f'Error. Index chosen {parsed.split_str} is out of range. Check capture groups')
            elif len(parsed.split_str) > 1:
                try:
                    # Create an int list for regex match iteration.
                    int_list: list[int] = [int(i) for i in parsed.split_str]
                except ValueError: # Value error when incorrect values for args.
                    print_err(f'Error. Index chosen {parsed.split_str} are incorrect. Options are "all" or number value, i.e. "1 2 3" ')
                for line in mmap_reader(**reader_args):
                    all_group = ''
                    try:
                        for i in int_list:
                            all_group = all_group + ' ' + line[i - 1].decode()
                        parsed.pyreg_last_list.append(all_group[1:])
                    # Indexerror due to incorrect index
                    except IndexError:
                        print_err(f'Error. Index chosen {parsed.split_str} is out of range. Check capture groups')

    gc.collect()
    return parsed.pyreg_last_list


###########################

def unified_input_reader(file_path: str = None) -> Iterable[str]:
    '''Reads lines from a file or stdin'''
    if file_path:
        with open(file_path, 'r') as file:
            for line in file:
                yield line.strip()
    else:
        if not sys.stdin.isatty():
            for line in sys.stdin:
                yield line.strip()


def multi_cpu(pos_val, args, n_cores=cpu_count(), file_path: str = None)-> Iterable:
    '''
    Accepts file_path, pos_val, args, and n_cores (default is system max cores)
    Only supported with python regex, where multiprocessing above 15 seconds in duration will see a benefit.
    '''

    global worker
    def worker(line_list):
        return pygrep_search(args=args, func_search=line_list, pos_val=pos_val)

    # chunk_size = n_cores * 1000
    chunk_size = 10000
    reader_args: dict = {
        'chunk_size': chunk_size,
        'file_path': file_path if file_path and Path(file_path).exists() else None,
        'stdin': sys.stdin if not sys.stdin.isatty() else None
        }
    
    with ProcessPoolExecutor(max_workers=n_cores) as executor:
        result = executor.map(worker, chunked_file_reader(**reader_args))
        gc.collect()  # Explicitly trigger garbage collection to manage memory

    for sublist in result:
        for r in sublist:
            yield r


def main_seq(python_args_bool=False, args=None):
    '''main sequence for arguments to run'''
    
    if python_args_bool is False:
        args = get_args()

    sense_check(args=args, argTty=sys.stdin.isatty())

    # Initial case-insensitivity check
    checkFirst, checkLast = omit_check(args=args)
    if args.start:
        # Getting input from file or piped input
        if args.file and Path(args.file).exists():
            file_list = unified_input_reader(args.file)
        elif not sys.stdin.isatty(): # for using piped std input. 
            file_list = unified_input_reader()
        else:
            print_err('Input not recognised, check file path or stdin')

        # check for case-insensitive & initial 'start' search
        if args.insensitive == False:
            pattern_search = normal_search(file_list=file_list,args=args,
                                                    checkFirst=checkFirst,
                                                    checkLast=checkLast)
        else:               
            pattern_search = lower_search(file_list=file_list,args=args,
                                          checkFirst=checkFirst,
                                          checkLast=checkLast)
    # python regex search
    if args.pyreg:
        try:
            pos_val = args.pyreg[1]
        except IndexError: # only if no group arg is added on commandline
            pos_val = 0
        if args.start:
            file_list = pattern_search
        if args.multi:
            pattern_search = multi_cpu(args=args, file_path=args.file, pos_val=pos_val, n_cores=int(args.multi[0]))
            gc.collect()
        else:
            # pattern_search = pygrep_search(args=args, func_search=file_list, pos_val=pos_val)
            pattern_search = pygrep_mmap(args=args, file_path=args.file, pos_val=pos_val)
            gc.collect()
        
        # pattern_search = pygrep_search(args=args, func_search=file_list, pos_val=pos_val)
    if not pattern_search:
        print('No Pattern Found')
        exit(0)
    # unique search
    if args.unique:
        pattern_search = list(dict.fromkeys(pattern_search))
    # sort search
    if args.counts != True and args.sort:
        test_re = re.compile(r'^[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}$')
        test_ip = test_re.findall(pattern_search[0])
        if args.sort:

        #match args.sort:
        #    case None:
            if test_ip:
                import ipaddress
                pattern_search.sort(key=ipaddress.IPv4Address)
            else:
                pattern_search.sort()
        #    case 'r':
        if args.rev:
            if test_ip:
                import ipaddress
                pattern_search.sort(key=ipaddress.IPv4Address, reverse=True)
            else:
                pattern_search.sort(reverse=True)
            # case _:
            #     print_err('--sort / -S can only take r as an arg, or standalone, \nFor Example:\n-Sr or -S')
    # counts search
    if args.counts:
        return counts(count_search = pattern_search, args=args)
    # lines search
    if args.lines:
        pattern_search, line_range = line_func(start_end=pattern_search, args=args)
        if line_range == True: # multiline
            # [print(i) for i in pattern_search]
            return [i for i in pattern_search]
        else: # This prevents a single string from being separated into lines.
        #    print(pattern_search)
            return pattern_search
    else:
        # [print(i) for i in pattern_search]
        return pattern_search
    
# Run main sequence if name == main.
if __name__ == '__main__':

    # Experimental
    # args = PythonArgs(#pyreg=['\w+\s+DST=(123.12.123.12)\s+\w+', '1'],
    #                     start=['SRC=', 1],
    #                     end=[' DST', 1],
    #                     file='ufw.test',
    #                     lines='1-10',
    #                     # counts=True,
    #                     # sort=True,
    #                     # rev=True,
    #                     # omitfirst=2,
    #                     # omitlast=5,
    #                     omitall=True
    #                     )
    # main_seq(python_args_bool=True, args=args)
    #return_main = main_seq()
    for i in main_seq():
        print(i) 
