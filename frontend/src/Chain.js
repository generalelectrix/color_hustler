import React from 'react';
import Noise from './Noise'
import Trigger from './Trigger'
import ConstantList from './ConstantList'
import Waveform from './Waveform'
import Foldable from './Foldable'

const Chain = ({index, dispatch}) => {
  return (
    <div>
      channel {index + 1}
      <div className="flexrow">
        <div className="panel flexrow">
          <Foldable label="hue">
            <Noise
              name={"hue" + index}
              initialCenter={0.0}
              dispatch={dispatch} />
          </Foldable>
          <Foldable label="offsets" startVisible={false}>
            <ConstantList
              name={"hue_offsets" + index}
              dispatch={dispatch} />
          </Foldable>
          <Foldable label="waveform" startVisible={false}>
            <Waveform
              name={"hue_waveform" + index}
              dispatch={dispatch} />
          </Foldable>
        </div>
        <div className="panel flexrow">
          <Foldable label="saturation">
            <Noise
              name={"saturation" + index}
              initialCenter={1.0}
              dispatch={dispatch} />
          </Foldable>
        </div>
        <div className="panel flexrow">
          <Foldable label="lightness">
            <Noise
              name={"lightness" + index}
              initialCenter={0.5}
              dispatch={dispatch} />
          </Foldable>
        </div>
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