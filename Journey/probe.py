try:
    a = 'sdfdsf'
    a[4] = '6'
except ValueError as e:
    print e
else:
    print 'else'
print 'after'