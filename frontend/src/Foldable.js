// A component that folds details away.
import React from 'react';
import { FaCaretRight, FaCaretDown } from "react-icons/fa";
import './Foldable.css'

const Foldable = props => {

  const [visible, setVisible] = React.useState(
    props.startVisible === undefined ? true : props.startVisible)

  if (visible) {
    return (
      <div className="fold-container flexcol">
        <div>
          <FaCaretDown size={20} onClick={_ => setVisible(false)}/>
          <span>{props.label}</span>
        </div>
        {props.children}
      </div>
    )
  }

  return (
    <div className="fold-container flexcol">
      <FaCaretRight size={20} onClick={_ => setVisible(true)}/>
      <span className="folded">{props.label}</span>
    </div>
  )

}

export default Foldable