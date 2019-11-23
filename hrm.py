import sys
import re
import optparse
################################################################################
#
#   HrmInterpreter class
#   Parses and executes HRM commands
#
################################################################################
class HrmInterpreter:
    # -------------------------------------------------------------------------
    def __init__(self, instructions_string, data_string, memsize, inboxmode):
        # set up virtual machine
        self.parser = HrmParser()
        self.inbox_mode = inboxmode
        self.memsize = memsize
        self.temp = [0 for i in range(memsize)]
        self.working = 0
        self.ip = 0 # instruction pointer
        self.dp = 0 # input data pointer
        self.instructions = instructions_string.split("\n")
        self.tags = dict([(b,a) for (a,b) in list(enumerate(self.instructions)) if b[:1] == ":"])
        self.data = [eval(x) for x in data_string.split()]
        self.names = {}
        self.stats = {"size":0, "steps":0}

        self.stats["size"] = len(
            [0 for a in self.instructions
            if a[:3] in ("inb", "out", "cop", "add", "sub", "bum", "jum")]
        )

    # -------------------------------------------------------------------------
    def display_stats(self):
        print( " Statistics:" )
        print( " Size = {}".format(self.stats["size"]) )
        print( " Steps = {}".format(self.stats["steps"]) )

    # -------------------------------------------------------------------------
    def get_location(self, loc_string):

        number = "\d+"  # 1+ digits
        name = "[a-zA-Z][0-9a-zA-Z_]*"  # 1 alpha and 0+ AlphaNumUnderscores

        address_re = "^(" + number + ")$"               # group 1: number
        address_deref_re = "^\[(" + number + ")\]$"     # group 2: [number]
        symbol_re = "^\$(" + name + ")$"                # group 3: $name
        symbol_deref_re = "^\[\$(" + name + ")\]$"      # group 4: [$name]

        location_re = address_re + "|" + address_deref_re + "|" + symbol_re + "|" + symbol_deref_re

        m = re.match(location_re, loc_string)
        if m:
            addr = None
            if m.group(1) != None:
                # we got a numeric memory address
                addr = int(m.group(1))
            elif m.group(2) != None:
                # we got a pointer, so dereference it
                addr = int(self.temp[int(m.group(2))])
            elif m.group(3) != None:
                # we got a symbolic memory address
                addr = int(self.names[m.group(3)])
            elif m.group(4) != None:
                # we got a symbolic pointer, so dereference it
                addr = int(self.temp[int(self.names[m.group(4)])])

            if addr == None or addr < 0 or addr >= self.memsize:
                sys.exit("Error on line {}: "
                    "invalid memory address {}, "
                    "should be in range [0,{}]".format(self.ip, addr, self.memsize-1))
            else:
                return addr
        else:
            sys.exit("Syntax error on line {}: "
                "'{}' is not a valid location.".format(self.ip, loc_string))

    # -------------------------------------------------------------------------
    def get_args(self, tokens, arg_types=[]):

        args = tokens[1:]

        if len(args) != len(arg_types):
            sys.exit(
                "Error on line {}: "
                "instruction '{}' should have had {} arguments, "
                "it had {}.".format(
                    self.ip+1, tokens[0], len(arg_types), len(args)
                    )
                )

        if len(args) == 0: return []

        parse_list = zip(arg_types, args)
        res = []
        for type,arg in parse_list:
            if type == "location":
                res.append(self.get_location(arg))
            elif type =="value":
                res.append(arg)
            elif type == "name":
                res.append(arg)
            elif type == "tag":
                res.append(arg)
            else:
                sys.exit("Error: bad argument type '{}'".format(type))
                pass

        return res

    # -------------------------------------------------------------------------
    def run(self):
        # execute the HRM program until there are no more instructions
        while self.ip < len(self.instructions):

            # skip blank lines, comments, and tagged lines
            if len(self.instructions[self.ip]) == 0 or self.instructions[self.ip][0] in ('#', ':'):
                self.ip += 1
                continue

            # perform the given instruction
            tokens = self.instructions[self.ip].split()
            instruction = tokens[0]

            if instruction == "inbox":
                self.stats["steps"] += 1
                self.get_args(tokens)
                d = None
                if self.dp >= len(self.data):
                    if self.inbox_mode == "WARN":
                        print("Warning: attempting to input data, but there is no more.")
                    elif self.inbox_mode == "STOP":
                        print("Tried to read data that is not there ... ending HRM program.")
                        return
                    elif self.inbox_mode == "QUERY":
                        d = input("Enter a value for the inbox instruction:")
                else:
                    d = self.data[self.dp]
                    self.dp += 1

                self.working = d

            elif instruction == "outbox":
                self.stats["steps"] += 1
                self.get_args(tokens)
                print(self.working)

            elif instruction == 'data':
                data_string = " ".join(tokens[1:])
                self.data = [eval(x) for x in data_string.split()]

            elif instruction == "copyfrom":
                self.stats["steps"] += 1
                [arg] = self.get_args(tokens, ["location"])
                self.working = self.temp[arg]

            elif instruction == "copyto":
                self.stats["steps"] += 1
                [arg] = self.get_args(tokens, ["location"])
                self.temp[arg] = self.working

            elif instruction == "bump+":
                self.stats["steps"] += 1
                [arg] = self.get_args(tokens, ["location"])
                self.temp[arg] += 1

            elif instruction == "bump-":
                self.stats["steps"] += 1
                [arg] = self.get_args(tokens, ["location"])
                self.temp[arg] -= 1

            elif instruction == "add":
                self.stats["steps"] += 1
                [arg] = self.get_args(tokens, ["location"])
                self.working += self.temp[arg]

            elif instruction == "sub":
                self.stats["steps"] += 1
                [arg] = self.get_args(tokens, ["location"])
                self.working -= self.temp[arg]

            elif instruction == "init":
                [loc, val] = self.get_args(tokens, ["location", "value"])
                self.temp[loc] = eval(val)

            elif instruction == "name":
                [loc, name] = self.get_args(tokens, ["location", "name"])
                self.names[name] = loc

            elif instruction == "jump":
                self.stats["steps"] += 1
                [arg] = self.get_args(tokens, ["tag"])
                self.ip = self.tags[arg]
                continue

            elif instruction == "jumpneg":
                self.stats["steps"] += 1
                [arg] = self.get_args(tokens, ["tag"])
                if self.working < 0:
                    self.ip = self.tags[arg]
                    continue

            elif instruction == "jumpzero":
                self.stats["steps"] += 1
                [arg] = self.get_args(tokens, ["tag"])
                if self.working == 0:
                    self.ip = self.tags[arg]
                    continue

            else:
                sys.exit("Error on line {}: "
                    "bad instruction '{}'".format(self.ip+1, instruction))

            self.ip += 1
# end class definition

################################################################################
#
#   HrmParser class
#   Does the work of parsing HRM instructions
#
################################################################################
class HrmParser:
    def __init__(self):
        self.re_line = re.compile(
            r"\s*(?P<instruction>\w+|:[a-zA-Z]\w*)"
            r"(\s+(?P<arg_string>\S.*)|\s*)"
        )
        self.re_jumptag = re.compile(
            r"(?P<jumptag>:[a-zA-Z]\w*)"
        )
        self.re_memref = re.compile(
            r"(?P<memaddr>\d+)\s*$|"
            r"\[(?P<memaddr_deref>\d+)\]\s*$|"
            r"(?P<memname>[a-zA-Z]\w*)\s*$|"
            r"\[(?P<memname_deref>[a-zA-Z]\w*)\]\s*$"
        )

    def parse_line(self, code_line):
        m = self.re_line.match(code_line)
        if not m: return "unmatched"
        return (m.group('instruction'), m.group('arg_string'))

    def parse_jumptag(self, arg_string):
        m = self.re_jumptag.match(arg_string)
        if not m: return "unmatched"
        return (m.group("jumptag"))

    def parse_memref(self, arg_string):
        m = self.re_memref.match(arg_string)
        if not m: return "unmatched"
        return (m.group("memaddr"), m.group("memaddr_deref"), m.group("memname"), m.group("memname_deref"))

# end class definition

################################################################################
#
#   HrmOptionManager class
#   Handles all of the command line arguments and options
#
################################################################################
class HrmOptionManager:
    def __init__(self):
        parser = optparse.OptionParser(usage="%prog [options] sourcefile")
        parser.add_option("-d", type="string", dest="datafile",
            help="specifies the file that the interpreter should use as input data for the program it is interpreting")
        parser.add_option("-m", type="int", dest="memsize", default=25,
            help="sets the size of temporary memory (default is 25)")
        parser.add_option("-i", type="choice", dest="inboxmode",
            choices=["WARN","STOP","QUERY"], default="WARN",
            help="tells the interpreter how to handle the situation where "
            "an 'inbox' instruction is encountered, but there is no more data to read:\n"
            "WARN = continue executing but display a warning (DEFAULT). "
            "STOP = gracefully stop execution. "
            "QUERY = Query the user for the additional input.")
        (self.options, pos_args) = parser.parse_args()

        if len(pos_args) < 1:
            parser.error("missing name of sourcefile")
        elif len(pos_args) > 1:
            parser.error("too many command line arguments")
        else:
            self.sourcefile = pos_args[0]

        # read instructions from source file
        self.instructions_string = ""
        with open(self.sourcefile) as file:
            self.instructions_string = file.read()

        # read input data from data file (if provided)
        self.data_string = ""
        if self.options.datafile != None:
            with open(self.options.datafile) as file:
                self.data_string = file.read()
# end class definition

################################################################################
#
#   Main Program
#
################################################################################

opman = HrmOptionManager()
hrm = HrmInterpreter(
    opman.instructions_string,
    opman.data_string,
    opman.options.memsize,
    opman.options.inboxmode)
hrm.run()
hrm.display_stats()

parser = HrmParser()
print(parser.parse_line("  command crisp_bacon"))
print(parser.parse_line("command   crisp_bacon  "))
print(parser.parse_line("  "))
print(parser.parse_line("command"))
print(parser.parse_line("  command 7"))
print(parser.parse_line("  command a_7"))
print(parser.parse_line("  command 1 2 3 4 5"))
print(parser.parse_line("  command %#@$"))
print(parser.parse_line("  command y"))
print(parser.parse_line(":foo"))
print(parser.parse_line(":foo_1"))
print(parser.parse_line(":1"))
print(parser.parse_line(":foo badarg"))
print(parser.parse_jumptag("test"))
print(parser.parse_jumptag(":test"))
print(parser.parse_jumptag(":1"))
print(parser.parse_jumptag(":test1"))
print(parser.parse_jumptag(":test  ") + "x")
print(parser.parse_jumptag(":_test"))
print(parser.parse_jumptag(":test_test"))
print(parser.parse_jumptag(":test_11"))
print(parser.parse_memref("5"))
print(parser.parse_memref("55"))
print(parser.parse_memref("5foo"))
print(parser.parse_memref("foo5"))
print(parser.parse_memref("foo_5"))
print(parser.parse_memref("_foo5"))
print(parser.parse_memref("[5]"))
print(parser.parse_memref("[55]"))
print(parser.parse_memref("[foo]"))
print(parser.parse_memref("[foo5]"))
