# number stats
nums = []
while True:
    line = input("enter number: ")
    if line == "":
        break
    nums.append(float(line))
total = sum(nums)
print("sum", total)
# average not implemented yet
