import React from 'react';

export const StatefulSlider = ({label, onChange, initialValue=0.0, min, max, showValue}) => {
  const [value, setValue] = React.useState(initialValue)

  const handleChange = v => {
    setValue(v)
    onChange(v)
  }

  return (
    <Slider
      label={label}
      onChange={handleChange}
      value={value}
      min={min}
      max={max}
      showValue={showValue} />
  )
}

export const Slider = ({label, onChange, value, min=0.0, max=1.0, showValue=false}) => {
  const handleChange = e => onChange(e.target.value)

  return (
    <label>
      {label}
      <input
        type="range"
        orient="vertical"
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