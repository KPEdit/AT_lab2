# CONSTANTS
GROUP_BRACKET = 1 #
SQ_BRACKET = 2
REPEATS = 3 #
OR = 4 #
KLINI = 5 #
META = 6 #
META_NUM = 7 #
CHAR = 8 #
CONCAT = 9 #
EMPTY = 10 #
END_MEAT = 11
TMP_TOKEN = 12

SPECIALS = set(r"{}()[]|*#\\$")

# ERRORS

class PatternError(Exception):
  pass