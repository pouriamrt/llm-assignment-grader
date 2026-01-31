# read numbers and show sum and avg
import sys

nums = []
for line in sys.stdin:
    for x in line.split():
        try:
            nums.append(float(x))
        except:
            pass
if nums:
    s = sum(nums)
    n = len(nums)
    print("Sum:", s)
    print("Average:", s / n)
else:
    print("no numbers")
