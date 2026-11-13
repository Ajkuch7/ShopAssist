const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      body.detail || "Support is unavailable right now, please try again.",
    );
  }
  return response.json();
}

export const getCustomers = () => request("/customers");
export const startChat = (sessionId, customerId) =>
  request("/chat/start", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, customer_id: customerId }),
  });
export const sendMessage = (sessionId, customerId, message) =>
  request("/chat", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      customer_id: customerId,
      message,
    }),
  });
export const resetSession = (sessionId) =>
  request("/session/reset", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
