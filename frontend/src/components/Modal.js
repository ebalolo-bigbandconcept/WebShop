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
      if (instanceRef.current) {
        instanceRef.current.hide();
        instanceRef.current.dispose();
      }
    };
  }, [backdrop, keyboard]);

  useImperativeHandle(ref, () => ({
    open: () => instanceRef.current && instanceRef.current.show(),
    close: () => instanceRef.current && instanceRef.current.hide(),
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
