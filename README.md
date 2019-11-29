
Interpreter for a programming language which is based on the language
in the game "Human Resource Machine" (with minor differences).

Usage:

    hrm.py [options] sourcefile
    Options:
        -d datafile Sets the interpreter to read input data from the datafile
                    (note: the "data" instruction will override data in the datafile)
        -m memsize  Sets the size of temporary memory (default is 25)
        -i inboxmode        
                    Tells the interpreter how to handle "inbox" instructions
                    when there is no more data to read:
                    WARN = continue executing but display a warning (DEFAULT)
                    STOP = gracefully stop execution
                    QUERY = Query the user for the additional input
        -g          enable debug mode
        -h          Display help.

Language Instruction Set:

    # comment       Lines starting with # are comments and are ignored.

    data valuelist  Uses a whitespace separated list of values as the input data.
                    Valid values are: integers, single characters enclosed in ''
                    Example: data 1 3 9 'A' 7 -1 15 'C'
                    Note: This command overrides data passed in via input file.

    init t v        Initialize temp memory reference t with value v.
                    Example: init 15 123

    name t n        Gives symbolic name n to temp memory reference t which allows
                    n to be used in place of t in all commands.
                    Example: name 15 foo

    :tag            Tags a position in the instruction set with a label (jumptag) that
                    can be referenced by any of the 'jump' instructions (see below).

    inbox           Reads from input into working memory.
    outbox          Outputs working memory.
    copyfrom t      Copies value from temp memory reference t into working memory.
    copyto t        Copies value from working memory into temp memory reference t.
    add t           Working memory = working memory + value at temp memory reference t.
    sub t           Working memory = working memory - value at temp memory reference t.
    bump+ t         Increment value at temp memory reference t.
    bump- t         Decrement value at temp memory reference t.
    jump :tag       Jump to the given tag.
    jumpneg :tag    Jump to the given tag if value in working memory < 0.
    jumpzero :tag   Jump to the given tag if value in working memory == 0.


    t is any numeric value from 0 to memsize
    n is any string starting with a letter, followed by any number of
      alphanumerics or underscores

Note:
    If instruction argument t above is surrounded by [], then dereference.
    Example: Let temp memory location 15 hold the value 7.
    Then "copyto [15]" will copy working memory to temp memory location 7.

There is one instruction per line.
Empty lines are ignored.
Temp memory is initialized to zeros.
Working memory has room for 1 value, and is initialized to zero.
