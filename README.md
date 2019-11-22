
Interpreter for a programming language based on the game "Human Resource Machine"

Usage:

    hrm.py [options] sourcefile
    Options:
        -d datafile Sets the interpreter to read input data from the datafile
                    (note: the "data" instruction will override data in the datafile)
        -m memsize     Sets the size of temporary memory (default is 25)
        -i inboxmode        
                    Tells the interpreter how to handle the situation where
                    an "inbox" instruction is encountered, but there is no more
                    data to read:
                    WARN = continue executing but display a warning (DEFAULT)
                    STOP = gracefully stop execution
                    QUERY = Query the user for the additional input
        -h          Display help.

Language Instruction Set:

    data valuelist  uses a whitespace separated list of values as the input data
                    Example: data 1 3 9 'A' 7 -1 15 'C'
                    Note: This command overrides data passed in via input file.

    init t v        initialize temp memory location t with value v
                    Example: init 15 123

    name t n        gives symbolic name n to temp memory location t which allows
                    $n to be used in place of t in all commands
                    Example: name 15 foo

    :tag            tags a position in the instruction set with a name that
                    can be referenced by any of the 'jump' instructions (see below)

    inbox           reads from input into working memory
    outbox          outputs working memory
    copyfrom t      copies value from temp memory location t into working memory
    copyto t        copies value from working memory into temp memory location t
    add t           working memory = working memory + value at temp memory location t
    sub t           working memory = working memory - value at temp memory location t
    bump+ t         increment value at temp memory location t
    bump- t         decrement value at temp memory location t
    jump tag        jump to the given tag
    jumpneg tag     jump to the given tag if value in working memory < 0
    jumpzero tag    jump to the given tag if value in working memory == 0


    t is any numeric value from 0 o 24
    n is any string starting with a letter, followed by any number of
      alphanumerics or underscores

Note:
    If instruction argument t above is surrounded by [], then dereference.
    Example: Let temp memory location 15 hold the value 7.
    Then "copyto [15]" will copy working memory to temp memory location 7.

There is one instruction per line.
Empty lines and lines starting with # are ignored.
Temp memory has room for 25 values (0-24).  It is initialized to zeros.
Working memory has room for 1 value, and is initialized to zero.
