import React from 'react'
import { StatefulSlider } from './Slider'

const Trigger = ({name, initialBpm, dispatch}) => {
  return (
    <div class="flexcol">
      <span>{name}</span>
      <button type="button" onClick={() => dispatch(name, "reset", true)}>reset</button>
      <StatefulSlider
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