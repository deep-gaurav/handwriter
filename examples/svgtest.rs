
use handwriter::HandWritingGen;

fn main() -> Result<(),anyhow::Error> {
    let h = crate::HandWritingGen::new(true,true)?;
    let svg =h.gen_svg_and_stroke("Test", 1, 0.75, "green", 1.5);
    println!("{:#?}",svg);
    Ok(())
}