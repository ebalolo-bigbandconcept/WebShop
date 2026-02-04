import { useEffect, useRef } from "react";
import Quill from "quill";
import "quill/dist/quill.snow.css";

/**
 * QuillEditor Component
 * A reusable Quill editor component that handles initialization, cleanup,
 * and content management.
 */
const QuillEditor = ({ containerRef, value, onChange, isActive, minHeight = "150px" }) => {
  const quillRef = useRef(null);
  const parentRef = useRef(null);
  const initialContentLoaded = useRef(false);

  const removeToolbar = (parent) => {
    if (!parent) return;
    parent.querySelectorAll(".ql-toolbar").forEach((toolbar) => toolbar.remove());
  };

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const parent = container.parentElement;
    parentRef.current = parent || parentRef.current;

    if (!isActive) {
      if (quillRef.current) {
        quillRef.current = null;
      }
      removeToolbar(parentRef.current || parent);
      container.innerHTML = "";
      initialContentLoaded.current = false;
      return;
    }

    if (quillRef.current) return;

    removeToolbar(parent);

    container.innerHTML = "";

    const quill = new Quill(container, {
      theme: "snow",
      modules: {
        toolbar: [
          [{ header: [1, 2, 3, false] }],
          ["bold", "italic", "underline", "strike"],
          [{ list: "ordered" }, { list: "bullet" }, { indent: "-1" }, { indent: "+1" }],
          ["link"],
          ["clean"],
        ],
      },
    });

    quill.on("text-change", () => {
      onChange(quill.root.innerHTML);
    });

    quillRef.current = quill;

    if (value) {
      quill.root.innerHTML = value;
      initialContentLoaded.current = true;
    } else {
      initialContentLoaded.current = true;
    }
  }, [isActive, containerRef, onChange, value]);

  useEffect(() => {
    if (!quillRef.current) return;
    if (initialContentLoaded.current) return;

    if (value) {
      quillRef.current.root.innerHTML = value;
      initialContentLoaded.current = true;
    }
  }, [value]);

  useEffect(() => {
    return () => {
      if (quillRef.current) {
        quillRef.current = null;
      }
      removeToolbar(parentRef.current);
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
      initialContentLoaded.current = false;
    };
  }, [containerRef]);

  return (
    <div
      ref={containerRef}
      style={{
        minHeight,
        backgroundColor: "#fff",
      }}
    />
  );
};

export default QuillEditor;
