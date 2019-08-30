import React from 'react'
import Slider from './Slider'

const GAUSSIAN = 'gaussian'
const UNIFORM = 'uniform'

const Noise = ({name, initialCenter, dispatch}) => {

  const [mode, setMode] = React.useState(GAUSSIAN)

  const updateMode = e => {
    const v = e.target.value
    setMode(v)
    dispatch(name, "mode", v)
  }

  return (
    <div>
      {name}
      <select value={mode} onChange={updateMode}>
        <option value={GAUSSIAN}>gaussian</option>
        <option value={UNIFORM}>uniform</option>
      </select>
      <Slider
        label="center"
        initialValue={initialCenter}
        onChange={v => dispatch(name, "center", v)} />
      <Slider
        label="width"
        initialValue={0.0}
        onChange={v => dispatch(name, "width", v)} />
    </div>
  )
}

export default Noise