import React from 'react'

const Toggle = ({label, initialState, onToggle, className}) => {
  const [on, setOn] = React.useState(initialState === undefined ? false : initialState)

  const toggle = () => {
    const newState = !on
    setOn(newState)
    onToggle(newState)
  }

  return (
    <button
      type="button"
      className={className + (on ? " active" : "")}
      onClick={() => toggle()}>
      {label}
    </button>
  )
}

export default Toggle