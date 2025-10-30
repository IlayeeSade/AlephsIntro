#################################################################
# FILE : shapes.py
# WRITER : ilayee david sade , elay.sade , 326748894
# EXERCISE : intro2cs ex2 2025
# DESCRIPTION: A simple program that has a method which returns area of a shape
# with the user's input of the type of shape and the relevant measures
# STUDENTS I DISCUSSED THE EXERCISE WITH: None
# WEB PAGES I USED: None
# NOTES: None
#################################################################

import math

def shape_area():
    """
    User input wanted shape and then the required arc length
    in order to calculate the area of the shape
    :return: result of shape area
    """
    print("Choose shape (1=circle, 2=rectangle, 3=triangle): ", end="")
    s = input()
    if s == "1":
        # circle
        r = input()
        r = float(r)
        return math.pi * r * r
    elif s == "2":
        # rectangle
        a = float(input())
        b = float(input())
        return a * b
    elif s == "3":
        # triangle
        a = input()
        a = float(a)
        return a * a * math.sqrt(3) / 4
    else:
        return None