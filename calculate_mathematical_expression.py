#################################################################
# FILE : calculate_mathematical_expression.py
# WRITER : ilayee david sade , elay.sade , 326748894
# EXERCISE : intro2cs ex2 2025
# DESCRIPTION: A simple program that calculates simple mathematical
# expressions using input from the user
# STUDENTS I DISCUSSED THE EXERCISE WITH: None
# WEB PAGES I USED: None
# NOTES: None
#################################################################

def calculate_mathematical_expression(a, b, sign):
    """
    :param a: int/float
    :param b: int/float
    :param sign: math-operation (str)
    :return: result of mathematical expression (float/int)
    """
    match sign:
        case "+":
            return a + b
        case "-":
            return a - b
        case "*":
            return a * b
        case ":":
            if b==0:
                return None
            return a / b
        case _:
            return None

def calculate_from_string(string):
    """
    :param string: input of mathematical expression (str)
    :return: result of mathematical expression in the string (float/int)
    """
    # split to string relevant to each variable
    string = string.split(" ")
    a = float(string[0])
    sign = string[1]
    b = float(string[2])
    return calculate_mathematical_expression(a, b, sign)