import React from "react";
import { StatefulSlider } from "./Slider";
// Define a bank and set easing parameter.

const SINGLE = "single";
const ALL = "all";
const TWO_VALUE = "two_value";

const LekoHustler = ({ name, dispatch }) => {
  const [bank, setBank] = React.useState(SINGLE);

  const updateBank = (e) => {
    const v = e.target.value;
    setBank(v);
    dispatch(name, "bank_name", v);
  };

  return (
    <div className="flexcol stretch">
      <select value={bank} onChange={updateBank} className="stretch">
        <option value={SINGLE}>single</option>
        <option value={TWO_VALUE}>two value</option>
        <option value={ALL}>all</option>
      </select>
      <StatefulSlider
        label="easing"
        initialValue={0.1}
        min={0.001}
        max={10.0}
        showValue={true}
        onChange={(v) => dispatch(name, "easing", v)}
      />
    </div>
  );
};

export default LekoHustler;
