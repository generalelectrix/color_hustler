import React from 'react'
import { Slider } from './Slider'

const GAUSSIAN = 'gaussian'
const UNIFORM = 'uniform'

const Noise = ({name, initialCenter, dispatch}) => {

  const [mode, setMode] = React.useState(GAUSSIAN)
  const [center, setCenter] = React.useState(initialCenter)
  const [width, setWidth] = React.useState(0.0)

  const updateAndSend = (parameter, value, stateUpdater) => {
    stateUpdater(value)
    dispatch(name, parameter, value)
  }

  const updateMode = e => {
    const v = e.target.value
    updateAndSend("mode", v, setMode)
  }

  return (
    <div class="flexcol">
      <span>{name}</span>
      <select value={mode} onChange={updateMode}>
        <option value={GAUSSIAN}>gaussian</option>
        <option value={UNIFORM}>uniform</option>
      </select>
      <div className="flexrow">
        <Slider
          label="center"
          value={center}
          onChange={v => updateAndSend("center", v, setCenter)} />
        <Slider
          label="width"
          value={width}
          onChange={v => updateAndSend("width", v, setWidth)} />
      </div>
    </div>
  )
}

export default Noise