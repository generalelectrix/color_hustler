import React from 'react'
// Quick and dirty control over constant list driven modulators.

const ConstantList = ({name, dispatch}) => {

  const [values, setValues] = React.useState("")
  const [random, setRandom] = React.useState(false)

  const handleKeyDown = e => {
    if (e.keyCode === 13) {
      // Try to parse it as json, ignore if invalid.
      var parsed;
      try {
        parsed = JSON.parse(values)
      } catch (e) {
        return
      }
      dispatch(name, "values", parsed)
    }
  }

  const handleRandom = e => {
    setRandom(e.target.checked)
    dispatch(name, "random", e.target.checked)
  }

  return (
    <div className="panel">
      <span>{name}</span>
      <input
        type="text"
        pattern=""
        onChange={e => setValues(e.target.value)}
        onKeyDown={handleKeyDown} />
      <br/>
      <label>
        randomize?
        <button type="checkbox" onChange={handleRandom} checked={random}/>
      </label>
    </div>

  )
}

export default ConstantList