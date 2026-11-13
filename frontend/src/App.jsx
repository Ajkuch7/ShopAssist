import { useEffect, useRef, useState } from "react";
import { getCustomers, resetSession, sendMessage, startChat } from "./api.js";
import ChatWidget from "./components/ChatWidget.jsx";

const freshSession = () => `web-${crypto.randomUUID()}`;

function App() {
  const [customers, setCustomers] = useState([]);
  const [customerId, setCustomerId] = useState(1);
  const [sessionId, setSessionId] = useState(freshSession);
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [summaryCard, setSummaryCard] = useState(null);
  const [quickReplies, setQuickReplies] = useState([]);
  const [toolsUsed, setToolsUsed] = useState([]);
  const [ended, setEnded] = useState(false);
  const [typing, setTyping] = useState(false);
  const [error, setError] = useState("");
  const initialized = useRef(false);

  useEffect(() => {
    getCustomers()
      .then(setCustomers)
      .catch(() =>
        setError("Support is unavailable right now, please try again."),
      );
  }, []);
  useEffect(() => {
    if (isOpen && !initialized.current) {
      initialized.current = true;
      beginSession(sessionId, customerId);
    }
  }, [isOpen]);

  async function beginSession(nextSession, nextCustomer) {
    setTyping(true);
    setError("");
    try {
      applyResponse(await startChat(nextSession, nextCustomer), true);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setTyping(false);
    }
  }

  function applyResponse(result, isGreeting = false) {
    const botMessage = {
      role: "bot",
      text: result.reply,
      timestamp: new Date(),
    };
    setMessages((current) =>
      isGreeting ? [botMessage] : [...current, botMessage],
    );
    setOrders(result.orders || []);
    setProducts(result.products || []);
    setSummaryCard(result.summary_card || null);
    setQuickReplies(result.quick_replies || []);
    setToolsUsed(result.tools_used || []);
    setEnded(Boolean(result.conversation_ended));
  }

  async function submitMessage(text) {
    const message = text.trim();
    if (!message || typing || ended) return;
    setMessages((current) => [
      ...current,
      { role: "customer", text: message, timestamp: new Date() },
    ]);
    setTyping(true);
    setQuickReplies([]);
    setError("");
    try {
      applyResponse(await sendMessage(sessionId, customerId, message));
    } catch {
      setError("Support is unavailable right now, please try again.");
    } finally {
      setTyping(false);
    }
  }

  async function changeCustomer(nextCustomerId) {
    const nextSession = freshSession();
    setCustomerId(Number(nextCustomerId));
    setSessionId(nextSession);
    setMessages([]);
    setOrders([]);
    setProducts([]);
    setSummaryCard(null);
    setEnded(false);
    initialized.current = true;
    await beginSession(nextSession, Number(nextCustomerId));
  }

  async function newChat() {
    await resetSession(sessionId).catch(() => {});
    const nextSession = freshSession();
    setSessionId(nextSession);
    setMessages([]);
    setOrders([]);
    setProducts([]);
    setSummaryCard(null);
    setQuickReplies([]);
    setToolsUsed([]);
    setEnded(false);
    initialized.current = true;
    beginSession(nextSession, customerId);
  }

  return (
    <main className="storefront">
      <header className="store-header">
        <div className="brand-mark">
          <span>SS</span>
        </div>
        <div>
          <p className="eyebrow">EVERYDAY GOODS / CUSTOMER CARE</p>
          <h1>ShopAssist Market</h1>
        </div>
        <nav>
          <a href="#featured">Featured</a>
          <a href="#orders">Your orders</a>
          <button className="quiet-button">Account</button>
        </nav>
      </header>
      <section className="store-hero">
        <div className="hero-copy">
          <p className="eyebrow">A calmer way to shop</p>
          <h2>
            Good products.
            <br />
            <em>Human answers.</em>
          </h2>
          <p>
            Browse a small collection of considered essentials, with support
            that remembers the details when something goes sideways.
          </p>
          <button className="primary-button" onClick={() => setIsOpen(true)}>
            Open support <span>↗</span>
          </button>
        </div>
        <div
          className="hero-art"
          aria-label="Abstract product display"
          role="img"
        >
          <span className="sun-disc" />
          <span className="product-shape shape-one" />
          <span className="product-shape shape-two" />
          <span className="product-shape shape-three" />
          <span className="hero-label">
            SPRING
            <br />
            EDIT / 24
          </span>
        </div>
      </section>
      <section className="catalog" id="featured">
        <div className="section-heading">
          <div>
            <p className="eyebrow">The current edit</p>
            <h2>Useful things, beautifully simple.</h2>
          </div>
          <span className="catalog-count">03 / essentials</span>
        </div>
        <div className="product-grid">
          {[
            [
              "01",
              "Everyday Laptop",
              "Lightweight workday companion",
              "$499",
              "electronics",
            ],
            [
              "02",
              "Quiet Headphones",
              "A little more focus",
              "$79",
              "headphones",
            ],
            ["03", "Trail Shoes", "Go further, comfortably", "$95", "footwear"],
          ].map(([number, name, subtitle, price, tone]) => (
            <article className={`catalog-card ${tone}`} key={name}>
              <div className="catalog-image">
                <span>{number}</span>
              </div>
              <div className="catalog-meta">
                <div>
                  <h3>{name}</h3>
                  <p>{subtitle}</p>
                </div>
                <strong>{price}</strong>
              </div>
              <button className="text-button" onClick={() => setIsOpen(true)}>
                Ask about this <span>→</span>
              </button>
            </article>
          ))}
        </div>
      </section>
      <footer>
        <span>SHOPASSIST / SYNTHETIC DEMO STORE</span>
        <span>Support is one click away.</span>
      </footer>
      <button
        className={`chat-launcher ${isOpen ? "is-hidden" : ""}`}
        onClick={() => setIsOpen(true)}
        aria-label="Open ShopAssist support"
      >
        <span className="launcher-spark">✦</span>
        <span>Need a hand?</span>
        <b>↗</b>
      </button>
      {isOpen && (
        <ChatWidget
          close={() => setIsOpen(false)}
          messages={messages}
          orders={orders}
          products={products}
          summaryCard={summaryCard}
          quickReplies={quickReplies}
          toolsUsed={toolsUsed}
          typing={typing}
          ended={ended}
          error={error}
          customers={customers}
          customerId={customerId}
          onCustomerChange={changeCustomer}
          onSubmit={submitMessage}
          onNewChat={newChat}
        />
      )}
    </main>
  );
}

export default App;
