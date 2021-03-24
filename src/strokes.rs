use serde::{Serialize,Deserialize};

#[derive(Debug,Serialize,Deserialize,Clone,PartialEq)]
pub struct Stroke{
    pub strokes:Vec<StrokeType>
}

#[derive(Debug,Clone,Serialize,Deserialize,PartialEq)]
pub enum StrokeType{
    Path(StrokePath),
    Text(StrokeText),
}

#[derive(Debug,Clone,Serialize,Deserialize,PartialEq)]
pub struct StrokePath{
    pub paths:Vec<PathType>,
    pub fill:String,
    pub stroke_color:String,
    pub line_cap:String,
    pub stroke_width:f32,
}

#[derive(Debug,Clone,Serialize,Deserialize,PartialEq)]
pub struct StrokeText{
    pub x:f32,
    pub y:f32,
    pub content:String,
    pub fill:String,
    pub font_color:String,
    pub font_size:u32,
    pub font_family:String
}

#[derive(Debug,Clone,Serialize,Deserialize,PartialEq)]
pub enum PathType {
    Move(f32,f32),
    Line(f32,f32),
}

impl PathType {
    /// Returns `true` if the path_type is [`Line`].
    pub fn is_line(&self) -> bool {
        matches!(self, Self::Line(..))
    }

    /// Returns `true` if the path_type is [`Move`].
    pub fn is_move(&self) -> bool {
        matches!(self, Self::Move(..))
    }
}
