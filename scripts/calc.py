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

class BlacklistError(Exception):
    """blacklist function called"""
    pass

class Point:
    def __init__(self, x: Decimal, y:Decimal):
        self.x = x
        self.y = y
        self.t = (x,y)
    def __getitem__(self, key):
        return self.t[key]

    def format(self, precision = 4, y_only=True, json=False):
        # Convert Decimal to float
        x = float(self.x)
        y = float(self.y)
        
        if json: #return JSON-serializable values
            # Helper to convert float to JSON-safe value
            def to_json_value(val):
                if math.isinf(val):
                    return "Infinity" if val > 0 else "-Infinity"
                elif math.isnan(val):
                    return "NaN"
                else:
                    return round(val, precision)
            x = to_json_value(x)
            y = to_json_value(y)
            out = [x, y]
            return out
        elif y_only:
            return str(round(y, precision))
        else:
            x = str(round(x, precision))
            y = str(round(y, precision))
            return x, y
    
    def __repr__(self) -> str:
        return(str(self.format()))

class Points:
    '''wrapper for a list of point objects'''
    def __init__(self, points: list[Point]):
        self.lst = points
    def __getitem__(self, key):
        return self.lst[key]

def sign(num) -> int:
    "returns 1 for positive, -1 for negative, 0 if within +- epsilon"
    if num > epsilon: return 1
    elif num < -epsilon: return -1
    return 0


def sample_function(func:str, num_points = 10, start=Decimal(1), dest = Decimal('Infinity')) -> Points:
    '''
    samples a function with exponetial samples
    acheives this by scaling a linear scale
    '''
    def variation(low = 0.9, high = 1.1) -> Decimal:
        '''generate float between low and high'''
        total_range = abs(high-low)
        shift = 1-(total_range/2)
        base = random.random()
        return Decimal((base*total_range)+shift)

    #check for bad function
    if func == '':
        raise ValueError('function cannot be empty')
    blacklist = ['yield', 'with', 'return', 'quit', 'lambda', 'exit()', 'os.', 'sys.', 'import', 'assert', 'raise', 'break', 'class', 'continue', 'def', 'del', 'dir', 'eval', 'exec', 'for', 'while']
    for ele in blacklist:
        if ele in func: raise BlacklistError(f'blacklisted item ({ele}) found in func')
    
    finite_point = False
    if dest == Decimal('Infinity'):
        dest = Decimal(math.exp(Decimal(num_points+1)))
    elif dest == Decimal('-Infinity'):
        dest = Decimal(-math.exp(Decimal(num_points-1)))
    else:
        finite_point = True
    
    direction = sign(dest-start)
    #get x values for sampled points
    x_values = []
    #print(start, dest, direction)
    if finite_point:
        for i in range(0, num_points):
            val = dest + (Decimal(math.exp(-i*variation())) * direction *-1)
            x_values.append(val)
    else:
        for i in range(0, num_points):
            val = start + (Decimal(math.exp(i*variation())) * direction)
            x_values.append(val)

    """ old broken method
    distance = abs(dest-start)
    assert sign(distance) != 0, ValueError(f'distance between start and destination of sampling is too small')
    adjusted_start  = Decimal(math.log(epsilon))
    adjusted_end    = Decimal(math.log(distance-epsilon))
    adjusted_distance = adjusted_end - adjusted_start
    
    delta = max(adjusted_distance/(num_points), 2*epsilon)
    linear_vals = [Decimal(0)] #these are a displacment from start
    for i in range(1, num_points):
        linear_vals.append(Decimal(linear_vals[-1]+delta))
    #shift to starting position
    shifted = [x*signs[2] for x in linear_vals]
    #scale to exponetial scale
    x_vals = [Decimal(math.exp(x))*variation()+start for x in shifted]
    """

    functions = [func.replace("var", str(x)) for x in x_values]
    def execute(index: int):
        try:
            y = Decimal(eval(functions[index]))
        except OverflowError:
            y = Decimal('Infinity')
            print('overflow error')
        except ZeroDivisionError:
            y = Decimal(0)
            print('zero div error')
        except NameError as e:
            raise ValueError(e, 'try "var"')
        return y
    points = [Point(x, execute(i)) for i, x in enumerate(x_values)]
    return Points(points)

def find_derivative(points: list[Point]) -> Points:
    "returns a list of the slope between each point"
    derivative_points = []
    for i, p in enumerate(points):
        if (i + 1) >= len(points): break
        x1 = p.x
        y1 = p.y
        x2 = points[i+1].x
        y2 = points[i+1].y
        delta_x = x2 - x1
        if delta_x == 0:
            raise ValueError(f"delta_x = 0, derivative can't be found, p0={p}, p1={points[i+1]}")
        if y2 == Decimal('Infinity'):
            derivative_points.append((delta_x/2+x1, y2))
            continue
        slope = (y2-y1)/delta_x
        derivative_points.append(Point(delta_x/2+x1, slope))
    return Points(derivative_points)

def find_limit(func, points=20, start=Decimal(0+epsilon), dest = Decimal('Infinity'), two_sided=True) -> tuple[Points, bool, str]:
    #takes a finite (two sided) limit by taking both right and left limits
    finite_point = False
    if math.isfinite(dest) and two_sided:
        #find negative limit
        print(dest-2)
        negative_limit   = find_limit(func, points//2, dest-2, dest, False)
        positive_limit   = find_limit(func, points//2, dest+2, dest, False)
        combined_points  = negative_limit[0].lst + [Point(Decimal("NaN"), Decimal("NaN"))] +positive_limit[0].lst #add a point at NaN, NaN between the lists so the graph knows not to draw a line
        combined_points  = Points(combined_points)
        both_reasons     = negative_limit[2] + ', ' + positive_limit[2]
        
        converges = False
        reason = "unknown, no test satisfied"
        #both derivatives must converge to the same val
        if all([negative_limit[1], positive_limit[1]]):
            converges = True
            reason = "both negative and positive limits converge, "
        else:
            converges = False
            if negative_limit[1]:
                reason = "the negative limit converges while the positive limit does not, "
            elif positive_limit[1]:
                reason = "the positive limit converges while the negative limit does not, "
            else:
                reason = "neither the positive or negative limits converge, "
        #they must reach the same value
        if sign(negative_limit[0][-1].y-positive_limit[0][-1].y)==0:
            #converges = converges and true does nothing
            reason += "and both limits approach the same value"
        else:
            if converges: reason += "but "
            else:         reason += "and "
            converges = False
            reason += f"the values the limits are different \n(-:{positive_limit[0][-1].format()}   +:{negative_limit[0][-1].format()})"

        reason += f"\n\n (subreasons: {both_reasons})"

        return (combined_points, converges, reason)
    else:
        p        = sample_function(func, points, start=start, dest=dest)
        p_1prime = find_derivative(p.lst)
        p_2prime = find_derivative(p_1prime.lst)
        #check all points are good 
        if not all([len(p.lst) == points, len(p_1prime.lst) == points-1, len(p_2prime.lst) == points-2]):
            raise ValueError(f'incorrect num of points, {len(p.lst), len(p_1prime.lst), len(p_2prime.lst)}')
        #find end behavior
        p_end = sign(p[-1].y)
        p_1prime_end = sign(p_1prime[-1].y)
        p_2prime_end = sign(p_2prime[-1].y)

        converges = False
        reason = "unknown, no test satisfied"

        #check for oscilation
        oscilation_0 = all([sign(p.y)==0 for p in p[-5:]])
        oscilation_1 = all([sign(p.y)==0 for p in p_1prime[-5:]])
        oscilation_2 = all([sign(p.y)==0 for p in p_2prime[-5:]])
        oscilates = all([(not oscilation_0), (not oscilation_1), (not oscilation_2)])
        oscilates = False #does not work right now
        print(oscilation_0, oscilation_1, oscilation_2, oscilates)

        #if end derivatives are non zero -> probably diverges
        if ((p_1prime_end != 0) or (p_2prime_end != 0)) and (not math.isfinite(dest)):
            converges = False
            reason = '1st and second derivatives are non zero'
            print(p_1prime[-1].y,p_2prime[-1].y)
        #outside bound
        elif abs(p[-1][1]) > bound:
            converges = False
            reason = f'Derivatives approach 0, but the function is too large >{round(bound,3)}'
        #if the function appears to oscilate
        elif oscilates:
            converges = False
            reason = f'function appears to oscilate'
        else:
            converges = True
            reason = 'Derivatives approach 0 and the function ends within bounds'
        
        return (p, converges, reason)

if __name__ == "__main__":
    sample_function('1/var', num_points = 5, start = Decimal(-1), dest = Decimal(1))
    #find_limit('(var**0.15)')

"""    
working functions:
1. reasonable rational functions

broken functions:
1. looping functions, take too long.  ex. math.fsum([Decimal(1/n) for n in range(1, int(var))])
2. oscilating functions, random sampiling is not completley immune ex. math.sin(var)
3. logarithmic growth




"""

