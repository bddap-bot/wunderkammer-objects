/// Live data sets how many decimal places apart the twin beads start, as in `{"digits":6}` or `6` (1 to 12; default 3), and starts a fresh pair from where the red bead is. The pair also restarts once the gap has spanned the attractor for six seconds; the blue bead fades out and back in at the red one.
const N: usize = scene::TRAIL_LENGTH as usize;
const SPEED: f64 = 0.6;
const STEP: f64 = 0.004;
const SAMPLE: f32 = 0.06;

struct State {
    red: [f64; 3],
    blue: [f64; 3],
    trails: [[[f32; 3]; N]; 2],
    head: usize,
    sampled: f32,
    last: f32,
    digits: f64,
    apart: f32,
    fading: f32,
    started: bool,
}

static mut STATE: State = State { red: [0.0; 3], blue: [0.0; 3], trails: [[[0.0; 3]; N]; 2], head: 0, sampled: 0.0, last: 0.0, digits: 3.0, apart: 0.0, fading: 0.0, started: false };

#[no_mangle]
pub extern "C" fn data(length: i32) -> i32 {
    receive(length)
}

fn flow(p: [f64; 3]) -> [f64; 3] {
    let (s, r, b) = (scene::SIGMA as f64, scene::RHO as f64, scene::BETA as f64);
    [s * (p[1] - p[0]), p[0] * (r - p[2]) - p[1], p[0] * p[1] - b * p[2]]
}

fn add(p: [f64; 3], k: [f64; 3], h: f64) -> [f64; 3] {
    [p[0] + k[0] * h, p[1] + k[1] * h, p[2] + k[2] * h]
}

fn step(p: [f64; 3], h: f64) -> [f64; 3] {
    let k1 = flow(p);
    let k2 = flow(add(p, k1, h / 2.0));
    let k3 = flow(add(p, k2, h / 2.0));
    let k4 = flow(add(p, k3, h));
    [0, 1, 2].map(|i| p[i] + h / 6.0 * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]))
}

fn drawn(p: [f64; 3]) -> [f32; 3] {
    let s = scene::SCALE;
    [p[0] as f32 * s, (p[2] as f32 - 25.0) * s, p[1] as f32 * s]
}

fn twin(red: [f64; 3], digits: f64) -> [f64; 3] {
    let mut gap = 1.0;
    for _ in 0..digits as i32 {
        gap /= 10.0;
    }
    [red[0] + gap, red[1], red[2]]
}

#[no_mangle]
pub extern "C" fn tick(time: f32, _x: f32, _y: f32, _z: f32, _touching: i32) -> i32 {
    let state = unsafe { &mut *core::ptr::addr_of_mut!(STATE) };
    if !state.started {
        state.started = true;
        state.red = [scene::START_X as f64, scene::START_Y as f64, scene::START_Z as f64];
        state.blue = twin(state.red, state.digits);
        let at = drawn(state.red);
        state.trails = [[at; N]; 2];
        state.last = time;
    }
    let (text, fresh) = inbox();
    if fresh {
        if let Some(digits) = number(text, b"") {
            state.digits = clamp(digits, 1.0, 12.0) as f64;
            state.fading = state.fading.max(0.001);
        }
    }
    let dt = clamp(time - state.last, 0.0, 0.1);
    state.last = time;

    let mut remaining = dt as f64 * SPEED;
    while remaining > 0.0 {
        let h = if remaining < STEP { remaining } else { STEP };
        state.red = step(state.red, h);
        state.blue = step(state.blue, h);
        remaining -= h;
    }

    let (red, mut blue) = (drawn(state.red), drawn(state.blue));
    let d = [blue[0] - red[0], blue[1] - red[1], blue[2] - red[2]];
    let length = sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
    state.apart = if length > 20.0 * scene::SCALE { state.apart + dt } else { 0.0 };
    if state.fading == 0.0 && state.apart > 6.0 {
        state.fading = 0.001;
    }
    if state.fading > 0.0 {
        let before = state.fading;
        state.fading += dt;
        if before < 0.6 && state.fading >= 0.6 {
            state.blue = twin(state.red, state.digits);
            blue = drawn(state.blue);
            state.trails[1] = [blue; N];
            state.apart = 0.0;
        }
        if state.fading >= 1.2 {
            state.fading = 0.0;
        }
    }
    let shown = if state.fading > 0.0 { (state.fading - 0.6).abs() / 0.6 } else { 1.0 };

    state.sampled += dt;
    if state.sampled >= SAMPLE {
        state.sampled = 0.0;
        state.head = (state.head + 1) % N;
        state.trails[0][state.head] = red;
        state.trails[1][state.head] = blue;
    }
    place(rest(scene::BEAD_RED), red, [0.0, 0.0, 0.0, 1.0], [1.0; 3]);
    place(rest(scene::BEAD_BLUE), blue, [0.0, 0.0, 0.0, 1.0], [shown; 3]);
    for (trail, first, size) in [(0, scene::TRAIL_RED_0, 1.0), (1, scene::TRAIL_BLUE_0, shown)] {
        for k in 0..N {
            let age = (state.head + N - k) % N;
            let fade = 1.0 - age as f32 / N as f32;
            place(rest(first + k), state.trails[trail][k], [0.0, 0.0, 0.0, 1.0], [size * fade; 3]);
        }
    }
    let gap = rest(scene::SEPARATION);
    if length > 1e-5 {
        place(gap, red, from_up([d[0] / length, d[1] / length, d[2] / length]), [shown, length * shown, shown]);
    } else {
        set_scale(gap, [0.0; 3]);
    }
    publish()
}
