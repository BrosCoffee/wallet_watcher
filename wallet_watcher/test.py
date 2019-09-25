import time
t = time.time()

print(time.strftime('%Y-%m-%d %H:%M %Z', time.localtime(t)))
# '2019-05-27 12:03 CEST'

print(time.strftime('%Y-%m-%d', time.localtime(t)))

print(time.strftime('%H:%M', time.localtime(t)))

print(time.strftime('%Z', time.localtime(t)))

print(time.strftime('%Y-%m-%d %H:%M %Z', time.gmtime(t)))
# '2019-05-27 10:03 GMT'