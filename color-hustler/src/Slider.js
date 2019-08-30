import React from 'react';

const Slider = ({label, onChange, initialValue=0.0, min=0.0, max=1.0, showValue=false}) => {
  const [value, setValue] = React.useState(initialValue)

  const handleChange = e => {
    setValue(e.target.value)
    onChange(e.target.value)
  }

  return (
    <label>
      {label}
      <input
        type="range"
        min={min}
        max={max}
        step={0.00001}
        value={value}
        onChange={handleChange}/>
      {showValue &&
        <input
          type="number"
          min={min}
          max={max}
          step={0.00001}
          value={value}
          onChange={handleChange}/>}
    </label>
  )
}

export default Slider