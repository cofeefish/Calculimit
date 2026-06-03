"""
this file starts and manages the server
run with --dev for devmode
only works on windows
max howard, 5/28/2026
start tunnel with  "ngrok http 8080"  ->  https://ounce-thong-bankbook.ngrok-free.dev 
"""

from flask import Flask, request, render_template
from waitress import serve
import logging, os, sys, json, math
import calc, compile_tex

def get_parent(path: str) -> str :
    parent = os.path.split(path)[0]
    return parent

source_dir = get_parent(get_parent(os.path.abspath(__file__)))
temp_dir = f'{source_dir}/static/temp/'
log_path = f'{source_dir}/log.txt'

#########################################################################

app = Flask(__name__, static_folder=f'{source_dir}\\static', template_folder=f'{source_dir}\\templates')

def isfloat(val:str) -> bool:
    try:
        float(val)
        return True
    except ValueError:
        return False

@app.route('/')
def home_page():
    from decimal import Decimal
    request_args = request.args.to_dict()

    result="no input"
    points=[]
    points_json = "[]"
    converges = False
    expression = ""
    dest = Decimal('Infinity')
    num_samples = 100
    if request_args != {}:
        method = request_args["method"].strip().lower()
        x_val = request_args["x_value"].strip().lower()
        if x_val == '-infinity':
            dest = Decimal('-Infinity')
        elif isfloat(x_val):
            dest = Decimal(x_val)
        if "num_points" in request_args and request_args["num_points"].isdecimal():
            num_samples = int(request_args["num_points"])

        expression = request_args["expression"].strip().lower()
        if method == "latex":
            expression = compile_tex.tex_to_python(expression)
        print(f"method={method}, x_val={x_val}, dest={dest}, num_samples={num_samples}, expression={expression}")

        try:
            points, converges, reason = calc.find_limit(expression, num_samples, dest=dest)
        except ValueError as e:
            print(e)
            result = f"Error: {e}"
            points = []
            converges = False
            reason = ""
        #format result
        if points != []:
            points = [p.format(json=True) for p in points]
            # Point.format with json=True returns JSON-serializable values
            points_json = json.dumps(points)

            if converges:
                result = f'{expression} converges to {points[-1][-1]} \n because {reason}'
            else:
                result = f'{expression} diverges (or converges above {points[-1][-1]})  \n because {reason}'
        else:
            points_json = "[]"

    return render_template('home_page.html',expression=expression, x_value=str(dest), num_samples=num_samples, result=result, points_json=points_json, converges=converges, points=points)

@app.route('/restart', methods=['POST'])
def restart_server():
    return "Server restarted", 200

###############################################################################

def start_development_server():
    print("Starting development server...")
    app.run(host='0.0.0.0', port=8080, debug=True)

def start_production_server():
    print("Starting production server...")
    serve(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write('\n\n----- New Session -----\n')
    log_format = '%(asctime)s - %(levelname)s - %(message)s;'
    logging.basicConfig(filename=log_path, level=logging.INFO, format=log_format, force=True)

    if len(sys.argv) > 1 and sys.argv[1] == '--dev':
        start_development_server()
    else:
        start_production_server()