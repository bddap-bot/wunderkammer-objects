/// Live data names home and the far ends with their measured round trips, as in `{"home":[39.74,-104.99],"pings":[[51.51,-0.13,142.0],[35.68,139.69,98.5]]}`: latitude and longitude in degrees, round trip in milliseconds, up to eight. Until the first arrives it shows a made-up home and round trips of 1.6 times the fibre limit plus 4 ms.
const N: usize = scene::TARGET_COUNT as usize;
const DEGREE: f32 = PI / 180.0;
const DEMO_HOME: [f32; 2] = [39.74, -104.99];
const DEMO: [[f32; 2]; N] = [[39.04, -77.49], [51.51, -0.13], [50.11, 8.68], [35.68, 139.69], [1.35, 103.82], [-33.87, 151.21], [-23.55, -46.63], [-33.92, 18.42]];

struct State {
    last: f32,
    home: [f32; 3],
    home_goal: [f32; 3],
    ends: [[f32; 3]; N],
    goals: [[f32; 3]; N],
    rtt: [f32; N],
    shown: [f32; N],
    wanted: [bool; N],
    phase: [f32; N],
    started: bool,
}

static mut STATE: State = State { last: 0.0, home: [0.0, 0.0, 1.0], home_goal: [0.0, 0.0, 1.0], ends: [[0.0, 0.0, 1.0]; N], goals: [[0.0, 0.0, 1.0]; N], rtt: [100.0; N], shown: [0.0; N], wanted: [false; N], phase: [0.0; N], started: false };

#[no_mangle]
pub extern "C" fn data(length: i32) -> i32 {
    receive(length)
}

/// Up to `out.len()` numbers after `key`, in order, skipping whatever separates them.
fn numbers(bytes: &[u8], key: &[u8], out: &mut [f32]) -> usize {
    let Some(start) = bytes.windows(key.len()).position(|window| window == key) else { return 0 };
    let mut rest = &bytes[start + key.len()..];
    let mut count = 0;
    while count < out.len() {
        let Some(at) = rest.iter().position(|b| b.is_ascii_digit() || *b == b'-') else { break };
        rest = &rest[at..];
        let Some(value) = number(rest, b"") else { break };
        out[count] = value;
        count += 1;
        let end = rest.iter().skip(1).position(|b| !(b.is_ascii_digit() || *b == b'.')).map_or(rest.len(), |p| p + 1);
        rest = &rest[end..];
    }
    count
}

fn unit(lat: f32, lon: f32) -> [f32; 3] {
    let (lat, lon) = (lat * DEGREE, lon * DEGREE);
    [cos(lat) * sin(lon), sin(lat), cos(lat) * cos(lon)]
}

fn dot(a: [f32; 3], b: [f32; 3]) -> f32 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}

fn normalized(a: [f32; 3]) -> [f32; 3] {
    let n = sqrt(dot(a, a)).max(1e-6);
    [a[0] / n, a[1] / n, a[2] / n]
}

fn toward(a: [f32; 3], b: [f32; 3], k: f32) -> [f32; 3] {
    normalized([a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k])
}

fn angle_between(a: [f32; 3], b: [f32; 3]) -> f32 {
    let c = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    atan2(sqrt(dot(c, c)), dot(a, b))
}

fn fibre_rtt(a: [f32; 3], b: [f32; 3]) -> f32 {
    2.0 * angle_between(a, b) * scene::EARTH_KM / scene::FIBRE_KM_PER_MS
}

/// The point a fraction `s` along the great circle from `a` to `b`, lifted off the surface in proportion to the distance.
fn arc(a: [f32; 3], b: [f32; 3], s: f32) -> [f32; 3] {
    let omega = angle_between(a, b);
    let p = if omega < 1e-4 {
        a
    } else {
        let (wa, wb) = (sin((1.0 - s) * omega) / sin(omega), sin(s * omega) / sin(omega));
        normalized([a[0] * wa + b[0] * wb, a[1] * wa + b[1] * wb, a[2] * wa + b[2] * wb])
    };
    let r = scene::RADIUS * (1.012 + 0.32 * omega / PI * sin(PI * s));
    [p[0] * r, p[1] * r, p[2] * r]
}

fn stand(node: usize, at: [f32; 3], size: f32) {
    place(rest(node), [at[0] * scene::RADIUS, at[1] * scene::RADIUS, at[2] * scene::RADIUS], from_up(at), [size; 3]);
}

#[no_mangle]
pub extern "C" fn tick(time: f32, _x: f32, _y: f32, _z: f32, _touching: i32) -> i32 {
    let state = unsafe { &mut *core::ptr::addr_of_mut!(STATE) };
    if !state.started {
        state.started = true;
        state.home_goal = unit(DEMO_HOME[0], DEMO_HOME[1]);
        state.home = state.home_goal;
        for t in 0..N {
            state.goals[t] = unit(DEMO[t][0], DEMO[t][1]);
            state.ends[t] = state.goals[t];
            state.rtt[t] = 1.6 * fibre_rtt(state.home, state.goals[t]) + 4.0;
            state.wanted[t] = true;
        }
        state.last = time;
    }
    let (text, fresh) = inbox();
    if fresh {
        let mut home = [0.0; 2];
        if numbers(text, b"home", &mut home) == 2 {
            state.home_goal = unit(home[0], home[1]);
        }
        let mut pings = [0.0; 3 * N];
        let count = numbers(text, b"pings", &mut pings) / 3;
        if count > 0 {
            for t in 0..N {
                state.wanted[t] = t < count;
                if t < count {
                    state.goals[t] = unit(pings[3 * t], pings[3 * t + 1]);
                    state.rtt[t] = pings[3 * t + 2].max(0.5);
                }
            }
        }
    }
    let dt = clamp(time - state.last, 0.0, 0.1);
    state.last = time;
    let ease = clamp(dt * 2.0, 0.0, 1.0);
    state.home = toward(state.home, state.home_goal, ease);

    let lat = atan2(state.home[1], sqrt(state.home[0] * state.home[0] + state.home[2] * state.home[2]));
    let lon = atan2(state.home[0], state.home[2]);
    let sway = 0.25 * sin(time * 0.15);
    let facing = compose(turn([1.0, 0.0, 0.0], lat - 25.0 * DEGREE), turn([0.0, 1.0, 0.0], -lon + sway));
    set_rotation(rest(scene::GLOBE), facing);
    stand(scene::HOME, state.home, 1.3);

    for t in 0..N {
        let goal = if state.wanted[t] { 1.0 } else { 0.0 };
        state.shown[t] += (goal - state.shown[t]) * ease;
        state.ends[t] = toward(state.ends[t], state.goals[t], ease);
        let (home, end, shown) = (state.home, state.ends[t], state.shown[t]);
        let first = scene::TARGET_0_PIN + t * (scene::TARGET_1_PIN - scene::TARGET_0_PIN);
        stand(first, end, shown);
        for b in 0..scene::ARC_BEADS as usize {
            let s = (b as f32 + 0.5) / scene::ARC_BEADS;
            place(rest(first + 2 + b), arc(home, end, s), [0.0, 0.0, 0.0, 1.0], [shown; 3]);
        }
        let cycle = state.rtt[t] * scene::SLOW;
        state.phase[t] = fract(state.phase[t] + dt / cycle);
        let u = state.phase[t];
        let packet = 1.0 - (2.0 * u - 1.0).abs();
        place(rest(first + 2 + scene::ARC_BEADS as usize), arc(home, end, packet), [0.0, 0.0, 0.0, 1.0], [shown; 3]);
        let v = u * cycle / (fibre_rtt(home, end) * scene::SLOW).max(1e-3);
        let light = if v < 1.0 { 1.0 - (2.0 * v - 1.0).abs() } else { 0.0 };
        let glow = smoothstep(0.0, 0.04, v) * (1.0 - smoothstep(1.0, 1.12, v));
        place(rest(first + 3 + scene::ARC_BEADS as usize), arc(home, end, light), [0.0, 0.0, 0.0, 1.0], [shown * glow; 3]);
    }
    publish()
}
