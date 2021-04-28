// A component that folds details away.
import React from "react";
import { FaCaretRight, FaCaretDown } from "react-icons/fa";
import "./Foldable.css";

const Foldable = (props) => {
  const [visible, setVisible] = React.useState(
    props.startVisible === undefined ? true : props.startVisible
  );

  const caret = visible ? (
    <FaCaretDown size={20} onClick={(_) => setVisible(false)} />
  ) : (
    <FaCaretRight size={20} onClick={(_) => setVisible(true)} />
  );

  return (
    <div className="fold-container flexcol">
      <div>
        {caret}
        <span className={visible ? null : "folded"}>{props.label}</span>
      </div>
      <div style={{ display: visible ? null : "none" }}>{props.children}</div>
    </div>
  );
};

export default Foldable;
