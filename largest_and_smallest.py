#     case4a, case4b, case4c = 5, 5, 5
#     case5a, case5b, case5c = -1, 1, 0
# In the first case everything is the same so it might confuse the system
# In the second case there are negatives and 0 so it might confuse the system
# and the minimum is in the last position, which is new

#################################################################
# FILE : largest_and_smallest.py
# WRITER : ilayee david sade , elay.sade , 326748894
# EXERCISE : intro2cs ex2 2025
# DESCRIPTION: A simple program that has a method which returns the max and min from
# 3 numbers and checks itself for correctness
# STUDENTS I DISCUSSED THE EXERCISE WITH: None
# WEB PAGES I USED: None
# NOTES: None
#################################################################
def largest_and_smallest(a, b, c):
    """
    :param a: int
    :param b: int
    :param c: int
    :return: max, min (int, int)
    """
    if a > b:
        # if a > b
        if b > c:
            # if a > b > c then we know
            return a, c
        else:
            # if a > b, b <= c then b is min but we need to know the max
            if a > c:
                return a, b
            else:
                return c, b
    else:
        # if a <= b
        if a > c:
            # if c < a <= b the c min and b is max
            return b, c
        else:
            # if a <= b, a <= c then we know a is min but we need to know the max
            if b > c:
                return b, a
            else:
                return c, a


def check_largest_and_smallest():
    """
    checks largest_and_smallest correctness
    :return: correctness (boolean)
    """
    # Define case inputs
    case1a, case1b, case1c = 17, 1, 6
    case2a, case2b, case2c = 1, 17, 6
    case3a, case3b, case3c = 1, 1, 2
    case4a, case4b, case4c = 5, 5, 5
    case5a, case5b, case5c = 1, 0, -1

    # Define expected outputs
    expected1a, expected1b = 17, 1
    expected2a, expected2b = 17, 1
    expected3a, expected3b = 2, 1
    expected4a, expected4b = 5, 5
    expected5a, expected5b = 1, -1
    # case 1
    a, b = largest_and_smallest(case1a, case1b, case1c)
    if not (a == expected1a and b == expected1b):
        return False
    # case 2
    a, b = largest_and_smallest(case2a, case2b, case2c)
    if not (a == expected2a and b == expected2b):
        return False
    # case 3
    a, b = largest_and_smallest(case3a, case3b, case3c)
    if not (a == expected3a and b == expected3b):
        return False
    # case 4
    a, b = largest_and_smallest(case4a, case4b, case4c)
    if not (a == expected4a and b == expected4b):
        return False
    # case 5
    a, b = largest_and_smallest(case5a, case5b, case5c)
    if not (a == expected5a and b == expected5b):
        return False
    return True
