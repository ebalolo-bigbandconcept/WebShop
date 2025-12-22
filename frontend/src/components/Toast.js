import { createContext, useCallback, useContext, useEffect, useState, useMemo } from "react";

const ToastContext = createContext(null);

const variantMap = {
  success: "success",
  error: "danger",
  danger: "danger",
  warning: "warning",
  info: "info",
  primary: "primary",
  secondary: "secondary",
  dark: "dark",
  light: "light",
};

const ToastItem = ({ toast, onClose }) => {
  const variant = variantMap[toast.variant] || "primary";

  // Schedule auto-dismiss when a duration is provided
  useEffect(() => {
    if (!toast.duration || toast.duration === Infinity) return undefined;
    const timer = setTimeout(() => onClose(toast.id), toast.duration);
    return () => clearTimeout(timer);
  }, [onClose, toast.duration, toast.id]);

  return (
    <div
      className={`toast show align-items-center text-bg-${variant} border-0 shadow mb-2`}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="d-flex">
        <div className="toast-body">
          {toast.title ? <strong className="me-2">{toast.title}</strong> : null}
          {toast.message}
        </div>
        <button
          type="button"
          className="btn-close btn-close-white me-2 m-auto"
          aria-label="Close"
          onClick={() => onClose(toast.id)}
        ></button>
      </div>
    </div>
  );
};

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    ({ message, title, variant = "info", duration = 4000 }) => {
      const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      setToasts((current) => [...current, { id, message, title, variant, duration }]);
      return id;
    },
    []
  );

  const contextValue = useMemo(
    () => ({ showToast, removeToast }),
    [showToast, removeToast]
  );

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <div className="toast-container position-fixed top-0 end-0 p-3" style={{ zIndex: 1080 }}>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onClose={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};
