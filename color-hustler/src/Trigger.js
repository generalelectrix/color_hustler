import React from 'react'
import Slider from './Slider'

const Trigger = ({name, initialBpm, dispatch}) => {
  return (
    <div>
      <button type="button" onClick={() => dispatch(name, "reset", true)}>reset</button>
      <Slider
        label="bpm"
        initialValue={initialBpm}
        min={0.001}
        max={3000.0}
        showValue={true}
        onChange={v => dispatch(name, "bpm", v)} />
    </div>
  )
}

export default Trigger