#################################################################
# FILE : temperature.py
# WRITER : ilayee david sade , elay.sade , 326748894
# EXERCISE : intro2cs ex2 2025
# DESCRIPTION: A simple program that returns if vormir had at least two days hotter
# then the max temp inputted
# STUDENTS I DISCUSSED THE EXERCISE WITH: None
# WEB PAGES I USED: None
# NOTES: None
#################################################################

def is_vormir_safe(ex_tmp, tmp1, tmp2, tmp3):
    """
    If we had at least two days hotter then the max temp
    then we return true because vormir is then safe
    :param ex_tmp: max temp
    :param tmp1: day 1 temperature (int)
    :param tmp2: day 2 temperature (int)
    :param tmp3: day 3 temperature (int)
    :return: is vormir safe (boolean)
    """
    # if tmp_i which is at least one, then we check for at least another one
    if tmp1 > ex_tmp and (tmp2 > ex_tmp or tmp3 > ex_tmp):
        return True
    if tmp2 > ex_tmp and (tmp1 > ex_tmp or tmp3 > ex_tmp):
        return True
    if tmp3 > ex_tmp and (tmp1 > ex_tmp or tmp2 > ex_tmp):
        return True
    return False