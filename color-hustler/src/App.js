import React from 'react';
import './App.css';
import Noise from './Noise'

// The websocket we'll use to communicate with the backend.
const socket = new WebSocket('ws://localhost:4321')

socket.onopen = _ => console.log("Opened websocket.")
socket.onmessage = event => console.log(event)

function App() {
  return (
    <div className="App">
      <Noise name="hue" dispatch={socket.send} />
    </div>
  );
}

export default App;
