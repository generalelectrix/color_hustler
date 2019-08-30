import React from 'react';

const Slider = ({label, onChange}) => {
  const [value, setValue] = React.useState(0.0)

  const handleChange = e => {
    setValue(e.target.value)
    onChange(e.target.value)
  }

  return (
    <label>
      {label}
      <input
        type="range"
        min="0.0"
        max="1.0"
        step="0.001"
        value={value}
        onChange={handleChange}/>
    </label>
  )
}

export default Slider