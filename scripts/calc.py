"""
this script manages calculations
finds the limit of an expression by testing the end behavior of its derivatives
only works on windows
max howard, 5/28/2026
"""

import math, random
from decimal import getcontext, Decimal
getcontext().prec = 50
bound = Decimal(math.exp(getcontext().prec/2-1))
epsilon = Decimal(math.exp(-getcontext().prec/2+1))

def format_point(point: tuple, precision = 4, x_only=True, json=False):
    if json: #expect at point to be [x, y] and infinity values a str
        x = float(point[0])
        y = float(point[1])
        if not math.isfinite(x):
            x = "Infinity" if x > 0 else "-Infinity"
        else:
            x = round(x, precision)
        if not math.isfinite(y):
            y = "Infinity" if y > 0 else "-Infinity"
        else:
            y = round(y, precision)
        
        return [x, y]
    
    if x_only:
        n = float(point[-1])
        return str(round(n, precision))
    x, y = float(point[0]), float(point[1])
    x = str(round(x, precision))
    y = str(round(y, precision))
    return x, y

def sign(num) -> int:
    "returns 1 for positive, -1 for negative, 0 if within +- epsilon"
    if num > epsilon: return 1
    elif num < -epsilon: return -1
    return 0

def generate_points(func:str, num_points = 10, start=1, dest = Decimal('Infinity')):
    #check for bad function
    if func == '':
        raise ValueError('function cannot be empty')
    blacklist = ['yield', 'with', 'return', 'quit', 'lambda', 'exit()', 'os.', 'sys.', 'import', 'assert', 'raise', 'break', 'class', 'continue', 'def', 'del', 'dir', 'eval', 'exec', 'for', 'while']
    for ele in blacklist:
        if ele in func: raise ValueError(f'blacklisted item ({ele}) found in func')
    
    finite_point = False
    if dest == Decimal('Infinity'):
        dest = Decimal(math.exp(Decimal(num_points+1)))
    elif dest == Decimal('-Infinity'):
        dest = Decimal(-math.exp(Decimal(num_points-1)))
    else:
        finite_point = True
    
    adjusted_start  = Decimal(math.log(start))
    adjusted_end    = Decimal(math.log(abs(dest-epsilon)))
    #swap start and end if needed
    if adjusted_start > adjusted_end:
        temp = adjusted_start
        adjusted_start = adjusted_end
        adjusted_end = temp
    if adjusted_start == adjusted_end:
        raise ValueError
    #get linear spacing
    adjusted_range = adjusted_end-adjusted_start

    if finite_point:
        num_points = num_points//2
        step = abs(adjusted_range/(num_points))
    else:
        step = abs(adjusted_range/(num_points))

    linear_vals = [adjusted_start]
    for i in range(1, num_points):
        linear_vals.append(Decimal(linear_vals[-1]+step))
    #print(f'range: {adjusted_start},{adjusted_end}  step: {step}  num points = {len(linear_vals)}')
    #readjust
    variations = [Decimal(random.random()/5+.9) for x in linear_vals]
    x_vals = [Decimal(math.exp(Decimal(x)))*variations[i] for i,x in enumerate(linear_vals)]
    if finite_point:
        #add other side
        negative_x_vals = [-1*(val-dest) for val in x_vals]
        x_vals += negative_x_vals

    functions = [func.replace("var", str(x)) for x in x_vals]
    def execute(index: int):
        try:
            y = Decimal(eval(functions[index]))
        except OverflowError:
            y = Decimal('Infinity')
        return y
    points = [(x, execute(i)) for i, x in enumerate(x_vals)]
    return points

def find_derivative(points: list) -> list:
    "returns a list of the slope between each point"
    derivative_points = []
    for i, p in enumerate(points):
        if (i + 1) >= len(points): break
        x1=p[0]
        y1=p[1]
        x2=points[i+1][0]
        y2=points[i+1][1]
        delta_x = x2 - x1
        if delta_x == 0:
            raise ValueError(f"delta_x = 0, derivative can't be found, p0={p}, p1={points[i+1]}")
        if y2 == Decimal('Infinity'):
            derivative_points.append((delta_x/2+x1, y2))
            continue
        slope = (y2-y1)/delta_x
        derivative_points.append((delta_x/2+x1, slope))
    return derivative_points

def find_limit(func, points=20, dest = Decimal('Infinity')) -> tuple[list[tuple[Decimal, Decimal]], bool, str]:
    p        = generate_points(func, points, dest=dest)
    p_1prime = find_derivative(p)
    p_2prime = find_derivative(p_1prime)
    #check all points are good 
    if not all([len(p) == points, len(p_1prime) == points-1, len(p_2prime) == points-2]):
        raise ValueError(f'incorrect num of points, {len(p), len(p_1prime), len(p_2prime)}')
    #find end behavior
    p_end = sign(p[-1][1])
    p_1prime_end = sign(p_1prime[-1][1])
    p_2prime_end = sign(p_2prime[-1][1])
    print(abs(p[-1][1]))

    if (p_1prime_end != 0) or (p_2prime_end != 0):
        print('func diverges')
        return (p, False, 'derivative does not approach 0')
    elif abs(p[-1][1]) > bound:
        print(f'function likely diverges above {format_point(p[-1])}')
        return (p, False, 'derivative approaches 0 but above bound')
    else:
        print(f'function converges to {format_point(p[-1])}')
        return (p, True, 'derivative approaches 0 and within bound')
        #print(p)
        #print(p_1prime)

if __name__ == "__main__":
    generate_points('1/var', num_points = 10, start=1, dest = Decimal(0))
    #find_limit('(var**0.15)')

"""    
working functions:
1. reasonable rational functions

broken functions:
1. looping functions, take too long.  ex. math.fsum([Decimal(1/n) for n in range(1, int(var))])
2. oscilating functions, random sampiling is not completley immune ex. math.sin(var)
3. logarithmic growth




"""

