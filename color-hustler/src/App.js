import React from 'react';
import Noise from './Noise'
import Trigger from './Trigger'
import ConstantList from './ConstantList'

// The websocket we'll use to communicate with the backend.
const socket = new WebSocket('ws://localhost:4321')

socket.onopen = _ => console.log("Opened websocket.")
socket.onmessage = event => console.log(JSON.parse(event.data))

const sendMessage = (name, attr, payload) => {
  socket.send(JSON.stringify([name + '.' + attr, payload]))
}

function App() {
  return (
    <div className="App">
      <Noise name="hue" initialCenter={0.0} dispatch={sendMessage} />
      <ConstantList name="hue_offsets" dispatch={sendMessage} />
      <Noise name="saturation" initialCenter={1.0} dispatch={sendMessage} />
      <Noise name="lightness" initialCenter={0.5} dispatch={sendMessage} />
      <Trigger name="note_trigger" initialBpm={60.0} dispatch={sendMessage} />
    </div>
  );
}

export default App;
