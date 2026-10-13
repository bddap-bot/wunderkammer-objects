const HIDDEN: [f32; 3] = [0.0, 0.0, 0.0];
const STILL: [f32; 4] = [0.0, 0.0, 0.0, 1.0];

fn around(radius: f32, y: f32, angle: f32) -> [f32; 3] {
    [radius * cos(angle), y, -radius * sin(angle)]
}

fn lerp(a: [f32; 3], b: [f32; 3], t: f32) -> [f32; 3] {
    [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]
}

/// How far a β subunit's lower domain swings out over its open, loose, tight cycle, one state per third of a turn.
fn openness(phase: f32) -> f32 {
    smoothstep(0.0, 0.3, phase) - 0.85 * smoothstep(0.75, 1.1, phase) - 0.15 * smoothstep(1.85, 2.2, phase)
}

fn show(node: usize, at: [f32; 3], facing: f32, size: f32) {
    if size > 0.0 {
        place(rest(node), at, turn([0.0, 1.0, 0.0], facing), [size; 3]);
    } else {
        set_scale(rest(node), HIDDEN);
    }
}

#[no_mangle]
pub extern "C" fn tick(time: f32, _x: f32, _y: f32, _z: f32, _touching: i32) -> i32 {
    let nm = scene::NM;
    let theta = TAU * time / scene::DURATION;
    set_rotation(rest(scene::ROTOR), turn([0.0, 1.0, 0.0], theta));

    let levers = [scene::BETA_1_LEVER, scene::BETA_2_LEVER, scene::BETA_3_LEVER];
    let ligands = [(scene::ATP_1, scene::ADP_1, scene::PHOSPHATE_1), (scene::ATP_2, scene::ADP_2, scene::PHOSPHATE_2), (scene::ATP_3, scene::ADP_3, scene::PHOSPHATE_3)];
    for k in 0..3 {
        let b = TAU * k as f32 / 3.0 + PI / 3.0;
        let phase = 3.0 * fract((theta - b) / TAU);
        set_rotation(rest(levers[k]), turn([sin(b), 0.0, cos(b)], scene::OPEN * openness(phase)));

        let facing = b - 0.4;
        let site = around(scene::HEAD_RADIUS + 1.1 * nm, scene::SITE_Y, facing);
        let outside = around(scene::HEAD_RADIUS + 6.0 * nm, scene::SITE_Y + 2.0 * nm, facing);
        let below = around(scene::HEAD_RADIUS + 5.0 * nm, scene::SITE_Y - 3.0 * nm, facing - 0.3);
        let chain_end = around(scene::HEAD_RADIUS + 1.1 * nm + 0.55 * nm * 3.4, scene::SITE_Y, facing);
        let waiting = around(scene::HEAD_RADIUS + 1.1 * nm + 0.55 * nm * 4.6, scene::SITE_Y - 0.4 * nm, facing);
        let (atp, adp, phosphate) = ligands[k];

        let leaving = smoothstep(0.0, 0.6, phase);
        let made = phase >= 2.5;
        if phase < 0.6 {
            show(atp, lerp(site, outside, leaving), facing, 1.0 - smoothstep(0.4, 0.6, phase));
        } else {
            show(atp, site, facing, if made { 1.0 } else { 0.0 });
        }
        let arriving = smoothstep(0.4, 1.0, phase);
        if made {
            show(adp, site, facing, 0.0);
            show(phosphate, chain_end, 0.0, 0.0);
        } else if phase < 1.0 {
            show(adp, lerp(outside, site, arriving), facing, smoothstep(0.4, 0.55, phase));
            show(phosphate, lerp(below, waiting, arriving), 0.0, smoothstep(0.4, 0.55, phase));
        } else {
            show(adp, site, facing, 1.0);
            show(phosphate, lerp(waiting, chain_end, smoothstep(2.0, 2.45, phase)), 0.0, 1.0);
        }
    }

    let delta = PI / scene::C_SUBUNITS;
    let channel = scene::RING + 1.3 * nm;
    let bound = scene::RING + 1.1 * nm;
    let n = scene::C_SUBUNITS as usize;
    for k in 0..n {
        let angle = theta + TAU * k as f32 / n as f32;
        let phi = TAU * fract(angle / TAU);
        let node = scene::PROTON_1 + k;
        if phi < delta {
            let u = phi / delta;
            show(node, lerp(around(channel, -3.0 * nm, delta), around(bound, 0.0, delta), u), 0.0, smoothstep(0.0, 0.3, u));
        } else if phi > TAU - delta {
            let u = (phi - (TAU - delta)) / delta;
            show(node, lerp(around(bound, 0.0, -delta), around(channel, 3.0 * nm, -delta), u), 0.0, 1.0 - smoothstep(0.7, 1.0, u));
        } else {
            show(node, around(bound, 0.0, angle), 0.0, 1.0);
        }
    }

    for k in 0..scene::AMBIENT as usize {
        let f = k as f32;
        let wobble = TAU * time / scene::DURATION;
        let x = -0.07 + 0.13 * fract(f * 0.618) + 0.008 * sin(wobble * (1.0 + (k % 3) as f32) + f);
        let z = -0.045 + 0.085 * fract(f * 0.382 + 0.2) + 0.008 * cos(wobble * (2.0 - (k % 2) as f32) + 2.0 * f);
        let y = -scene::HALF_MEMBRANE - 0.01 - 0.012 * fract(f * 0.73) + 0.003 * sin(wobble * 3.0 + f);
        place(rest(scene::AMBIENT_PROTON_1 + k), [x, y, z], STILL, [1.0; 3]);
    }
    publish()
}
