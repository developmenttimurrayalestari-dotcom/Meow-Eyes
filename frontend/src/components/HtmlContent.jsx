import React, { useMemo } from "react";
import DOMPurify from "dompurify";

export default function HtmlContent({ html, ...props }) {
  const content = useMemo(() => DOMPurify.sanitize(html || "", {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ["style", "form", "input", "button", "textarea", "select", "iframe", "object", "embed", "base", "link"],
    FORBID_ATTR: ["style"],
  }), [html]);
  return <div {...props} dangerouslySetInnerHTML={{ __html: content }} />;
}
