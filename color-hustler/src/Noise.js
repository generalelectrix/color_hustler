import React from 'react'
import Slider from './Slider'

const GAUSSIAN = 'gaussian'
const UNIFORM = 'uniform'

const Noise = ({name, dispatch}) => {

  const sendMessage = (attr, payload) => {
    dispatch(JSON.stringify([name + '.' + attr, payload]))
  }

  const [mode, setMode] = React.useState(GAUSSIAN)

  const updateMode = e => {
    const v = e.target.value
    setMode(v)
    sendMessage("mode", v)
  }

  return (
    <div>
      {name}
      <select value={mode} onChange={updateMode}>
        <option value={GAUSSIAN}>gaussian</option>
        <option value={UNIFORM}>uniform</option>
      </select>
      <Slider label="center" onChange={v => sendMessage("center", v)} />
      <Slider label="width" onChange={v => sendMessage("width", v)} />
    </div>
  )
}

export default Noise