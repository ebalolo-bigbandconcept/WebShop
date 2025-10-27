import { Navigate } from "react-router-dom";

function PrivateRoute({ user, requiredRole, children }) {
  if (!user) return <Navigate to="/" />;
  if (requiredRole && user.role !== requiredRole) return <Navigate to="/" />;
  return children;
}

export default PrivateRoute;