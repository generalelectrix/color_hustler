import React from 'react';
import Noise from './Noise'
import Trigger from './Trigger'
import ConstantList from './ConstantList'

const Chain = ({index, dispatch}) => {
  return (
    <div>
      channel {index + 1}
      <div className="flexrow">
        <div className="panel flexrow">
          <Noise
            name={"hue" + index}
            displayName="hue"
            initialCenter={0.0}
            dispatch={dispatch} />
          <ConstantList
            name={"hue_offsets" + index}
            displayName="hue offsets"
            dispatch={dispatch} />
        </div>
        <div className="panel">
          <Noise
            name={"saturation" + index}
            displayName="saturation"
            initialCenter={1.0}
            dispatch={dispatch} />
        </div>
        <div className="panel">
          <Noise
            name={"lightness" + index}
            displayName="lightness"
            initialCenter={0.5}
            dispatch={dispatch} />
        </div>
        <div className="panel">
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