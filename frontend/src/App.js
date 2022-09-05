import React from "react";
import { ColorChain, GoboChain, DimmerChain } from "./Chain";
import "./App.css";

// The websocket we'll use to communicate with the backend.
const socket = new WebSocket("ws://" + window.location.hostname + ":4321");

socket.onopen = (_) => console.log("Opened websocket.");
socket.onmessage = (event) => console.log(JSON.parse(event.data));

const dispatch = (name, attr, payload) => {
  socket.send(JSON.stringify([name + "." + attr, payload]));
};

function App() {
  return (
    <div className="App">
      {/* <ColorChain dispatch={dispatch} index={0} label="rainbow g2s" />
      <ColorChain dispatch={dispatch} index={1} label="tree uplights" />
      <ColorChain dispatch={dispatch} index={2} label="source 4s" /> */}
      <GoboChain dispatch={dispatch} index={3} />
      <DimmerChain dispatch={dispatch} index={4} />
    </div>
  );
}

export default App;
