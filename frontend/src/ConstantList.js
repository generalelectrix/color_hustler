import React from 'react'
import Toggle from './Toggle'
// Quick and dirty control over constant list driven modulators.

const ConstantList = ({name, dispatch}) => {

  const [values, setValues] = React.useState("[0.0]")

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

  return (
    <div className="flexcol stretch">
      <input
        type="text"
        value={values}
        onChange={e => setValues(e.target.value)}
        onKeyDown={handleKeyDown} />
      <Toggle
        label="randomize"
        onToggle={v => dispatch(name, "random", v)} />
    </div>

  )
}

export default ConstantList