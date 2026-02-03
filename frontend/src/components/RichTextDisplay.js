/**
 * RichTextDisplay Component
 * A reusable component for displaying rich HTML content with Quill styling.
 */
const RichTextDisplay = ({ content, fontSize = "1rem", lineHeight = "1.2" }) => {
  if (!content || content.trim() === "" || content === "<p><br></p>") {
    return (
      <div
        style={{
          fontSize,
          lineHeight,
          color: "#999",
          fontStyle: "italic",
        }}
      >
        Aucun commentaire
      </div>
    );
  }

  return (
    <div
      className="quill-content"
      style={{
        fontSize,
        lineHeight,
      }}
      dangerouslySetInnerHTML={{ __html: content }}
    />
  );
};

export default RichTextDisplay;
