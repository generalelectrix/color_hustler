import React from 'react';
import Chain from './Chain';
import './App.css'

// The websocket we'll use to communicate with the backend.
const socket = new WebSocket('ws://localhost:4321')

socket.onopen = _ => console.log("Opened websocket.")
socket.onmessage = event => console.log(JSON.parse(event.data))

const dispatch = (name, attr, payload) => {
  socket.send(JSON.stringify([name + '.' + attr, payload]))
}

function App() {
  return (
    <div className="App">
      <Chain dispatch={dispatch} index={0}/>
      <Chain dispatch={dispatch} index={1}/>
      <Chain dispatch={dispatch} index={2}/>
    </div>
  );
}

export default App;
