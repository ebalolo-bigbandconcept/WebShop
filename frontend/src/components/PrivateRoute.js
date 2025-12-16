import { Navigate } from "react-router-dom";

function PrivateRoute({ user, requiredRole, children }) {
  if (!user) return <Navigate to="/" />;
  if (requiredRole) {
    if (Array.isArray(requiredRole)) {
      if (!requiredRole.includes(user.role)) return <Navigate to="/" />;
    } else {
      if (user.role !== requiredRole) return <Navigate to="/" />;
    }
  }
  return children;
}

export default PrivateRoute;
