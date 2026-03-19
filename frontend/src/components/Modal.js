import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import bootstrap from "bootstrap/dist/js/bootstrap.js";

const Modal = forwardRef(({ title, children, footer, size = "modal-lg", backdrop = "static", keyboard = false, centered = false }, ref) => {
  const modalRef = useRef(null);
  const instanceRef = useRef(null);

  useEffect(() => {
    if (modalRef.current) {
      instanceRef.current = new bootstrap.Modal(modalRef.current, { backdrop, keyboard });
    }
    return () => {
      if (instanceRef.current && modalRef.current) {
        try {
          // Force remove any active transitions and backdrops before disposal.
          const backdrop = document.querySelector('.modal-backdrop');
          if (backdrop) {
            backdrop.remove();
          }
          
          // Remove the transition end listeners that might cause issues
          modalRef.current.classList.remove('show');
          modalRef.current.style.display = 'none';
          
          // Dispose of the Bootstrap modal instance
          instanceRef.current.dispose();
        } catch (error) {
          // Silently catch errors during cleanup
          console.debug("Modal cleanup error:", error);
        }
        instanceRef.current = null;
      }
    };
  }, [backdrop, keyboard]);

  useImperativeHandle(ref, () => ({
    open: () => {
      try {
        if (instanceRef.current && modalRef.current) {
          instanceRef.current.show();
        }
      } catch (error) {
        console.debug("Error opening modal:", error);
      }
    },
    close: () => {
      try {
        if (instanceRef.current && modalRef.current) {
          instanceRef.current.hide();
          // Clean up any lingering backdrops after the hide animation completes
          setTimeout(() => {
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
              backdrop.remove();
            }
          }, 300);
        }
      } catch (error) {
        console.debug("Error closing modal:", error);
      }
    },
  }));

  return (
    <div className="modal fade" tabIndex="-1" ref={modalRef} data-bs-backdrop={backdrop} data-bs-keyboard={keyboard}>
      <div className={`modal-dialog ${size} ${centered ? "modal-dialog-centered" : ""}`}>
        <div className="modal-content">
          {title && (
            <div className="modal-header">
              <h1 className="modal-title fs-5">{title}</h1>
            </div>
          )}
          <div className="modal-body">{children}</div>
          {footer && <div className="modal-footer">{footer}</div>}
        </div>
      </div>
    </div>
  );
});

export default Modal;
