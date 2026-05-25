import math, random
from decimal import getcontext, Decimal
epsilon = Decimal(1e-8)

def format_point(point: tuple, precision = 3):
    n = int(point[-1])
    return str(round(n, precision))

def sign(num) -> int:
    "returns 1 for positive, -1 for negative, 0 if within +- epsilon"
    if num > epsilon: return 1
    elif num < -epsilon: return -1
    return 0

def generate_points(func:str, num_points = 10, start=1, dest = Decimal('Infinity')):
    #check for bad function
    if 'for' in func:
        print('function contains looping, replacing function with a polynomial')
    #
    getcontext().prec = 15
    
    #generate x_vals for test points
    if dest == Decimal('Infinity'):
        #list of random multiplers to add to x_val to improve sampling 
        variations = [Decimal(random.random()/5+.9) for x in range(start, num_points)]
        x_vals = [Decimal(math.exp(Decimal(x)*variations[x])) for x in range(start, num_points)]
    elif dest == Decimal('-Infinity'):
        variations = [Decimal(random.random()/5+.9) for x in range(-num_points, -start)]
        x_vals = [Decimal(math.exp(Decimal(x)*variations[x])) for x in range(-num_points, -start)]
    else:
        adjusted_start  = math.pow(start, -math.e)
        adjusted_end    = math.pow(abs(dest-epsilon), -math.e)
        #get linear spacing
        adjusted_range = adjusted_end-adjusted_start
        step = adjusted_range/(num_points//2)
        linear_vals = [adjusted_start]
        while linear_vals[-1] < adjusted_end:
            linear_vals.append(linear_vals[-1]+step)
        #readjust
        print(adjusted_start, adjusted_end)
        x_vals = [Decimal(math.exp(val)) for val in linear_vals]
        #add negative half of x_vals
        negative_x_vals = [-1*(val-dest) for val in x_vals]
        x_vals += negative_x_vals
        print(x_vals)


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
        if y2 == Decimal('Infinity'):
            derivative_points.append((delta_x/2+x1, y2))
            continue
        slope = (y2-y1)/delta_x
        derivative_points.append((delta_x/2+x1, slope))
    return derivative_points

def find_limit(func):
    p        = generate_points(func, 20)
    p_1prime = find_derivative(p)
    p_2prime = find_derivative(p_1prime)
    p_3prime = find_derivative(p_1prime)
    #if the derivative is does not approach 0, it diverges (sign of 2nd and first derivative must match)
    print(sign(p_1prime[-1][1]) != 0, sign(p_1prime[-1][1]), sign(p_2prime[-1][1]))
    if (sign(p_1prime[-1][1]) != 0) and ((sign(p_1prime[-1][1]) == sign(p_2prime[-1][1])) or (sign(p_2prime[-1][1]) == 0)):
        print('func diverges')
        return
    #if first and second derivative are oppisite signs,
        print(f'function diverges or converges above {format_point(p[-1])}')
    else:
        print(f'function converges to {format_point(p[-1])}')
        #print(p)
        #print(p_1prime)
if __name__ == "__main__":
    generate_points('1/x', num_points = 10, start=1, dest = Decimal(0))
    #find_limit('(var**0.15)')

"""
working functions:
1. reasonable rational functions

broken functions:
1. looping functions, take too long.  ex. math.fsum([Decimal(1/n) for n in range(1, int(var))])
2. oscilating functions, random sampiling is not completley immune ex. math.sin(var)
3. logarithmic growth




"""

