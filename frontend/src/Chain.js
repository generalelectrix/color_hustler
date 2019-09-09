import React from 'react';
import Noise from './Noise'
import Trigger from './Trigger'
import ConstantList from './ConstantList'
import Waveform from './Waveform'
import Foldable from './Foldable'

const ModulationChain = ({name, initialCenter, index, dispatch}) => {
  return (
    <div className="panel flexrow">
      <Foldable label={name}>
        <Noise
          name={name + index}
          initialCenter={initialCenter}
          dispatch={dispatch} />
      </Foldable>
      <Foldable label="offsets" startVisible={false}>
        <ConstantList
          name={name + "_offsets" + index}
          dispatch={dispatch} />
      </Foldable>
      <Foldable label="waveform" startVisible={false}>
        <Waveform
          name={name + "_waveform" + index}
          dispatch={dispatch} />
      </Foldable>
    </div>
  )
}

const Chain = ({index, dispatch}) => {
  return (
    <div>
      channel {index + 1}
      <div className="flexrow">
        <ModulationChain name="hue" initialCenter={0.0} index={index} dispatch={dispatch} />
        <ModulationChain name="saturation" initialCenter={1.0} index={index} dispatch={dispatch} />
        <ModulationChain name="lightness" initialCenter={0.5} index={index} dispatch={dispatch} />
        <div className="panel">
          <span>trigger</span>
          <Trigger
            name={"trigger" + index}
            initialBpm={60.0}
            dispatch={dispatch} />
        </div>
      </div>
    </div>

  )
}

export default Chain