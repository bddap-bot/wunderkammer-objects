/// Live data is the host's device feed, laid out as OBJECTS.md's "Device feed" says; until the first arrives the panel stays empty.
const SAMPLE: usize = 40;
const CORE: usize = 12;
const PROCESS: usize = 28;

struct State {
    samples: usize,
    cpu: [f32; scene::HISTORY as usize],
    gpu: [f32; scene::HISTORY as usize],
    gpu_memory: [f32; scene::HISTORY as usize],
}

static mut STATE: State = State { samples: 0, cpu: [0.0; scene::HISTORY as usize], gpu: [0.0; scene::HISTORY as usize], gpu_memory: [0.0; scene::HISTORY as usize] };

#[no_mangle]
pub extern "C" fn data(length: i32) -> i32 {
    receive(length)
}

fn word(bytes: &[u8], at: usize) -> usize {
    match bytes.get(at..at + 4) {
        Some(b) => u32::from_le_bytes([b[0], b[1], b[2], b[3]]) as usize,
        None => 0,
    }
}

fn float(bytes: &[u8], at: usize) -> f32 {
    let value = match bytes.get(at..at + 4) {
        Some(b) => f32::from_le_bytes([b[0], b[1], b[2], b[3]]),
        None => 0.0,
    };
    if value.is_finite() { value } else { 0.0 }
}

fn ratio(part: f32, whole: f32) -> f32 {
    if whole > 0.0 { clamp(part / whole, 0.0, 1.0) } else { 0.0 }
}

fn shown(on: bool) -> [f32; 3] {
    if on { [1.0; 3] } else { [0.0; 3] }
}

fn push(history: &mut [f32; scene::HISTORY as usize], value: f32) {
    history.copy_within(1.., 0);
    history[history.len() - 1] = value;
}

fn glyph(byte: u8) -> usize {
    let upper = byte.to_ascii_uppercase();
    match scene::CHARSET.iter().position(|&c| c as u8 == upper) {
        Some(at) => at,
        None => scene::QUESTION as usize,
    }
}

fn history(first: usize, values: &[f32], filled: usize, height: f32) {
    let empty = values.len() - filled.min(values.len());
    for (i, &value) in values.iter().enumerate() {
        set_scale(rest(first + i), [1.0, if i < empty { 0.0 } else { clamp(value, 0.0, 1.0) * height }, 1.0]);
    }
}

fn heat(node: usize, celsius: f32) {
    let filled = if celsius > 0.0 { ratio(celsius - scene::COOLEST, scene::HOTTEST - scene::COOLEST).max(0.04) } else { 0.0 };
    set_scale(rest(node), [scene::THERMOMETER, filled * scene::GRAPH_HEIGHT, 1.0]);
}

#[no_mangle]
pub extern "C" fn tick(_time: f32, _x: f32, _y: f32, _z: f32, _touching: i32) -> i32 {
    let (bytes, fresh) = inbox();
    if !fresh || bytes.len() < SAMPLE {
        return 0;
    }
    let state = unsafe { &mut *core::ptr::addr_of_mut!(STATE) };
    let (cores, processes) = (word(bytes, 0), word(bytes, 4));
    let field = |at: usize| float(bytes, 8 + at * 4);
    let (memory_total, memory_available, gpu_busy, gpu_memory, gpu_clock, gpu_most, cpu_heat, gpu_heat) = (field(0), field(1), field(2), field(3), field(4), field(5), field(6), field(7));
    let core_at = |core: usize, at: usize| float(bytes, SAMPLE + core * CORE + at * 4);

    let mut total = 0.0;
    for core in 0..cores {
        total += core_at(core, 0);
    }
    push(&mut state.cpu, if cores > 0 { total / cores as f32 } else { 0.0 });
    push(&mut state.gpu, gpu_busy);
    push(&mut state.gpu_memory, ratio(gpu_memory, memory_total));
    state.samples += 1;
    history(scene::CPU_COLUMN0, &state.cpu, state.samples, scene::GRAPH_HEIGHT);
    history(scene::GPU_COLUMN0, &state.gpu, state.samples, scene::GRAPH_HEIGHT);
    let empty = state.gpu_memory.len() - state.samples.min(state.gpu_memory.len());
    for (i, &value) in state.gpu_memory.iter().enumerate() {
        let record = rest(scene::GPU_MEMORY0 + i);
        set_translation(record, [record[0], value * scene::GRAPH_HEIGHT, record[2]]);
        set_scale(record, shown(i >= empty));
    }
    let record = rest(scene::GPU_CLOCK);
    set_translation(record, [record[0], ratio(gpu_clock, gpu_most) * scene::GRAPH_HEIGHT, record[2]]);
    set_scale(record, shown(gpu_most > 0.0));
    heat(scene::CPU_HEAT, cpu_heat);
    heat(scene::GPU_HEAT, gpu_heat);

    let core_stride = scene::CORE1 - scene::CORE0;
    for core in 0..scene::CORES as usize {
        let present = core < cores;
        let busy = if present { core_at(core, 0) } else { 0.0 };
        set_scale(rest(scene::CORE0_BUSY + core * core_stride), [1.0, clamp(busy, 0.0, 1.0) * scene::CORE_HEIGHT, 1.0]);
        let (clock, most) = if present { (core_at(core, 1), core_at(core, 2)) } else { (0.0, 0.0) };
        let record = rest(scene::CORE0_CLOCK + core * core_stride);
        set_translation(record, [record[0], ratio(clock, most) * scene::CORE_HEIGHT, record[2]]);
        set_scale(record, shown(most > 0.0));
    }

    let used = memory_total - memory_available;
    set_scale(rest(scene::MEMORY_USED), [ratio(used, memory_total) * scene::MEMORY_WIDTH, scene::REST[scene::MEMORY_USED][8], 1.0]);
    set_scale(rest(scene::MEMORY_GPU), [ratio(gpu_memory.min(used), memory_total) * scene::MEMORY_WIDTH, scene::REST[scene::MEMORY_GPU][8], 1.0]);

    let row_stride = scene::ROW1 - scene::ROW0;
    let char_stride = scene::ROW0_CHAR1 - scene::ROW0_CHAR0;
    let start = SAMPLE + cores * CORE;
    for row in 0..scene::ROWS as usize {
        let present = row < processes && bytes.len() >= start + (row + 1) * PROCESS;
        let at = start + row * PROCESS;
        let name = if present { &bytes[at + 12..at + PROCESS] } else { &[][..] };
        for c in 0..scene::CHARS as usize {
            let letter = match name.get(c) {
                Some(&byte) if byte != 0 => glyph(byte),
                _ => scene::SPACE as usize,
            };
            for d in 0..35 {
                let bits = scene::FONT[letter * 7 + d / 5] as u32;
                let on = bits & (1 << (4 - d % 5)) != 0;
                set_scale(rest(scene::ROW0_CHAR0_DOT0 + row * row_stride + c * char_stride + d), shown(on));
            }
        }
        let values = if present { [ratio(float(bytes, at), cores as f32), ratio(float(bytes, at + 4), memory_total), clamp(float(bytes, at + 8), 0.0, 1.0)] } else { [0.0; 3] };
        for (b, value) in values.into_iter().enumerate() {
            let fill = [scene::ROW0_FILL0, scene::ROW0_FILL1, scene::ROW0_FILL2][b] + row * row_stride;
            set_scale(rest(fill), [value * scene::BAR_WIDTH, scene::REST[fill][8], 1.0]);
        }
    }
    publish()
}
