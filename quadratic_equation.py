#################################################################
# FILE : quadratic_equation.py
# WRITER : ilayee david sade , elay.sade , 326748894
# EXERCISE : intro2cs ex2 2025
# DESCRIPTION: A simple program that has a method which calculates the solutions of
# quadratic equations and solves quadratic equations which are inputted by the user
# STUDENTS I DISCUSSED THE EXERCISE WITH: None
# WEB PAGES I USED: None
# NOTES: None
#################################################################

import math

def quadratic_equation(a, b, c):
    """
    :param a: int/float
    :param b: int/float
    :param c: int/float
    :return: the solutions of the quadratic equation (int\float, int\float)
    """
    d = b*b - 4*a*c
    if d < 0: # no solutions
        return None, None
    if d == 0: # 1 solution
        return -b/(2*a), None
    else: # 2 solutions
        x_1 = (-b + math.sqrt(d))/(2*a)
        x_2 = (-b - math.sqrt(d))/(2*a)
        return x_1, x_2

def quadratic_equation_user_input():
    """
    User input for a,b,c of the quadratic equation
    and then printing of the solutions
    :return: None
    """
    print("Insert coefficients a, b, and c: ", end="")
    # split to string relevant to each variable
    a, b, c = input().split(' ')
    a, b, c = int(a), int(b), int(c)
    if a == 0:
        print("The parameter 'a' may not equal 0")
        return
    x_1, x_2 = quadratic_equation(a, b, c)
    if x_1 is None:
        print("The equation has no solutions")
    elif x_2 is None:
        print("The equation has 1 solution: " + str(x_1))
    else:
        print("The equation has 2 solutions: " + str(x_1) + " and " + str(x_2))