import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Cat } from "lucide-react";

export const ProtectedRoute = ({ children, requireRole }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" data-testid="protected-loading">
        <Cat className="h-10 w-10 text-meow-salmon animate-pulse" />
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname + location.search + location.hash }} replace />;
  }
  if (requireRole === "admin" && !["staff", "admin", "super_admin"].includes(user.role)) {
    return <Navigate to="/" replace />;
  }
  if (requireRole === "super_admin" && user.role !== "super_admin") {
    return <Navigate to="/" replace />;
  }
  return children;
};

export default ProtectedRoute;
