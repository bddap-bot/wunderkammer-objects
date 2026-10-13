const HIDDEN: [f32; 3] = [0.0, 0.0, 0.0];
const STILL: [f32; 4] = [0.0, 0.0, 0.0, 1.0];

fn lerp(a: [f32; 3], b: [f32; 3], t: f32) -> [f32; 3] {
    [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]
}

fn along(points: &[[f32; 3]], p: f32) -> [f32; 3] {
    let legs = (points.len() - 1) as f32;
    let at = clamp(p * legs, 0.0, legs - 1e-4);
    let leg = floor(at) as usize;
    lerp(points[leg], points[leg + 1], at - leg as f32)
}

fn position(node: usize) -> [f32; 3] {
    let r = scene::REST[node];
    [r[0], r[1], r[2]]
}

fn oxidise(first: usize, n: usize, f: f32) {
    let node = first + 2 * n;
    set_scale(rest(node), [1.0 - smoothstep(0.85, 1.0, f); 3]);
    set_scale(rest(node + 1), [1.08 * f; 3]);
}

#[no_mangle]
pub extern "C" fn tick(time: f32, _x: f32, _y: f32, _z: f32, _touching: i32) -> i32 {
    let time = scene::DURATION * fract(time / scene::DURATION);
    let half = scene::DURATION / 2.0;
    let charged = if time < half { time } else { scene::DURATION - time };
    let (q, face) = (scene::QUARTER, scene::FACE);
    for i in 0..8 {
        let p = smoothstep(0.25 + i as f32 * 0.95, 1.1 + i as f32 * 0.95, charged);
        let home = position(scene::NA_1 + i);
        let [_, y, z] = home;
        let park = [scene::PARK_X + if i < 4 { scene::PARK_STEP } else { 0.0 }, y, z];
        let at = if i < 4 { along(&[home, [face, y, z], park], p) } else { along(&[home, [0.0, y, z], [q, y, z], [face, y, z], park], p) };
        place(rest(scene::NA_1 + i), at, STILL, [1.0; 3]);

        let (first, sites, group) = if i < 4 { (scene::FE_HS_0, scene::HIGH_SPIN as usize, i) } else { (scene::FE_LS_0, scene::LOW_SPIN as usize, i - 4) };
        let (from, to) = (group * sites / 4, (group + 1) * sites / 4);
        for n in from..to {
            oxidise(first, n, p);
        }
        let start = position(first + 2 * from);
        let electron = rest(scene::ELECTRON_1 + i);
        if p > 0.0 && p < 1.0 {
            let travel = smoothstep(0.15, 1.0, p);
            let size = smoothstep(0.1, 0.25, p) * (1.0 - smoothstep(0.85, 1.0, p));
            place(electron, lerp(start, [scene::COLLECTOR_X, start[1], start[2]], travel), STILL, [size; 3]);
        } else {
            set_scale(electron, HIDDEN);
        }
    }
    publish()
}
