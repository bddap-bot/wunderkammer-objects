const HIDDEN: [f32; 3] = [0.0, 0.0, 0.0];

fn fade(p: f32) -> f32 {
    smoothstep(0.0, 0.08, p) * (1.0 - smoothstep(0.9, 1.0, p))
}

fn core_radius(x: f32) -> f32 {
    let stations = [
        (scene::INLET, scene::R_LPC + 0.006),
        (scene::SPLITTER, scene::R_LPC),
        (scene::HPC_IN, scene::R_HPC_IN),
        (scene::HPC_OUT, scene::R_HPC_OUT),
        (scene::BURN, scene::R_BURN),
        (scene::LPT_OUT, scene::R_LPT),
        (scene::EXIT, scene::R_LPT - 0.004),
    ];
    for pair in stations.windows(2) {
        let ((x0, r0), (x1, r1)) = (pair[0], pair[1]);
        if x <= x1 {
            return r0 + (r1 - r0) * clamp((x - x0) / (x1 - x0), 0.0, 1.0);
        }
    }
    stations[stations.len() - 1].1
}

fn around(x: f32, r: f32, angle: f32) -> [f32; 3] {
    [x, r * cos(angle), r * sin(angle)]
}

#[no_mangle]
pub extern "C" fn tick(time: f32, _x: f32, _y: f32, _z: f32, _touching: i32) -> i32 {
    let loop_fraction = time / scene::DURATION;
    set_rotation(rest(scene::LP_SPOOL), turn([1.0, 0.0, 0.0], scene::LP_TURNS * TAU * loop_fraction));
    set_rotation(rest(scene::HP_SPOOL), turn([1.0, 0.0, 0.0], scene::HP_TURNS * TAU * loop_fraction));

    let flicker = 1.0 + 0.06 * sin(time * TAU * 5.0) + 0.04 * sin(time * TAU * 13.0);
    let flame = rest(scene::FLAME);
    let size = flame[7];
    set_scale(flame, [size, size * flicker, size * flicker]);

    let n = scene::BYPASS_BEADS as usize;
    for k in 0..n {
        let p = fract(k as f32 / n as f32 + scene::BYPASS_LAPS * loop_fraction);
        let x = scene::INLET + p * (scene::BYPASS_END - scene::INLET);
        let r = scene::BYPASS_INNER + (scene::BYPASS_OUTER - scene::BYPASS_INNER) * fract(k as f32 * 0.618);
        let record = rest(scene::BYPASS_AIR_0 + k);
        set_translation(record, around(x, r, k as f32 * 2.39996));
        set_scale(record, [fade(p); 3]);
    }

    let n = scene::CORE_BEADS as usize;
    for k in 0..n {
        let p = fract(k as f32 / n as f32 + scene::CORE_LAPS * loop_fraction);
        let x = scene::INLET + p * (scene::EXIT - scene::INLET);
        let at = around(x, core_radius(x), k as f32 * TAU / n as f32 + 0.5 + p * 2.0);
        let hot = smoothstep(scene::BURN - 0.004, scene::BURN + 0.004, x);
        let cold = rest(scene::CORE_AIR_0 + k);
        place(cold, at, [0.0, 0.0, 0.0, 1.0], [fade(p) * (1.0 - hot) * 1.3; 3]);
        let burnt = rest(scene::CORE_GAS_0 + k);
        if hot > 0.0 {
            place(burnt, at, [0.0, 0.0, 0.0, 1.0], [fade(p) * hot * 1.3; 3]);
        } else {
            set_scale(burnt, HIDDEN);
        }
    }
    publish()
}
