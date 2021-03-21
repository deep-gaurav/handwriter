
use handwriter::HandWritingGen;

fn main() -> Result<(),anyhow::Error> {
    let h = crate::HandWritingGen::new()?;
    let svg =h.gen_svg("Test", 1, 0.75, "green", 1.5);
    println!("{:#?}",svg);
    Ok(())
}