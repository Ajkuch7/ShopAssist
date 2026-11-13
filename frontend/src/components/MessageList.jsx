import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble.jsx";
function MessageList({ messages, typing }) {
  const endRef = useRef(null);
  useEffect(
    () => endRef.current?.scrollIntoView({ behavior: "smooth" }),
    [messages, typing],
  );
  return (
    <div className="message-list">
      {messages.map((message, index) => (
        <MessageBubble
          key={`${message.timestamp.toISOString()}-${index}`}
          message={message}
        />
      ))}
      {typing && (
        <div className="typing">
          <span />
          <span />
          <span />
          ShopAssist is typing...
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
export default MessageList;
