use std::os::unix::prelude::CommandExt;

use anyhow::Result;
use pyo3::{prelude::*, types::PyList};

pub struct HandWritingGen {}

impl HandWritingGen {
    pub fn new() -> Result<HandWritingGen> {
        Self::ensure_dependencies()?;
        Self::ensure_handwriter()?;
        Ok(HandWritingGen {})
    }

    pub fn ensure_dependencies() -> Result<()> {
        let mut chid = std::process::Command::new("python")
            .arg("-m")
            .arg("pip")
            .arg("install")
            .args(&["numpy", "tensorflow","tensorflow_probability", "sklearn", "svgwrite","matplotlib","pandas"])
            .spawn()?;
        chid.wait()?;
        Ok(())
    }

    pub fn ensure_handwriter() -> Result<()> {
        let d = std::path::Path::new(env!("HANDLIBPATH")).exists();
        if !d {
            let mut chid =std::process::Command::new("git")
            .arg("clone")
            .arg("https://89b81c9198c7975942f82cf05ecc040ded55051f@github.com/deep-gaurav/handwriter.git")
            .arg(env!("HANDLIBPATH"))
            .spawn()?;
            chid.wait()?;
            Ok(())
        } else {
            Ok(())
        }
    }

    pub fn gen_svg(
        &self,
        text: &str,
        style: u32,
        bias: f32,
        color: &str,
        width: f32,
    ) -> Result<String> {
        Python::with_gil(|py| {
            let syspath: &PyList = py
                .import("sys")
                .unwrap()
                .get("path")
                .unwrap()
                .try_into()
                .unwrap();

            syspath.insert(0, env!("HANDLIBPATH")).unwrap();
            let demo = py.import("demo")?;
            let c = demo.call("runStrokes", (text, style, bias, color, width), None)?;
            Self::write_svg(c)
        })
        .map_err(|er| anyhow::anyhow!(er))
    }

    pub fn write_svg(params: &PyAny) -> PyResult<String> {
        let width: f32 = params.get_item("width")?.extract()?;

        let height: f32 = params.get_item("height")?.extract()?;
        let mut document = svg::Document::new().set("viewBox", (0, 0, width, height));

        let svg_paths: Vec<&PyAny> = params.get_item("svgpaths")?.extract()?;
        for p in svg_paths.iter() {
            let ptype: String = p.get_item("type")?.extract()?;

            use svg::node::element::path::Data;
            use svg::node::element::Path;
            use svg::node::Text;

            if ptype == "path" {
                let mut data = Data::new();
                let positions: Vec<&PyAny> = p.get_item("positions")?.extract()?;
                for pos in positions.iter() {
                    let x: f32 = pos.get_item("x")?.extract()?;
                    let y: f32 = pos.get_item("y")?.extract()?;
                    if pos.get_item("type")?.extract::<&str>()? == "move" {
                        data = data.move_to((x, y));
                    } else {
                        data = data.line_to((x, y));
                    }
                }
                data = data.close();
                let color: &str = p.get_item("color")?.extract()?;
                let width: f32 = p.get_item("width")?.extract()?;
                let line_cap: &str = p.get_item("linecap")?.extract()?;
                let fill: &str = p.get_item("fill")?.extract()?;
                let path = Path::new()
                    .set("d", data)
                    .set("fill", fill)
                    .set("stroke", color)
                    .set("fill", fill)
                    .set("linecap", line_cap)
                    .set("stroke-width", width);
                document = document.add(path);
            } else if ptype == "text" {
                let content: &str = p.get_item("text")?.extract()?;
                let fill: &str = p.get_item("fill")?.extract()?;
                let x: f32 = p.get_item("x")?.extract()?;
                let y: f32 = p.get_item("y")?.extract()?;
                let font_color: &str = p.get_item("font-color")?.extract()?;
                let font_size: &str = p.get_item("font-size")?.extract()?;
                let font_family: &str = p.get_item("font-family")?.extract()?;
                let text = svg::node::element::Text::new()
                    .set("fill", fill)
                    .set("x", x)
                    .set("y", y)
                    .set("font-color", font_color)
                    .set("font-size", font_size)
                    .set("font-family", font_family)
                    .add(Text::new(content));
                document = document.add(text);
            }
        }
        let mut buff = vec![];
        svg::write(&mut buff, &document)?;
        let svgstring = std::str::from_utf8(&buff)?;
        println!("{}", svgstring);
        Ok(svgstring.to_string())
    }
}
