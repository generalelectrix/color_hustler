import React from 'react';
import './Slider.css';

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

export const Slider = ({label, onChange, value, min=0.0, max=1.0, showValue=true}) => {
  const handleChange = e => onChange(e.target.value)

  return (
    <div className="slider">
      <input
        type="range"
        orient="vertical"
        min={min}
        max={max}
        step={0.001}
        value={value}
        onChange={handleChange}/>
      {label}
      {showValue &&
        <input
          type="number"
          className="slider-input"
          min={min}
          max={max}
          step={0.001}
          value={value}
          onChange={handleChange}/>}
    </div>
  )
}