# pygrep
## Python string and regex search

## The Why?

Well, I think tools like grep, sed and awk, tail, head are amazing, but thought i’d write something that does a bit of all of them.

This will be under development as i think of new things to add, and optimize the code.

## Info

Tested on Python 3.10.6 for the most part on Ubuntu22.04, very little testing has taken place on other versions.

After seeking some feedback on pygrep, pygrep might not be the right tool for every job, but what is? Anyway, I have some performance stats at the bottom of the page.

## Features I'd like to add or improve

* improve docstrings
* debug to the point where I feel I can create a stable branch
* modular for other python packages

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
```./pygrep.py --start \( 1 --end \) 1 -f filename ``` This would select the 1st end character found. For now --end takes 2 arguments. The character/string/word followed by a numerical value would end the string at that index. IF no numerical value provided, the string will output to end of the line.

* -of | --omitfirst is optional for deleting the first characters of your match. For instance, using the above example, you might want something enclosed in brackets, but without the brackets. ``` ./pygrep.py --start cron 1 -of -f /var/log/syslog ``` (default without specifying a number of characters to omit, will remove the characters in --start from the output, otherwise use an integar for the number of characters) 

* -ol | --omitlast is optional and same use as --omitfirst. This would default to number of characters in the --end arg, unless a number value is included.

* -O | --omitall is optional and combines both -of and -ol.

* -u | --unique is optional, and will output unique entries only.

* -S | --sort is optional, and will output in sorted order. When used with --counts, it sorts by count value. Now includes an 'r' flag to reverse output, i.e. -Sr.

* -l | --lines is optional and to save piping using tail, head or sed. Examples are easier to understand and syntax easy. You can select a range of lines, i.e. '5-10' last 3 lines '$-3' a single line '5', last line '$', line 5 to end '5-$'
```
./pygrep.py --start string -l '$' -f filename # last line
./pygrep.py --start string -l '1-5' -f filename # first 5 lines
```

* -i | --insensitive is optional and whether you want case sensitive searched. No further agrs required.

* -c / --counts is an optional arg which summarises the number of unique lines identified. Works standalone without unique and with --start , --pyreg


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

With --counts.
./pygrep.py -p 'SRC=([\d\.]+)\s+DST' 1 -c -f /var/log/ufw.log
./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -c -f ufw.test
```

## Performance stats

Ok, I felt the need to include this, so here goes. After some performance tweaking with pygrep, i've been able to find an example where pygrep is faster than grep, sed, and ripgrep, and that's when you are expecting a lot of output from a log file etc. This example uses UFW, i find UFW logs an easy example to practice some regex on.
I am heavily focused on the capture group performance and output, so i've left grep out of this for now.

_Updated: 16/04/2023_

```bash
jonny@jp-vivo:~/git/pygrep$ time ./pygrep.py -s 'SRC=' 1 -e ' DST' 1 -O -f ufw.test1 | wc -l
11129400

real	0m12.063s
user	0m10.977s
sys	0m1.202s

jonny@jp-vivo:~/git/pygrep$ time ./pygrep.py -p 'SRC=([\d\.]+)\s+DST' all -f ufw.test1 | wc -l # Since theres only one capture group, the all arg outputs the one capture group more quickly.
11129400

real	0m8.301s
user	0m7.335s
sys	0m1.120s

jonny@jp-vivo:~/git/pygrep$ time ./pygrep.py -p 'SRC=([\d\.]+)\s+DST' 1 -f ufw.test1 | wc -l
11129400

real	0m8.796s
user	0m7.421s
sys	0m1.541s


jonny@jp-vivo:~/git/pygrep$ time rg -No 'SRC=([\d\.]+)\s+DST' ufw.test1 -r '$1' | wc -l
11129400

real	0m18.704s
user	0m18.747s
sys	0m0.299s

jonny@jp-vivo:~/git/pygrep$ time sed -En 's/.*SRC=([0-9\.]+)\s+DST.*/\1/p' ufw.test1 | wc -l
11129400

real	3m40.930s
user	3m40.804s
sys	0m0.601s

# EDIT: Late entry from my desktop, similar spec vs my laptop
jonny@uby-umc:~/git/pygrep$ time gawk 'match($0, /SRC=([0-9\.]+)\s+DST/, ipmatch){print ipmatch[1] }' ufw.test1 | wc -l
11129400

real	0m42.857s
user	0m42.634s
sys	0m0.442s

```

This is an 11 million line UFW log.
Ok, now for less output with the same log file and a leading \s+.

```bash
#(ok, this is a literal, but to show it depends on the regex)
jonny@jp-vivo:~/git/pygrep$ time ./pygrep.py -p ' DST=(124\.14\.124\.14)' 1 -f ufw.test1
124.14.124.14

real	0m4.120s
user	0m3.248s
sys	0m0.872s

#(\s+ for adding in a left hand side opened ended regex)
jonny@jp-vivo:~/git/pygrep$ time pygrep -p '\s+DST=(124.14.124.14)' 1 -f ufw.test1 
124.14.124.14

real	0m27.946s
user	0m26.973s
sys	0m0.972s

# Using --start, --end and -of we get a speedup, since it's mostly literals we're searching for.
jonny@jp-vivo:~/git/pygrep$ time ./pygrep.py -s ' DST=' 1 -e '124.14.124.14' 1 -of -f ufw.test1
124.14.124.14

real	0m10.249s
user	0m9.321s
sys	0m0.928s

jonny@jp-vivo:~/git/pygrep$ time rg -No '\s+DST=(124.14.124.14)' -r '$1' ufw.test1
124.14.124.14

real	0m5.629s
user	0m5.557s
sys	0m0.072s

# I know ripgrep has a -F strings only, but this removes capture groups,
# but fear not, simple escaping the period gives us....
jonny@jp-vivo:~/git/pygrep$ time rg -No ' DST=(124\.14\.124\.14)' -r '$1' ufw.test1
124.14.124.14

real	0m0.233s
user	0m0.169s
sys	0m0.065s

jonny@jp-vivo:~/git/pygrep$ time sed -En 's/.*\s+DST=(124.14.124.14).*/\1/p' ufw.test1
124.14.124.14

real	0m4.514s
user	0m4.166s
sys	0m0.348s

# sed with escaped periods doesn't make any difference.
jonny@jp-vivo:~/git/pygrep$ time sed -En 's/.*\s+DST=(124\.14\.124\.14).*/\1/p' ufw.test1
124.14.124.14

real	0m4.629s
user	0m4.301s
sys	0m0.328s

```

So as you can see, when the regex is less favourable and there's less output pygrep would not be the best tool.

Ok now for lots of output with the same harshness of regex (I could be a bit more aggresive with the regex, but this slow down works)

```bash
jonny@jp-vivo:~/git/pygrep$ time pygrep -p '\s+DST=(123.12.123.12)' 1 -f ufw.test1 | wc -l
11129399

real	0m31.644s
user	0m30.622s
sys	0m1.136s

# using 'all' in this instance doesn't have too big an impact.
jonny@jp-vivo:~/git/pygrep$ time pygrep -p '\s+DST=(123.12.123.12)' all -f ufw.test1 | wc -l 
11129399

real	0m30.355s
user	0m29.272s
sys	0m1.197s

# escaping the periods and removing the \s+ better performance.
jonny@uby-umc:~/git/pygrep$ time ./pygrep.py -p ' DST=(123\.12\.123\.12)' all -f ufw.test1 | wc -l
11129399

real	0m8.159s
user	0m7.140s
sys	0m1.142s

# another option for literals using --start and --end and -of, helps with a speedup
jonny@jp-vivo:~/git/pygrep$ time ./pygrep.py -s ' DST=' 1 -e '123.12.123.12' -1 -of -f ufw.test1 | wc -l
11129399

real	0m12.304s
user	0m11.282s
sys	0m1.138s


jonny@jp-vivo:~/git/pygrep$ time rg -No '\s+DST=(123.12.123.12)' -r '$1' ufw.test1 | wc -l
11129399

real	0m24.041s
user	0m24.043s
sys	0m0.174s

# small performance boost escaping the periods.
jonny@jp-vivo:~/git/pygrep$ time rg -No '\s+DST=(123\.12\.123\.12)' -r '$1' ufw.test1 | wc -l
11129399

real	0m18.421s
user	0m18.415s
sys	0m0.147s

# further improvement removing the \s+ and adding the space character.
jonny@jp-vivo:~/git/pygrep$ time rg -No ' DST=(123\.12\.123\.12)' -r '$1' ufw.test1 | wc -l
11129399

real	0m13.141s
user	0m13.086s
sys	0m0.188s

jonny@jp-vivo:~/git/pygrep$ time sed -En 's/.*\s+DST=(123.12.123.12).*/\1/p' ufw.test1 | wc -l
11129399

real	4m2.065s
user	4m1.786s
sys	0m0.663s

```
Some less favourable regex using a leading \s+, but requiring a lot of output makes things a little messy for all. 

Ok now for no capture groups, just literals

```bash
jonny@jp-vivo:~/git/pygrep$ time pygrep -p '124\.14\.124\.14' -f ufw.test1
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=12345 DPT=33333 WINDOW=1024 RES=0x00 SYN URGP=0

real	0m4.533s
user	0m3.684s
sys	0m0.848s

jonny@jp-vivo:~/git/pygrep$ time rg '124\.14\.124\.14' ufw.test1
25:Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=12345 DPT=33333 WINDOW=1024 RES=0x00 SYN URGP=0

real	0m0.437s
user	0m0.259s
sys	0m0.179s

jonny@jp-vivo:~/git/pygrep$ time grep '124\.14\.124\.14' ufw.test1
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=12345 DPT=33333 WINDOW=1024 RES=0x00 SYN URGP=0

real	0m1.043s
user	0m0.657s
sys	0m0.385s

jonny@jp-vivo:~/git/pygrep$ time sed -n '/124\.14\.124\.14/p' ufw.test1
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=12345 DPT=33333 WINDOW=1024 RES=0x00 SYN URGP=0

real	0m2.349s
user	0m1.825s
sys	0m0.525s

jonny@jp-vivo:~/git/pygrep$ time pygrep -s '124.14.124.14' -f ufw.test1 #(for a literal line like this --start works a bit faster than --pyreg)
Feb 19 10:39:46 proxy kernel: [852160.927134] [UFW BLOCK] IN=eth0 OUT= MAC=f2:3c:93:1c:e2:44:00:00:0c:9f:f0:01:08:00 SRC=79.124.59.134 DST=124.14.124.14 LEN=40 TOS=0x00 PREC=0x00 TTL=245 ID=47185 PROTO=TCP SPT=12345 DPT=33333 WINDOW=1024 RES=0x00 SYN URGP=0

real	0m3.209s
user	0m2.313s
sys	0m0.896s

```

Lastly ripgrep pulls ahead on a more killer regex capture group which also would output a lot of data. I feel bad for sed here, it's got a much worse regex to single out the capture group, so at the bottom i've put ripgrep and pygrep through the same torture test...

```bash
jonny@jp-vivo:~/git/pygrep$ time pygrep -p '\w+\s+DST=(123.12.123.12)\s+\w+' 1 -f ufw.test1 | wc -l
11129399

real	1m40.939s
user	1m39.772s
sys	0m1.280s
jonny@jp-vivo:~/git/pygrep$ time rg -No '\w+\s+DST=(123.12.123.12)\s+\w+' -r '$1' ufw.test1 | wc -l
11129399

real	0m29.853s
user	0m29.798s
sys	0m0.303s
jonny@jp-vivo:~/git/pygrep$ time sed -En 's/.*\w+\s+DST=(123.12.123.12)\s+\w+.*/\1/p' ufw.test1 | wc -l
11129399

real	5m16.777s
user	5m16.396s
sys	0m0.769s


#########################################################################################################

# To be fair on sed, the same torture regex, but you wouldn't do this in the real world (just a bit of fun)...

jonny@jp-vivo:~/git/pygrep$ time rg -No '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' -r '$1' ufw.test1 | wc -l
11129399

real	3m50.565s
user	3m50.464s
sys	0m0.468s

# I ran the result above twice, and this was the better of the two results.

# But somehow pygrep decided to take on this challenge with an unexpected result, surprised it was faster than without .* at each end. 

jonny@jp-vivo:~/git/pygrep$ time pygrep -p '.*\w+\s+DST=(123.12.123.12)\s+\w+.*' 1 -f ufw.test1 | wc -l
11129399

real	1m5.473s
user	1m4.439s
sys	0m1.148s

------------------------------------------------------------------------------------------------------------

# So following on from the .*, I thought i would try excluding the \w+\s+ and roll with .*

jonny@jp-vivo:~/git/pygrep$ time rg -No '.*DST=(123.12.123.12).*' -r '$1' ufw.test1 | wc -l
11129399

real	2m49.839s
user	2m49.834s
sys	0m0.373s

jonny@jp-vivo:~/git/pygrep$ time pygrep -p '.*DST=(123.12.123.12).*' 1 -f ufw.test1 | wc -l
11129399

real	0m11.793s
user	0m10.381s
sys	0m1.559s

# Python regex engine seems to work well with wildcards like .* (Never knew that until i started testing, interesting!!)

#Edit: The wildcard .* at either end does help python regex a lot in this scenario.

jonny@uby-umc:~/git/pygrep$ time pygrep -p '.*\s+DST=([\d\.]+).*' 1 -f ufw.test1 | wc -l
11129400

real	0m27.197s
user	0m26.173s
sys	0m1.150s

# Without

jonny@uby-umc:~/git/pygrep$ time pygrep -p '\s+DST=([\d\.]+)' 1 -f ufw.test1 | wc -l
11129400

real	0m34.948s
user	0m33.883s
sys	0m1.179s

jonny@uby-umc:~/git/pygrep$ time pygrep -p '.*\s+DST=([\d\.]+).*' all -f ufw.test1 | wc -l # small speed boost with all.
11129400

real	0m24.810s
user	0m23.769s
sys	0m1.162s

jonny@uby-umc:~/git/pygrep$ time rg -No '\s+DST=([\d\.]+)' -r '$1' ufw.test1 | wc -l
11129400

real	0m25.892s
user	0m25.799s
sys	0m0.237s

# A not too unrealistic regex search looking for source IP and Source Port.

jonny@jp-vivo:~/git/pygrep$ time rg -No 'SRC=([\d\.]+).*SPT=([\d\.]+)' -r '$1 $2' ufw.test1 | wc -l
11129400

real	1m14.487s
user	1m14.529s
sys	0m0.288s

jonny@jp-vivo:~/git/pygrep$ time ./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' '1 2' -f ufw.test1 | wc -l
11129400

real	0m12.688s
user	0m11.225s
sys	0m1.592s

jonny@jp-vivo:~/git/pygrep$ time ./pygrep.py -p 'SRC=([\d\.]+).*SPT=([\d\.]+)' 'all' -f ufw.test1 | wc -l # small improvement with all.
11129400

real	0m11.667s
user	0m10.236s
sys	0m1.568s

```

Any personal use log files of around 100,000 lines will not break much of a sweat for any of the above, but I just wanted to throw together some benchmarks so everyone see's any strengths and weaknesses in terms of performance. Each programme has it's own perks and quite different in their own right, and there's a lot more to regex than i'm showing here, plus as i say, each programme has it's own functionality
