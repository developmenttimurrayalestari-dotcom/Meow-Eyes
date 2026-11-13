import React, { useState } from "react";
import { Navigate } from "react-router-dom";
import { takeAuthReturn } from "../lib/authReturn";

// Old bookmarks return to local login; legacy broker credentials are ignored.
export default function AuthCallback() {
  const [returnTo] = useState(takeAuthReturn);
  return <Navigate to={returnTo ? "/login?returnTo=" + encodeURIComponent(returnTo) : "/login"} replace />;
}
