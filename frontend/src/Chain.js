import React from "react";
import Noise from "./Noise";
import Trigger from "./Trigger";
import ConstantList from "./ConstantList";
import Waveform from "./Waveform";
import Foldable from "./Foldable";
import LekoHustler from "./GoboHustler";

const ModulationChain = ({ name, initialCenter, bipolar, index, dispatch }) => {
  return (
    <div className="panel flexrow">
      <Foldable label={name}>
        <Noise
          name={name + index}
          initialCenter={initialCenter}
          bipolar={bipolar}
          dispatch={dispatch}
        />
      </Foldable>
      <Foldable label="offsets" startVisible={false}>
        <ConstantList name={name + "_offsets" + index} dispatch={dispatch} />
      </Foldable>
      <Foldable label="waveform" startVisible={false}>
        <Waveform name={name + "_waveform" + index} dispatch={dispatch} />
      </Foldable>
    </div>
  );
};

export const ColorChain = ({ index, dispatch, label }) => {
  return (
    <div>
      {label ? label : "channel" + (index + 1)}
      <div className="flexrow">
        <ModulationChain
          name="hue"
          initialCenter={0.0}
          index={index}
          dispatch={dispatch}
        />
        <ModulationChain
          name="saturation"
          initialCenter={1.0}
          index={index}
          dispatch={dispatch}
        />
        <ModulationChain
          name="lightness"
          initialCenter={0.5}
          index={index}
          dispatch={dispatch}
        />
        <div className="panel">
          <span>trigger</span>
          <Trigger
            name={"trigger" + index}
            initialBpm={60.0}
            dispatch={dispatch}
          />
        </div>
      </div>
    </div>
  );
};

export const GoboChain = ({ index, dispatch }) => {
  return (
    <div>
      gobo rotation
      <div className="flexrow">
        <ModulationChain
          name="rotation"
          initialCenter={0.0}
          bipolar={true}
          index={index}
          dispatch={dispatch}
        />
        <div className="panel">
          <span>banks</span>
          <LekoHustler name="gobo_hustler" dispatch={dispatch} />
        </div>
        <div className="panel">
          <span>trigger</span>
          <Trigger
            name={"trigger" + index}
            initialBpm={60.0}
            dispatch={dispatch}
          />
        </div>
      </div>
    </div>
  );
};

export const DimmerChain = ({ index, dispatch }) => {
  return (
    <div>
      dimmers
      <div className="flexrow">
        <ModulationChain
          name="level"
          initialCenter={1.0}
          bipolar={false}
          index={index}
          dispatch={dispatch}
        />
        <div className="panel">
          <span>banks</span>
          <LekoHustler name="dimmer_hustler" dispatch={dispatch} />
        </div>
        <div className="panel">
          <span>trigger</span>
          <Trigger
            name={"trigger" + index}
            initialBpm={60.0}
            dispatch={dispatch}
          />
        </div>
      </div>
    </div>
  );
};
