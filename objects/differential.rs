/// Live data sets the two numbers to add, in tenths of a turn, as in `{"a":3,"b":4}` or `a=2.5 b=-1`; without data, 3 and 4. Each loop turns A in, then B, holds the sum, and turns both back.
static mut STATE: [f32; 5] = [3.0, 4.0, 3.0, 4.0, 0.0];

#[no_mangle]
pub extern "C" fn data(length: i32) -> i32 {
    receive(length)
}

#[no_mangle]
pub extern "C" fn tick(time: f32, _x: f32, _y: f32, _z: f32, _touching: i32) -> i32 {
    let [goal_a, goal_b, shown_a, shown_b, last] = unsafe { &mut *core::ptr::addr_of_mut!(STATE) };
    let (text, fresh) = inbox();
    if fresh {
        if let Some(a) = number(text, b"a") {
            *goal_a = a;
        }
        if let Some(b) = number(text, b"b") {
            *goal_b = b;
        }
    }
    let ease = clamp(clamp(time - *last, 0.0, 0.1) * 2.0, 0.0, 1.0);
    *last = time;
    *shown_a += (*goal_a - *shown_a) * ease;
    *shown_b += (*goal_b - *shown_b) * ease;

    let time = scene::DURATION * fract(time / scene::DURATION);
    let unit = TAU / 10.0;
    let a = *shown_a * unit * (smoothstep(0.5, 2.5, time) - smoothstep(8.5, 10.5, time));
    let b = *shown_b * unit * (smoothstep(3.0, 5.0, time) - smoothstep(9.0, 11.5, time));
    let cage = (a + b) / 2.0;
    let spin = (a - b) / 2.0;
    let x = [1.0, 0.0, 0.0];
    set_rotation(rest(scene::INPUT_A), turn(x, a));
    set_rotation(rest(scene::INPUT_B), turn(x, b));
    set_rotation(rest(scene::CARRIER), turn(x, cage));
    set_rotation(rest(scene::SPIDER_TOP), turn([0.0, 1.0, 0.0], spin));
    set_rotation(rest(scene::SPIDER_BOTTOM), turn([0.0, 1.0, 0.0], -spin));
    set_rotation(rest(scene::IDLER), turn(x, -cage * scene::RING_RATIO));
    set_rotation(rest(scene::OUTPUT), turn(x, cage * scene::RING_RATIO));
    set_rotation(rest(scene::DIAL_A), turn(x, -a));
    set_rotation(rest(scene::DIAL_B), turn(x, -b));
    set_rotation(rest(scene::DIAL_SUM), turn(x, -cage * scene::RING_RATIO));
    publish()
}
