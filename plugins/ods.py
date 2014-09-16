#!/usr/bin/env python

'''
# PLACEHOLDER CODE
# copy pasted straight from the example at https://github.com/mmulqueen/odswriter

TODO:
  * Parse datapackage.json and read the JSON table schema
  * Lint and store rows
'''

import datetime
import decimal
import odswriter as ods

with ods.writer(open("test.ods","wb")) as odsfile:
    odsfile.writerow(["String", "ABCDEF123456", "123456"])
    # Lose the 2L below if you want to run this example code on Python 3, Python 3 has no long type.
    odsfile.writerow(["Float", 1, 123, 123.123, 2L, decimal.Decimal("10.321")])
    odsfile.writerow(["Date/DateTime", datetime.datetime.now(), datetime.date(1989,11,9)])
    odsfile.writerow(["Time",datetime.time(13,37),datetime.time(16,17,18)])
    odsfile.writerow(["Bool",True,False,True])
    odsfile.writerow(["Formula",1,2,3,ods.Formula("IF(A1=2,B1,C1)")])

