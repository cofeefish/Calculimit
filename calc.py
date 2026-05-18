import math
function_dict = { 
    # function : (arg_amnt, python eqiv)
    "+"     : (2, "x+x"),
    "-"     : (2, "x-x"),
    "^"     : (2, "math.pow(x, x)"),
    "frac"  : (2, "x/x")

}

class math_node :
    node_dict = {}
    def __init__(self, func_interval:list|None, arg_intervals:list|None, level:int, full_str:str, parent = None, root = False, leaf = False, data = None):
        self.level = level
        self.leaf = False
        if not leaf:
            assert type(func_interval) == list
            assert type(arg_intervals) == list
            self.start_ind = func_interval[0]
            assert type(self.start_ind) == int
            self.end_ind = arg_intervals[-1][-1]
            assert type(self.end_ind) == int
            self.id = f'{self.start_ind}-{self.end_ind},{level}'
            self.raw_str = full_str[self.start_ind:self.end_ind]

            self.func_name = full_str[self.start_ind:func_interval[1]]
            arg_amnt = function_dict[self.func_name][0]
            sub_args = []
            for interval in arg_intervals[-arg_amnt:]:
                arg_j = full_str[interval[0]:interval[1]]#.strip('{')
                if arg_j.isdigit(): arg_j = int(arg_j)
                sub_args.append(arg_j)
            assert function_dict[self.func_name][0] == len(sub_args), f"unexpected number of args ({len(sub_args)}) in \"{self.raw_str}\""

            self.parent = parent
            self.arguments = sub_args #argumernts are the node's children
            if parent is None:
                self.root = self
                self.tree_dict = {self.id : self}
            else:
                self.root = parent.root
                parent.add_child(self)
                self.root.tree_dict[self.id] = self
            node_dict = math_node.node_dict
            if level not in node_dict.keys():
                math_node.node_dict.update({level : []})
            if level+1 not in node_dict.keys():
                math_node.node_dict.update({level+1 : []})
            math_node.node_dict[level].append(self)
        else:
            self.leaf = True
            assert data != None
            self.variable = False
            if str(data).isdecimal():
                self.data = str(data).strip()
                self.variable = True
            else:
                self.data = float(data)

    def vizualize(self):
        '''print full equation tree'''
        #find longest (by str len) level
        #traverse tree
        

        padding = 2
        longest = 0 
        for level, node_list in sorted(math_node.node_dict.items()):
            length = sum([len(func.func_name)+padding for func in node_list])
            if length >= longest:
                longest = length

        for level, node_list in sorted(math_node.node_dict.items()):
            length = sum([len(func.func_name)+padding for func in node_list])
            margin = (longest - length)//2
            level_str = ' '*margin+''.join([func.func_name + ' '*padding for func in node_list])+' '*margin
            print(level, level_str)

    def __repr__(self) -> str:
        par = self.parent.id if type(self.parent) == math_node else None
        return f'function [{self.id}]: {self.func_name}({str(self.arguments)[1:-1]}), inside of {par}'

def parser(func: str) -> float:
    r'''
    parses math functions written in tex into a tree,
    each node (function) sould have a child for each of it's arguments
    leaf nodes are constants or variables, non-leaf nodes are operators or functions
    example eq \frac{\sin(x)}{2\sqrt[3]{\textbf{y}}}
       div
    sin   mult
     x    2  root
             3  y
    '''
    i = 0
    level = 0
    func_intervals = {}
    arg_intervals = {}
    func_list = []
    last_close = 0
    while i < len(func):
        c = func[i]
        print(f'{str(i).zfill(3)}: level_{str(level).zfill(2)}, {c}')
        if (c == "\\"):
            if not (level in func_intervals.keys()):
                func_intervals.update({level : [[i+1, None]]})
            else:
                func_intervals[level].append([i+1, None])
        elif c == "{" :
            if not (level in arg_intervals.keys()):
                arg_intervals.update({level : [[i+1, None]]})
            else:
                arg_intervals[level].append([i+1, None])
            if func_intervals[level][-1][1] == None:
                func_intervals[level][-1][1] = i
            level += 1
            last_close = i
        elif c == "}":
            level -= 1
            if level < 0: raise(ValueError(f"level less than 0 at {i} in {func}"))
            arg_intervals[level][-1][1] = i
            #append func to list if next char isn't an arg
            interval = None
            if i == len(func)-1 or (func[i+1] not in ['{']):
                func_list.append(math_node(func_intervals[level][-1], arg_intervals[level], level, func))
            last_close = i
        elif c in ['+', '-', '^']:
            if not (level in func_intervals.keys()):
                func_intervals.update({level : [[i, i+1]]})
            else:
                func_intervals[level].append([i+1])

            #find arg start
            if not (level in arg_intervals.keys()):
                arg_intervals.update({level : [[last_close+1, i]]})
            else:
                arg_intervals[level].append([last_close+1, i])
            #find arg end
            j = i
            while j < len(func):
                if func[j] == "}": break
                j += 1
            arg_intervals[level].append([i+1, j])

            print(arg_intervals[level])
            func_list.append(math_node(func_intervals[level][-1], arg_intervals[level], level, func))
        i += 1
        
    #relpace string args with nodes
    func_list.reverse()
    for i, func_obj in enumerate(func_list):
        assert type(func_obj) == math_node
        args = func_obj.arguments
        for i, arg in enumerate(args):
            if type(arg) != str:
                math_node(None, None, func_obj.level, arg, func_obj, leaf=True, data=arg)
                continue
            arg = arg.strip('\\')[:-1]
            child_node = [x for x in func_list if x.raw_str == arg]
            if len(child_node) > 0:
                #add parent
                child_node = child_node[0]
                assert type(child_node) == math_node
                child_node.parent = func_obj
                #add child
                func_obj.arguments[i] = child_node

    func_list[0].vizualize()
    print(func_intervals, '\n', arg_intervals)
    print(func_list)
    func_str = "1+1"
    y = eval(func_str)
    return y

if __name__ == "__main__":
    a = parser("\\frac{x^{2}}{\\frac{3}{2}}")
    print(a)

"""
if b == "infinity":
      x_vals = [e**j for j in range(0,n)]
Analytical method
Sources:
https://docs.python.org/3/library/functions.html#eval """

