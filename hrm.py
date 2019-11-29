import sys
import re
import optparse
from sys import version_info
if version_info.major == 3:
    pass
elif version_info.major == 2:
    try:
        input = raw_input
    except NameError:
        pass
################################################################################
#
#   HrmInterpreter class
#   Parses and executes HRM commands
#
################################################################################
class HrmInterpreter:
    # -------------------------------------------------------------------------
    def __init__(self, instructions_string, data_string, memsize, debugmode, inboxmode):
        # set up virtual machine
        self.parser = HrmParser()
        self.inbox_mode = inboxmode
        self.debug_mode = debugmode
        self.memsize = memsize
        self.temp = [0 for i in range(memsize)]
        self.working = 0
        self.ip = 0 # instruction pointer
        self.dp = 0 # input data pointer
        self.instructions = instructions_string.split("\n")
        self.jumptags = dict(
            [(b.strip(),a)
            for (a,b) in list(enumerate(self.instructions))
            if b.strip()[:1] == ":"]
        )
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
    def validate_memaddr(self, addr):
        if addr == None or addr < 0 or addr >= self.memsize:
            sys.exit("Error on line {}: "
                "invalid memory address {}, "
                "should be in range [0,{}]".format(self.ip+1, addr, self.memsize-1))
    # -------------------------------------------------------------------------
    def validate_memname(self, name):
        if not name in self.names:
            sys.exit("Error on line {}: "
                "instruction referenced "
                "non-existent memory name '{}''.".format(self.ip+1, name))
    # -------------------------------------------------------------------------
    def validate_jumptag(self, jumptag):
        if not jumptag in self.jumptags:
            sys.exit("Error on line {}: "
                "instruction referenced "
                "non-existent jumptag '{}''.".format(self.ip+1, jumptag))
    # -------------------------------------------------------------------------
    def get_memref(self, mem_tuple):

            (memref, type, deref) = mem_tuple

            addr = None
            if   type == 'addr': addr = int(memref)
            elif type == 'name':
                self.validate_memname(memref)
                addr = self.names[memref]

            self.validate_memaddr(addr)

            if deref: addr = self.temp[addr]

            self.validate_memaddr(addr)

            return addr

    # -------------------------------------------------------------------------
    def get_args(self, instruction, arg_string, arg_types=[]):

        args = arg_string.split()

        if len(arg_types)>0 and arg_types[0] == "valuelist":
            arg_types = ["valuelist" for a in args]

        if len(args) != len(arg_types):
            sys.exit(
                "Error on line {}: "
                "instruction '{}' should have had {} arguments, "
                "it had {}.".format(
                    self.ip+1, instruction, len(arg_types), len(args)
                    )
                )

        if len(args) == 0: return []

        parse_list = zip(arg_types, args)
        res = []
        for type,arg in parse_list:
            if type == "memref":
                mem_tuple = self.parser.parse_memref(arg)
                res.append(self.get_memref(mem_tuple))
            elif type == "value" or type == "valuelist":
                value = self.parser.parse_value(arg)
                res.append(value)
            elif type == "name":
                name = self.parser.parse_name(arg)
                res.append(name)
            elif type == "jumptag":
                jumptag = self.parser.parse_jumptag(arg)
                self.validate_jumptag(jumptag)
                res.append(jumptag)
            else:
                sys.exit("Error: bad argument type '{}'".format(type))
                pass

        return res

    # -------------------------------------------------------------------------
    def run(self):
        # execute the HRM program until there are no more instructions
        while self.ip < len(self.instructions):

            self.parser.set_line_num(self.ip+1)
            (instruction, arg_string) = self.parser.parse_line(self.instructions[self.ip])

            if self.debug_mode:
                print(">> working with value {}".format(self.working))
                print(">> line {}, {} {}".format(self.ip+1, instruction, arg_string))
                dbgcmd = input("Enter debug command (n=next, q=quit):")
                if dbgcmd != "" and dbgcmd in "qQ": return

            # perform the given instruction

            if len(instruction) == 0 or instruction[0] in ('#', ':'):
                # skip blank lines, comments, and lines with jumptags
                self.ip += 1
                continue

            elif instruction == 'data':
                self.data = self.get_args(instruction, arg_string, ["valuelist"])

            elif instruction == "init":
                [loc, val] = self.get_args(instruction, arg_string, ["memref", "value"])
                self.temp[loc] = val

            elif instruction == "name":
                [loc, name] = self.get_args(instruction, arg_string, ["memref", "name"])
                self.names[name] = loc

            elif instruction == "inbox":
                self.stats["steps"] += 1
                self.get_args(instruction, arg_string)
                d = None
                if self.dp >= len(self.data):
                    if self.inbox_mode == "WARN":
                        print("Warning: attempting to input data, but there is no more.")
                    elif self.inbox_mode == "STOP":
                        print("Data exhausted ... ending HRM program.")
                        return
                    elif self.inbox_mode == "QUERY":
                        d = input("Enter a value for the inbox instruction:")
                else:
                    d = self.data[self.dp]
                    self.dp += 1

                self.working = d

            elif instruction == "outbox":
                self.stats["steps"] += 1
                self.get_args(instruction, arg_string)
                print(self.working)

            elif instruction == "copyfrom":
                self.stats["steps"] += 1
                [arg] = self.get_args(instruction, arg_string, ["memref"])
                self.working = self.temp[arg]

            elif instruction == "copyto":
                self.stats["steps"] += 1
                [arg] = self.get_args(instruction, arg_string, ["memref"])
                self.temp[arg] = self.working

            elif instruction == "bump+":
                self.stats["steps"] += 1
                [arg] = self.get_args(instruction, arg_string, ["memref"])
                self.temp[arg] += 1

            elif instruction == "bump-":
                self.stats["steps"] += 1
                [arg] = self.get_args(instruction, arg_string, ["memref"])
                self.temp[arg] -= 1

            elif instruction == "add":
                self.stats["steps"] += 1
                [arg] = self.get_args(instruction, arg_string, ["memref"])
                if type(self.working) == type(self.temp[arg]):
                    self.working += self.temp[arg]
                else:
                    sys.exit("Error on line {}: "
                    "incompatible operand types "
                    "{},{}".format(self.ip+1, self.working, self.temp[arg]))

            elif instruction == "sub":
                self.stats["steps"] += 1
                [arg] = self.get_args(instruction, arg_string, ["memref"])
                if type(self.working) == type(self.temp[arg]):
                    self.working -= self.temp[arg]
                else:
                    sys.exit("Error on line {}: "
                    "incompatible operand types: "
                    "{},{}".format(self.ip+1, self.working, self.temp[arg]))

            elif instruction == "jump":
                self.stats["steps"] += 1
                [arg] = self.get_args(instruction, arg_string, ["jumptag"])
                self.ip = self.jumptags[arg]
                continue

            elif instruction == "jumpneg":
                self.stats["steps"] += 1
                [arg] = self.get_args(instruction, arg_string, ["jumptag"])
                if self.working < 0:
                    self.ip = self.jumptags[arg]
                    continue

            elif instruction == "jumpzero":
                self.stats["steps"] += 1
                [arg] = self.get_args(instruction, arg_string, ["jumptag"])
                if self.working == 0:
                    self.ip = self.jumptags[arg]
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
        self.line_num = None
        self.re_line = re.compile(
            r"\s*(?P<instruction>[\w\+-]+|:[a-zA-Z]\w*|#.*|$)"
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
        self.re_value = re.compile(
            r"(?P<intval>-?\d+)|'(?P<charval>[a-zA-Z])'"
        )
        self.re_name = re.compile(
            r"(?P<name>[a-zA-Z]\w*)"
        )

    # -------------------------------------------------------------------------
    def set_line_num(self, line_num):
        self.line_num = line_num

    # -------------------------------------------------------------------------
    def parse_line(self, code_line):
        # returns a tuple containing the instruction and the arg_string
        m = self.re_line.match(code_line)
        if not m:
            sys.exit("Error on line {}: invalid line of HRM code '{}'".format(self.line_num, code_line))
        arg_string = "" if m.group('arg_string')==None else m.group('arg_string')
        return (m.group('instruction'), arg_string)

    # -------------------------------------------------------------------------
    def parse_jumptag(self, arg_string):
        # returns the jumptag
        m = self.re_jumptag.match(arg_string)
        if not m:
            sys.exit("Error on line {}: invalid jumptag '{}'".format(self.line_num, arg_string))
        return m.group('jumptag')

    # -------------------------------------------------------------------------
    def parse_memref(self, arg_string):
        # returns a tuple containing the memory reference, and what type it is
        # (possible types are: 'addr', 'name'), and a boolean indicating whether we
        # need to dereference it.
        m = self.re_memref.match(arg_string)
        if not m:
            sys.exit("Error on line {}: invalid memory reference '{}'".format(self.line_num, arg_string))

        for k,v in m.groupdict().items():
            if v != None:
                deref = ('deref' in k)
                type = k[3:7] # extract the type from the dictionary key
                return (v, type, deref)

        return (None, None, None) # should be impossible to execute this

    # -------------------------------------------------------------------------
    def parse_value(self, arg_string):
        # returns a valid data value
        m = self.re_value.match(arg_string)
        if not m:
            sys.exit("Error on line {}: invalid data value '{}'".format(self.line_num, arg_string))
        if m.group('intval') != None:
            return int(m.group('intval'))
        elif m.group('charval') != None:
            return m.group('charval')
        else:
            return None # should be impossible to execute this
    # -------------------------------------------------------------------------
    def parse_name(self, arg_string):
        # returns a valid name for a memory address
        m = self.re_name.match(arg_string)
        if not m:
            sys.exit("Error on line {}: invalid name '{}'".format(self.line_num, arg_string))
        return m.group("name")

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
            help="specifies the file that the interpreter should use as input "
            "data for the program it is interpreting")
        parser.add_option("-g", action="store_true", dest="debugmode", default=False,
            help="enables debug mode")
        parser.add_option("-i", type="choice", dest="inboxmode",
            choices=["WARN","STOP","QUERY"], default="WARN",
            help="tells the interpreter how to handle 'inbox' instructions "
            "when there is no more data to read: "
            "WARN = continue executing but display a warning (DEFAULT). "
            "STOP = gracefully stop execution. "
            "QUERY = Query the user for the additional input.")
        parser.add_option("-m", type="int", dest="memsize", default=25,
            help="sets the size of temporary memory (default is 25)")
        (options, pos_args) = parser.parse_args()

        if len(pos_args) < 1:
            parser.error("missing name of sourcefile")
        elif len(pos_args) > 1:
            parser.error("too many command line arguments")
        else:
            sourcefile = pos_args[0]

        self.memsize = options.memsize
        self.inboxmode = options.inboxmode
        self.debugmode = options.debugmode

        # read instructions from source file
        self.instructions_string = ""
        with open(sourcefile) as file:
            self.instructions_string = file.read()

        # read input data from data file (if provided)
        self.data_string = ""
        if options.datafile != None:
            with open(options.datafile) as file:
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
    opman.memsize,
    opman.debugmode,
    opman.inboxmode)
hrm.run()
hrm.display_stats()
