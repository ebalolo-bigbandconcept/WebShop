import DOMPurify from "dompurify";
/**
 * RichTextDisplay Component
 * A reusable component for displaying rich HTML content with Quill styling.
 */
const RichTextDisplay = ({
  content,
  fontSize = "1rem",
  lineHeight = "1.2",
  emptyText = "Aucun commentaire",
}) => {
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
        {emptyText}
      </div>
    );
  }

  const sanitizedContent = DOMPurify.sanitize(content, { 
    ALLOWED_TAGS: ['p', 'h1', 'h2', 'h3', 'strong', 'b', 'em', 'i', 'u', 's', 'ol', 'ul', 'li', 'a', 'br'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    KEEP_CONTENT: true
  });

  return (
    <div
      className="quill-content"
      style={{
        fontSize,
        lineHeight,
      }}
      dangerouslySetInnerHTML={{ __html: sanitizedContent }}
    />
  );
};

export default RichTextDisplay;
