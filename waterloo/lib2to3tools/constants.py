from enum import IntEnum


class Token(IntEnum):
    """
    copied from constants defined in:
    cpython/lib2to3/pgen2/token.py

    `from lib2to3.pgen2 import token`
    """
    ENDMARKER = 0
    NAME = 1
    NUMBER = 2
    STRING = 3
    NEWLINE = 4
    INDENT = 5
    DEDENT = 6
    LPAR = 7
    RPAR = 8
    LSQB = 9
    RSQB = 10
    COLON = 11
    COMMA = 12
    SEMI = 13
    PLUS = 14
    MINUS = 15
    STAR = 16
    SLASH = 17
    VBAR = 18
    AMPER = 19
    LESS = 20
    GREATER = 21
    EQUAL = 22
    DOT = 23
    PERCENT = 24
    BACKQUOTE = 25
    LBRACE = 26
    RBRACE = 27
    EQEQUAL = 28
    NOTEQUAL = 29
    LESSEQUAL = 30
    GREATEREQUAL = 31
    TILDE = 32
    CIRCUMFLEX = 33
    LEFTSHIFT = 34
    RIGHTSHIFT = 35
    DOUBLESTAR = 36
    PLUSEQUAL = 37
    MINEQUAL = 38
    STAREQUAL = 39
    SLASHEQUAL = 40
    PERCENTEQUAL = 41
    AMPEREQUAL = 42
    VBAREQUAL = 43
    CIRCUMFLEXEQUAL = 44
    LEFTSHIFTEQUAL = 45
    RIGHTSHIFTEQUAL = 46
    DOUBLESTAREQUAL = 47
    DOUBLESLASH = 48
    DOUBLESLASHEQUAL = 49
    AT = 50
    ATEQUAL = 51
    OP = 52
    COMMENT = 53
    NL = 54
    RARROW = 55
    AWAIT = 56
    ASYNC = 57
    ERRORTOKEN = 58
    N_TOKENS = 59
    NT_OFFSET = 256


class Symbol(IntEnum):
    """
    copied from constants defined in:
    cpython/Lib/symbol.py

    `from symbol import *`
    """
    single_input = 256
    file_input = 257
    eval_input = 258
    decorator = 259
    decorators = 260
    decorated = 261
    async_funcdef = 262
    funcdef = 263
    parameters = 264
    typedargslist = 265
    tfpdef = 266
    varargslist = 267
    vfpdef = 268
    stmt = 269
    simple_stmt = 270
    small_stmt = 271
    expr_stmt = 272
    annassign = 273
    testlist_star_expr = 274
    augassign = 275
    del_stmt = 276
    pass_stmt = 277
    flow_stmt = 278
    break_stmt = 279
    continue_stmt = 280
    return_stmt = 281
    yield_stmt = 282
    raise_stmt = 283
    import_stmt = 284
    import_name = 285
    import_from = 286
    import_as_name = 287
    dotted_as_name = 288
    import_as_names = 289
    dotted_as_names = 290
    dotted_name = 291
    global_stmt = 292
    nonlocal_stmt = 293
    assert_stmt = 294
    compound_stmt = 295
    async_stmt = 296
    if_stmt = 297
    while_stmt = 298
    for_stmt = 299
    try_stmt = 300
    with_stmt = 301
    with_item = 302
    except_clause = 303
    suite = 304
    namedexpr_test = 305
    test = 306
    test_nocond = 307
    lambdef = 308
    lambdef_nocond = 309
    or_test = 310
    and_test = 311
    not_test = 312
    comparison = 313
    comp_op = 314
    star_expr = 315
    expr = 316
    xor_expr = 317
    and_expr = 318
    shift_expr = 319
    arith_expr = 320
    term = 321
    factor = 322
    power = 323
    atom_expr = 324
    atom = 325
    testlist_comp = 326
    trailer = 327
    subscriptlist = 328
    subscript = 329
    sliceop = 330
    exprlist = 331
    testlist = 332
    dictorsetmaker = 333
    classdef = 334
    arglist = 335
    argument = 336
    comp_iter = 337
    sync_comp_for = 338
    comp_for = 339
    comp_if = 340
    encoding_decl = 341
    yield_expr = 342
    yield_arg = 343
    func_body_suite = 344
    func_type_input = 345
    func_type = 346
    typelist = 347
