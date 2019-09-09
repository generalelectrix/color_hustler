import React from 'react'
import { StatefulSlider } from './Slider'
import { FaPlayCircle, FaPauseCircle } from "react-icons/fa";

const Trigger = ({name, initialBpm, dispatch}) => {
  const [active, setActive] = React.useState(true)

  const handleActive = v => {
    setActive(v)
    dispatch(name, "active", v)
  }

  return (
    <div className="flexcol stretch">
      <button
        type="button"
        className={active ? "active" : ""}
        onClick={() => handleActive(!active)}>
        active
      </button>
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