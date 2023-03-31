# pygrep
## Python string and regex search

## The Why?

Well, I think tools like grep, sed and awk, tail, head are amazing, but thought i’d write something that does a bit of all of them.

This will be under development as i think of new things to add, and optimize the code.

## Info

Tested on Python 3.10.6 for the most part on Ubuntu22.04, very little testing has taken place on other versions.

After seeking some feedback on pygrep, pygrep might not be the right tool for every job, but what is? Anyway, I have some performance stats at the bottom of the page.

## Basic Rules

* Required args are at least --start or --pyreg otherwise the programme won't do anything
* Requires input from --file or if using piped input from another command.
* When using --start with --pyreg, the --start function runs first, and then further filtering takes place using --pyreg.
* --start and --end takes place before --pyreg when used with --pyreg.
* --pyreg doesn't use --end
* --omitlast requires --end
* --omitfirst requires --start

## String Searches
Basic string searches using -s | --start and -e | --end
* -s | --start can be used standlone (without --pyreg) or with --pyreg for some extra filtering. This uses a starting string/word/character on a line, and can take an optional number value or 'all' (default is all if excluded). The number value will switch to a different index in the line. For example.. if you require the 2nd position of string/word/character in the line, you would simply follow with the number 2. 
```./pygrep.py --start string 2 -f filename ```
* -e | --end is optional and provides an end to the line you are searching for. Say for instance you only want a string which is enclosed in brackets 
```./pygrep.py --start \( 1 --end \) 1 -f filename ``` This would select the 1st end character found. For now --end takes 2 arguments. The character/string/word followed by a numerical value.
* -of | --omitfirst is optional for deleting the first characters of your match. For instance, using the above example, you might want something enclosed in brackets, but without the brackets. ``` ./pygrep.py --start cron 1 -of -f /var/log/syslog ``` (default without specifying a number of characters to omit, will remove the characters in --start from the output, otherwise use an integar for the number of characters) 
* -ol | --omitlast is optional and same use as --omitfirst. This would default to number of characters in the --end arg, unless a number value is included.
* -un | --unique is optional, and will output unique entries only.
* -so | --sort is optional, and will output in sorted order.. no reverse order currently available... will be planned in.
* -l | --lines is optional and to save piping using tail, head or sed. Examples are easier to understand and syntax easy. You can select a range of lines, i.e. '5-10' last 3 lines '$-3' a single line '5', last line '$', line 5 to end '5-$'
```
./pygrep.py --start string -l '$' -f filename # last line
./pygrep.py --start string -l '1-5' -f filename # first 5 lines
```
* -i | --insensitive is optional and whether you want case sensitive searched. No further agrs required.
* -c / --counts is an optional arg which summarises the number of unique lines identified. Works standalone without unique.

## Python Regex

I recommend having a read of the python docs for some helpful regular expression used by python. Just enclose the regex in this programme in single quotes to pass the regex to the pygrep.py.

https://docs.python.org/3/library/re.html

* -p | --pyreg can be used standlone (without --start) or with --start for some extra filtering. Up to 2 arguments, one for the regex and the other is for whether you want positional values on the regex using groups - this arg is a number value. Instead of the number value, you could use the keyword 'all', which will show all groups you've enclosed in brackets. The default without any 2nd argument is to print the line.
```bash
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=(123.12.123.12)' 1 -i -l 1 -f ufw.test

# This is using python regex. \d is for numerical value, + is more than 1.
# the first group in this example is the ip address of the SRC. The second 
# group is the ip address for DST. I've followed the regex with a number 
# value of 1, which will display the ip address in group 1 (enclosed in 
# brackets). Also in this example, i've included case insensitive with -i 
# and also asked for only the first line with -l 1.
```

 ## Examples

 Run script with...
 ```bash
./pygrep.py -s [keyword/character [position]] [-p regex [position|all]] [-e keyword/character position] [-i] [-l int|$|$-int|int-int] [-of int|=start] [-ol int|=end] [--unique] [--sort] [-f /path/to/file]

 -s can be run with position being equal to all, to capture the start of the line, this is default if no position provided
 
 ./pygrep.py -s root all -f /etc/passwd                                         ## output: root:x:0:0::/root:/bin/bash
 ./pygrep.py -s root 1 -e \: 4 -f /etc/passwd                                   ## output: root:x:0:0:
 ./pygrep.py -s CRON 1 -e \) 2 -f /var/log/syslog                               ## Output: CRON[108490]: (root) CMD (command -v debian-sa1 > /dev/null && debian-sa1 1 1)
 ./pygrep.py -s jonny 2 -f /etc/passwd                                          ## output: jonny:/bin/bash

 without -ol -of (only works with --start & --end, not --pyreg)
 ./pygrep.py -s \( 1 -e \) 1 -f testfile                                        ## output: (2nd line, 1st bracket)
 with -ol -of (only works with --start & --end, not --pyreg)
 ./pygrep.py -s \( 1 -e \) 1 -ol -of -f testfile                            ## output: 2nd line, 1st bracket
 ./pygrep.py -s 'SRC=' 1 -e 'DST=' 1 -of -ol -f /var/log/ufw.log    ## output: 123.123.123.123 (ip address from ufw.log between SRC= and DST=)

OR -O for --omitall...
./pygrep.py -s 'SRC=' 1 -e 'DST=' 1 -O -f /var/log/ufw.log    ## output: 123.123.123.123 (ip address from ufw.log between SRC= and DST=)

-p or --pyreg | I recommend consulting the python documentation for python regex using re.
 
 with -s (--start) & -p (--pyreg)
 ./pygrep.py -s Feb -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test

 with --pyreg (-p)
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -f ufw.test
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=(123.12.123.12)' all -f ufw.test =>  because SRC and DST are in 2 groups using (), all will show both groups
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=(123.12.123.12)' 1 -f ufw.test => This will show the SRC ip enclosed () as the first group
./pygrep.py -p 'SRC=([\d\.]+)\s+DST=123.12.123.12' 1 -f ufw.test => Shorthand version enclosing [\d\.]+ in square brackets.

with -i (--insensitive) = case insensitive, this doesn't require much, just needs to be included if required. Works with --start and --pyreg
./pygrep.py -p 'src=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -f ufw.test

with --lines (-l) Note: $ is an end of line character. Enclose in single quotes ''
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -l '$-4' -f ufw.test => last 4 lines
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -l '$' -f ufw.test => last line
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -l '1-4' -f ufw.test => lines 1-4
./pygrep.py -p 'SRC=(\d+\.\d+\.\d+\.\d+)\s+DST=123.12.123.12' -i -l 1 -f ufw.test => first line

Still testing --counts. Still Experimental.
./pygrep.py -p 'SRC=([\d\.]+)\s+DST' 1 -c -f /var/log/ufw.log
./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -c -f ufw.test
```

## Performance stats

Ok, I felt the need to include this, so here goes. After some performance tweaking with pygrep, i've been able to find an example where pygrep is faster than grep, sed, and ripgrep, and that's when you are expecting a lot of output from a log file etc. This example uses UFW, i find UFW logs an easy example to practice some regex on.
I am heavily focused on the capture group performance and output, so i've left grep out of this for now.


```bash
jonny@jp-vivo:~/git/pygrep$ time pygrep -s 'SRC=' 1 -e ' DST' 1 -O -f ufw.test1 | wc -l
11129400

real	0m14.109s
user	0m12.350s
sys	0m1.945s

jonny@jp-vivo:~/git/pygrep$ time pygrep -p 'SRC=([\d\.]+)\s+DST' 1 -f ufw.test1 | wc -l
11129400

real	0m11.568s
user	0m10.135s
sys	0m1.584s

jonny@jp-vivo:~/git/pygrep$ time rg -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -r '$1' | wc -l
11129400

real	0m18.704s
user	0m18.747s
sys	0m0.299s

jonny@jp-vivo:~/git/pygrep$ time time sed -En 's/.*SRC=([0-9\.]+)\s+DST.*/\1/p' ufw.test1 | wc -l
11129400

real	3m41.461s
user	3m41.182s
sys	0m0.806s
```

This is an 11 million line UFW log.
Ok, now for less output with the same log file.

```bash
jonny@jp-vivo:~/git/pygrep$ time pygrep -p 'DST=(124.14.124.14)' 1 -f ufw.test1 (ok, this is a literal, but to show it depends on the regex)
124.14.124.14

real	0m4.913s
user	0m3.684s
sys	0m1.228s

jonny@jp-vivo:~/git/pygrep$ time pygrep -p '\s+DST=(124.14.124.14)' 1 -f ufw.test1 (\s+ for regex)
124.14.124.14

real	0m38.723s
user	0m37.492s
sys	0m1.229s

jonny@jp-vivo:~/git/pygrep$ time rg -No '\s+DST=(124.14.124.14)' -r '$1' ufw.test1
124.14.124.14

real	0m4.610s
user	0m4.525s
sys	0m0.084s

jonny@jp-vivo:~/git/pygrep$ time sed -En 's/.*\s+DST=(124.14.124.14).*/\1/p' ufw.test1
124.14.124.14

real	0m4.514s
user	0m4.166s
sys	0m0.348s

```

So as you can see, when the regex is less favourable and there's less output pygrep would not be the best tool.

Ok now for lots of output and a little harsher regex (I could be a bit more aggresive with the regex, but this slow down works)

```bash
jonny@jp-vivo:~/git/pygrep$ time pygrep -p '\s+DST=(123.12.123.12)' 1 -f ufw.test1 | wc -l
11129399

real	0m33.434s
user	0m32.360s
sys	0m1.189s

jonny@jp-vivo:~/git/pygrep$ time rg -No '\s+DST=(123.12.123.12)' -r '$1' ufw.test1 | wc -l
11129399

real	0m24.041s
user	0m24.043s
sys	0m0.174s

jonny@jp-vivo:~/git/pygrep$ time sed -En 's/.*\s+DST=(123.12.123.12).*/\1/p' ufw.test1 | wc -l
11129399

real	4m2.065s
user	4m1.786s
sys	0m0.663s

```
Some less favourable regex using a leading \s+, but requiring a lot of output makes things a little messy for all. 

Any personal use log files of around 100,000 lines will not break much of a sweat for any of the above, but I just wanted to throw together some benchmarks so everyone see's any strengths and weaknesses in terms of performance. Each programme has it's own perks and quite different in their own right.
