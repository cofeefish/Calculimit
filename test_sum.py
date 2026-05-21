from decimal import getcontext, Decimal
import tqdm, math

getcontext().prec = 16
#math.fsum([Decimal(1/n) for n in range(1, int(10e6))])
s=Decimal(0)
for n in tqdm.tqdm(range(1, int(10e8))):
    s += Decimal(1/n)
print(s)
#1574226