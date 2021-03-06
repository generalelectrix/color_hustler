import React from 'react'
import { Slider } from './Slider'
import Toggle from './Toggle'

const SINE = "sine"
const SQUARE = "square"
const SAWTOOTH = "sawtooth"
const TRIANGLE = "triangle"

const Waveform = ({name, displayName, dispatch}) => {

  const [waveform, setWaveform] = React.useState(SINE)
  const [amplitude, setAmplitude] = React.useState(0.0)
  const [smoothing, setSmoothing] = React.useState(0.0)
  const [dutyCycle, setDutyCycle] = React.useState(1.0)
  const [bpm, setBpm] = React.useState(60.0)

  const updateAndSend = (parameter, value, stateUpdater) => {
    stateUpdater(value)
    dispatch(name, parameter, value)
  }

  const updateWaveform = e => {
    const v = e.target.value
    updateAndSend("waveform", v, setWaveform)
  }

  return (
    <div className="flexcol stretch">
      <div className="flexrow">
        <select value={waveform} onChange={updateWaveform} className="stretch">
          <option value={SINE}>sine</option>
          <option value={SQUARE}>square</option>
          <option value={SAWTOOTH}>sawtooth</option>
          <option value={TRIANGLE}>triangle</option>
        </select>

        <button className="stretch" type="button" onClick={() => dispatch(name, "reset", true)}>reset</button>
        <Toggle
          label="pulse"
          className="stretch"
          onToggle={v => dispatch(name, "pulse", v)} />
      </div>
      <div className="flexrow stretch">
        <Slider
          label="bpm"
          value={bpm}
          min={0.001}
          max={3000.0}
          showValue={true}
          onChange={v => updateAndSend("bpm", v, setBpm)} />
        <Slider
          label="amplitude"
          value={amplitude}
          onChange={v => updateAndSend("amplitude", v, setAmplitude)} />
        <Slider
          label="smoothing"
          value={smoothing}
          onChange={v => updateAndSend("smoothing", v, setSmoothing)} />
        <Slider
          label="duty cycle"
          value={dutyCycle}
          onChange={v => updateAndSend("duty_cycle", v, setDutyCycle)} />
      </div>
    </div>
  )
}

export default Waveform