import ReactMarkdown from "react-markdown";
function MessageBubble({ message }) {
  return (
    <div className={`message-row ${message.role}`}>
      <div className="message-bubble">
        {message.role === "bot" ? (
          <ReactMarkdown>{message.text}</ReactMarkdown>
        ) : (
          <p>{message.text}</p>
        )}
        <time>
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </time>
      </div>
    </div>
  );
}
export default MessageBubble;
