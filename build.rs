use std::process::Stdio;


fn main()  {
    println!("Running build");
    let mut chid =std::process::Command::new("git")
    .arg("python")
    .arg("-m")
    .arg("pip")
    .arg("install")
    .arg("tensorflow")
    .arg("svgwrite")
    .stdout(Stdio::piped())
    .stderr(Stdio::piped())    
    .spawn().expect("Cant spawn pip");
    chid.wait().expect("pip failed");
}