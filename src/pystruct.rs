use core::f32;

use anyhow::Result;
use pyo3::{prelude::*, types::PyList};
use serde::{Serialize,Deserialize};
use svg::node::{Text, element::path::Data};

use crate::strokes::*;

#[derive(Clone)]
pub struct HandWritingGen {}

impl HandWritingGen {
    pub fn new(ensure_dep:bool,ensure_lib:bool) -> Result<HandWritingGen> {
        if ensure_dep{
            Self::ensure_dependencies()?;
        }
        if ensure_lib {
            Self::ensure_handwriter()?;
        }
        pyo3::prepare_freethreaded_python();
        Ok(HandWritingGen {})
    }

    pub fn ensure_dependencies() -> Result<()> {
        let mut chid = std::process::Command::new("python")
            .arg("-m")
            .arg("pip")
            .arg("install")
            .args(&["numpy", "tensorflow","tensorflow_probability", "sklearn", "svgwrite","matplotlib","pycairo","pandas"])
            .spawn()?;
        chid.wait()?;
        Ok(())
    }

    fn libpath()->String{
        std::env::var("HANDLIBPATH").unwrap_or("/tmp/hlib".to_string())
    }

    pub fn ensure_handwriter() -> Result<()> {
        let d = std::path::Path::new(&Self::libpath()).exists();
        if !d {
            let mut chid =std::process::Command::new("git")
            .arg("clone")
            .arg("https://89b81c9198c7975942f82cf05ecc040ded55051f@github.com/deep-gaurav/handwriter.git")
            .arg(&Self::libpath())
            .spawn()?;
            chid.wait()?;
            Ok(())
        } else {
            Ok(())
        }
    }

    pub fn gen_svg_and_stroke(
        &self,
        text: &str,
        style: u32,
        bias: f32,
        color: &str,
        width: f32,
    ) -> Result<(String,Stroke)> {
        Python::with_gil(|py| {
            
            let os = py.import("os")?;
            log::info!("changing to dir {}",Self::libpath());
            os.call("chdir",(&Self::libpath(),),None)?;
            log::info!("Adding {} to path",Self::libpath());
            let syspath: &PyList = py
                .import("sys")
                .unwrap()
                .get("path")
                .unwrap()
                .try_into()
                .unwrap();
            syspath.insert(0, &Self::libpath()).unwrap();
            log::info!("Importing demo");
            let demo = py.import("demo")?;
            log::info!("Running runStrokes");
            let c = demo.call("runStrokes", (text, style, bias, color, width), None)?;
            log::info!("Writing svg");
            let svg = Self::write_svg(c)?;
            let stroke = Self::get_stroke(c)?;
            Ok((svg,stroke))
        })
    }

    pub fn get_stroke(params: &PyAny) -> PyResult<Stroke> {
        let svg_paths: Vec<&PyAny> = params.get_item("svgpaths")?.extract()?;
            let mut strokes = vec![];
            for p in svg_paths.iter() {
                let ptype: String = p.get_item("type")?.extract()?;
                if ptype == "path" {
                    let mut path_segs = vec![];
                    let positions: Vec<&PyAny> = p.get_item("positions")?.extract()?;
                    for pos in positions.iter() {
                        let x: f32 = pos.get_item("x")?.extract()?;
                        let y: f32 = pos.get_item("y")?.extract()?;
                        if pos.get_item("type")?.extract::<&str>()? == "move" {
                            path_segs.push(PathType::Move(x,y));
                        } else {
                            path_segs.push(PathType::Line(x,y))
                        }
                    }
                    let color: &str = p.get_item("color")?.extract()?;
                    let width: f32 = p.get_item("width")?.extract()?;
                    let line_cap: &str = p.get_item("linecap")?.extract()?;
                    let fill: &str = p.get_item("fill")?.extract()?;
                    strokes.push(StrokeType::Path(StrokePath{
                        paths: path_segs,
                        fill: fill.to_string(),
                        stroke_color: color.to_string(),
                        line_cap: line_cap.to_string(),
                        stroke_width: width,

                    }));
                } else if ptype == "text" {
                    let content: &str = p.get_item("text")?.extract()?;
                    let fill: &str = p.get_item("fill")?.extract()?;
                    let x: f32 = p.get_item("x")?.extract()?;
                    let y: f32 = p.get_item("y")?.extract()?;
                    let font_color: &str = p.get_item("font-color")?.extract()?;
                    let font_size = p.get_item("font-size")?.extract()?;
                    let font_family: &str = p.get_item("font-family")?.extract()?;
                    strokes.push(StrokeType::Text(StrokeText{ x, y, content: content.to_string(), fill:fill.to_string(), font_color: font_color.to_string(), font_size, font_family: font_family.to_string()}));
                }
            }
            Ok(
                Stroke{
                    strokes
                }
            )
    }

    pub fn write_svg_fromstroke(params:Vec<Stroke>,width: f32,line_height:f32) ->Result<String,anyhow::Error> {
        let height = {
            (params.len()+1) as f32 *(3. * line_height / 4.)
        };
        let mut document = svg::Document::new().set("viewBox", (0, 0, width, height));

        for (line_num,line) in params.iter().enumerate(){
            for stroke in line.strokes.iter(){
                match stroke {
                    StrokeType::Path(path) => {
                        use svg::node::element::path::Data;
                        use svg::node::element::Path;
                        use svg::node::Text;
            
                        let mut data = Data::new();
                        for pos in path.paths.iter(){
                            match pos{
                                PathType::Move(x, y) => {
                                    let y = y+ (line_num as f32)*(3. * line_height / 4.);
                                    data = data.move_to((*x,y));
                                }
                                PathType::Line(x, y) => {
                                    let y = y+ (line_num as f32)*(3. * line_height / 4.);
                                    data = data.line_to((*x,y));
                                }
                            }
                        }
                        data = data.close();
                        let path = Path::new()
                        .set("d", data)
                        .set("fill", path.fill.to_string())
                        .set("stroke", path.stroke_color.to_string())
                        .set("linecap", path.line_cap.to_string())
                        .set("stroke-width", path.stroke_width);
                        document = document.add(path);
                    }
                    StrokeType::Text(text) => {
                        let text = svg::node::element::Text::new()
                            .set("fill", text.fill.to_string())
                            .set("x", text.x)
                            .set("y", text.y)
                            .set("font-color", text.font_color.to_string())
                            .set("font-size", text.font_size.to_string())
                            .set("font-family", text.font_family.to_string())
                            .add(Text::new(text.content.to_string()));
                        document = document.add(text);
                    }
                }
            }
        }

        let mut buff = vec![];
        svg::write(&mut buff, &document)?;
        let svgstring = std::str::from_utf8(&buff)?;
        println!("{}", svgstring);
        Ok(svgstring.to_string())
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
