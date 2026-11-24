import React, { useId } from 'react';

/** Visible label and optional instructions for one native form control. */
export default function FormField({ label, hint, children, className = '' }) {

  const generatedId = useId();
  const id = children.props.id || generatedId;
  const hintId = `${id}-help`;
  const describedBy = [children.props['aria-describedby'], hint && hintId].filter(Boolean).join(' ') || undefined;

  return <div className={`min-w-0 space-y-1.5 ${className}`}>
    <label htmlFor={id} className="block text-xs font-semibold">
      {label}{children.props.required && <span aria-hidden="true"> *</span>}
    </label>
    {React.cloneElement(children, {
      id,
      'aria-describedby': describedBy,
      className: `w-full min-w-0 ${children.props.className || ''}`
    })}
    {hint && <p id={hintId} className="text-xs text-meow-gray">{hint}</p>}
  </div>;
}
