import React, { useMemo } from "react";
import { sanitizeRichContent } from "../lib/richContent";

export default function HtmlContent({ html, className = "", ...props }) {
  const content = useMemo(() => sanitizeRichContent(html, { resolveImages: true }), [html]);
  return <div {...props} className={`rich-content ${className}`} dangerouslySetInnerHTML={{ __html: content }} />;
}
