import { useState } from 'react'
import AgentActivity from './AgentActivity.jsx'
import CustomerPicker from './CustomerPicker.jsx'
import MessageList from './MessageList.jsx'
import OrderCards from './OrderCards.jsx'
import ProductCard from './ProductCard.jsx'
import QuickReplies from './QuickReplies.jsx'
import SummaryCard from './SummaryCard.jsx'

function ChatWidget({ close, messages, orders, products, summaryCard, quickReplies, toolsUsed, typing, ended, error, customers, customerId, onCustomerChange, onSubmit, onNewChat }) {
  const [draft, setDraft] = useState('')
  const submit = (event) => { event?.preventDefault(); onSubmit(draft); setDraft('') }
  return <aside className="chat-panel"><header className="chat-header"><div className="chat-title"><div className="support-avatar">✦</div><div><h2>ShopAssist Support</h2><span><i />Online · synthetic demo</span></div></div><div className="chat-actions"><button onClick={onNewChat} title="Start a new chat">↻</button><button onClick={close} title="Close support">×</button></div></header><div className="chat-controls"><CustomerPicker customers={customers} value={customerId} onChange={onCustomerChange} /><button className="new-chat" onClick={onNewChat}>New chat</button></div><MessageList messages={messages} typing={typing} /><div className="chat-content"><OrderCards orders={orders} onSelect={onSubmit} />{products?.length > 0 && <div className="recommendations"><div className="recommendation-heading"><span>Curated for you</span><small>Select an option</small></div>{products.map((product, index) => <ProductCard key={product.product_id || index} product={product} index={index} onSelect={onSubmit} />)}</div>}<SummaryCard summary={summaryCard} /></div>{error && <div className="error-state">{error}</div>}<AgentActivity tools={toolsUsed} /><QuickReplies replies={quickReplies} onSelect={onSubmit} disabled={typing || ended} /><form className="composer" onSubmit={submit}><input disabled={typing || ended} value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={ended ? 'Chat ended' : 'Type a message...'} aria-label="Message ShopAssist" /><button disabled={typing || ended || !draft.trim()} aria-label="Send message">↑</button></form>{ended && <div className="ended-label">Chat ended · Start a New chat to continue</div>}</aside>
}
export default ChatWidget