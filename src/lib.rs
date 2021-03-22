cfg_if::cfg_if! {
    if #[cfg(feature = "pygen")] {
        pub mod pystruct;
    } else {
    }
}
pub mod strokes;