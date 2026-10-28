# LAYER 4 - FRAMEWORKS & DRIVERS
#
# DEPENDENCY RULE: source code dependencies may only point inwards. This is the
# outermost layer, so it is the only place allowed to know about concrete
# frameworks, I/O devices, the system clock, and to import from every inner
# layer. Nothing in the inner layers may import from here; they reach this
# code only through interfaces that are wired up in main.py.
