const graph_canvas = document.getElementById("graph-display")
const graph_data = document.getElementById("graph-data")
const points = JSON.parse(graph_data?.dataset?.points || "[]")
const converges = (graph_data?.dataset?.converges || "false") === "true"
const graph_type_radios = document.getElementsByName("graph-type")
for (const radio of graph_type_radios){
    radio.addEventListener('change', draw_graph)
}
function parseNumberOrInfinity(v){
    if (typeof v === 'string'){
        if (v === 'Infinity') return Infinity
        if (v === '-Infinity') return -Infinity
        if (v === 'NaN') return NaN
    }
    return Number(v)
}
function formatNumberForDisplay(num){
    if (num === Infinity) return '∞'
    if (num === -Infinity) return '-∞'
    if (Math.abs(num) >= 1e6 || Math.abs(num) <= 1e-6){
        return num.toExponential(2)
    }
    return num.toFixed(2)
}

const foreground = window.getComputedStyle(document.body ,null).getPropertyValue('color');
const foreground2 = window.getComputedStyle(document.body ,null).getPropertyValue('--color-foreground2');
const font_size = parseFloat(window.getComputedStyle(document.body ,null).getPropertyValue('font-size'));
const scale_factor = 2

function draw_graph(){
    //constants
    const graph_display_width = graph_canvas.getBoundingClientRect().width;
    const graph_display_height = graph_canvas.getBoundingClientRect().height;
    graph_canvas.style.width = graph_display_width + "px";
    graph_canvas.style.height = graph_display_height + "px";
    graph_canvas.width = Math.round(graph_display_width * scale_factor);
    graph_canvas.height = Math.round(graph_display_height * scale_factor);
    //setup
    const background = window.getComputedStyle(document.body ,null).getPropertyValue('background-color');
    const ctx = graph_canvas.getContext('2d')
    ctx.lineCap = "round";
    ctx.fillStyle = background
    ctx.fillRect(0,0,graph_canvas.width,graph_canvas.height)
    ctx.fillStyle = foreground
    ctx.font = String(font_size) + "px Arial";
    ctx.strokeStyle = foreground
    ctx.lineWidth = 1
    ctx.stroke()
    //
    let x_values = []
    let y_values = []
    let valid_points_indices = []  // Track original indices of valid points
    if (graph_type_radios[0].checked) {
        //convert points to log scale
        for (let i = 0; i < points.length; i++){
            const point = points[i]
            const x_num = parseNumberOrInfinity(point[0])
            const y_num = parseNumberOrInfinity(point[1])
            if (!Number.isFinite(x_num) || !Number.isFinite(y_num)) {
                console.warn('Skipping invalid point:', point)
                continue
            }
            valid_points_indices.push(i)
            x_values.push(Math.sign(x_num) * Math.log(1 + Math.abs(x_num)));
            y_values.push(Math.sign(y_num) * Math.log(1 + Math.abs(y_num)));
        }
    } else {
        //linear scale
        for (let i = 0; i < points.length; i++){
            const point = points[i]
            const x_num = parseNumberOrInfinity(point[0])
            const y_num = parseNumberOrInfinity(point[1])
            if (!Number.isFinite(x_num) || !Number.isFinite(y_num)) {
                console.warn('Skipping invalid point:', point)
                continue
            }
            valid_points_indices.push(i)
            x_values.push(x_num);
            y_values.push(y_num);
        }
    }

    if (x_values.length === 0 || y_values.length === 0) {
        console.warn('No valid points to draw')
        return
    }
    const x_min = Math.min(...x_values);
    const x_max = Math.max(...x_values);
    let x_range = x_max - x_min;
    const y_min = Math.min(...y_values);
    const y_max = Math.max(...y_values);
    let y_range = y_max - y_min;
    if (x_range === 0) x_range = 1
    if (y_range === 0) y_range = 1
    ctx.beginPath();
    const px_coords = []
    for (let valid_idx = 0; valid_idx < x_values.length; valid_idx++){
        let x = x_values[valid_idx];
        let y = y_values[valid_idx];
        //scale each point as a percentage of range
        x = (x-x_min)/x_range
        y = (y-y_min)/y_range
        //convert to canvas coordinates
        x = x * graph_canvas.width
        y = (1-y) * graph_canvas.height
        px_coords.push([x,y])
        if (valid_idx == 0){
            ctx.moveTo(x,y)
        }
        else{
            // Check if there's a discontinuity (NaN point) between this and the last valid point
            const prev_original_idx = valid_points_indices[valid_idx - 1]
            const current_original_idx = valid_points_indices[valid_idx]
            
            // If there are points skipped between them, there's a discontinuity
            if (current_original_idx - prev_original_idx > 1) {
                ctx.stroke()  // Draw the current line segment
                ctx.beginPath()  // Start a new line segment
                ctx.moveTo(x, y)
            } else {
                ctx.lineTo(x, y)
            }
        }
    }
    ctx.stroke()  // Stroke any remaining path

    // draw point markers
    ctx.fillStyle = foreground
    for (let i = 0; i < px_coords.length; i++){
        const [px, py] = px_coords[i]
        ctx.beginPath()
        ctx.arc(px, py, Math.max(2, 3 * scale_factor), 0, Math.PI * 2)
        ctx.fill()
    }
    // label graph bounds
    ctx.fillStyle = foreground2
    ctx.font = String(font_size) + "px Arial";
    ctx.fillText(formatNumberForDisplay(Math.exp(x_min)), 10, graph_canvas.height/2 - 10)
    ctx.fillText(formatNumberForDisplay(Math.exp(x_max)), graph_canvas.width - 70, graph_canvas.height/2 - 10)
    ctx.fillText(formatNumberForDisplay(Math.exp(y_max)), graph_canvas.width/2 + 10, 20)
    ctx.fillText(formatNumberForDisplay(Math.exp(y_min)), graph_canvas.width/2 + 10, graph_canvas.height - 10)
    //draw axes
    if (y_min < 0 && y_max > 0){
        const y_axis_x = (-x_min/x_range) * graph_canvas.width
        ctx.beginPath()
        ctx.moveTo(y_axis_x, 0)
        ctx.lineTo(y_axis_x, graph_canvas.height)
        ctx.strokeStyle = foreground2
        ctx.lineWidth = 1 * scale_factor
        ctx.stroke()
    }
    if (x_min < 0 && x_max > 0){
        const x_axis_y = (1 - (-y_min/y_range)) * graph_canvas.height
        ctx.beginPath()
        ctx.moveTo(0, x_axis_y)
        ctx.lineTo(graph_canvas.width, x_axis_y)
        ctx.strokeStyle = foreground2
        ctx.lineWidth = 1 * scale_factor
        ctx.stroke()
    } 
    
}

window.onload  = function() {
    draw_graph()
}
