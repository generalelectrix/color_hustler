use std::{
    error::Error,
    thread::sleep,
    time::{Duration, Instant},
};

use midir::{MidiIO, MidiInput, MidiInputConnection, MidiOutput, MidiOutputConnection, SendError};
use std::sync::mpsc::{channel, Receiver, Sender};

const DELAY: Duration = Duration::from_micros(3000);

fn main() -> Result<(), Box<dyn Error>> {
    let (inputs, outputs) = list_ports()?;
    println!("Inputs: {:?}\nOutputs: {:?}", inputs, outputs);
    let (send, recv) = channel();

    let input = Input::new("IAC Driver Bus 1".to_string(), send)?;

    let mut output = Output::new("Network Network Session 1".to_string())?;

    let mut last_sent = Instant::now();
    let mut buffer: Option<Vec<u8>> = None;
    loop {
        let now = Instant::now();
        if let Some(ref buf) = buffer {
            if now.duration_since(last_sent) >= DELAY {
                // println!("Sending {:?}", buf);
                if let Err(err) = output.send(buf) {
                    println!("Message send error: {}", err);
                }
                last_sent = Instant::now();
                buffer = None;
            } else {
                let time_to_next_send = (last_sent + DELAY).duration_since(now);
                // println!("Sleep {:?}", time_to_next_send);
                sleep(time_to_next_send);
            }
            continue;
        }
        buffer = Some(recv.recv()?);
        // println!("Receieved buffer: {:?}", buffer);
    }
}

fn get_named_port<T: MidiIO>(source: &T, name: &str) -> T::Port {
    for port in source.ports() {
        if let Ok(this_name) = source.port_name(&port) {
            if this_name == name {
                return port;
            }
        }
    }
    panic!("no port found with name {}", name);
}

pub struct Output {
    conn: MidiOutputConnection,
}

impl Output {
    pub fn new(name: String) -> Result<Self, Box<dyn Error>> {
        let output = MidiOutput::new("spreader")?;
        let port = get_named_port(&output, &name);
        let conn = output.connect(&port, &name)?;
        Ok(Self { conn })
    }

    pub fn send(&mut self, msg: &[u8]) -> Result<(), Box<dyn Error>> {
        self.conn.send(msg)?;
        Ok(())
    }
}

pub struct Input {
    _conn: MidiInputConnection<()>,
}

impl Input {
    pub fn new(name: String, sender: Sender<Vec<u8>>) -> Result<Self, Box<dyn Error>> {
        let input = MidiInput::new("spreader")?;
        let port = get_named_port(&input, &name);

        let conn = input.connect(
            &port,
            &name,
            move |_, msg: &[u8], _| {
                sender.send(msg.to_vec()).unwrap();
            },
            (),
        )?;
        Ok(Input { _conn: conn })
    }
}

#[allow(dead_code)]
// Return the available ports by name,
pub fn list_ports() -> Result<(Vec<String>, Vec<String>), Box<dyn Error>> {
    let input = MidiInput::new("spreader")?;
    let inputs = input
        .ports()
        .iter()
        .filter_map(|p| input.port_name(p).ok())
        .collect::<Vec<String>>();
    let output = MidiOutput::new("spreader")?;
    let outputs = output
        .ports()
        .iter()
        .filter_map(|p| output.port_name(p).ok())
        .collect::<Vec<String>>();
    Ok((inputs, outputs))
}
