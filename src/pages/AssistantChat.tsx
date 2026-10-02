import { useEffect, useRef, useState } from 'react';

type Message = { role: 'user' | 'assistant'; text: string };
export default function AssistantChat({ crop, connected, send }: { crop: string; connected: boolean; send: (message: string, callback: (reply: string) => void) => (() => void) | undefined }) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const cancel = useRef<(() => void) | undefined>();
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => () => cancel.current?.(), []);
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }); }, [messages, busy, open]);
  const submit = (text: string) => {
    if (!text.trim() || busy || !connected) return;
    setDraft(''); setMessages(previous => [...previous, { role: 'user', text }]); setBusy(true);
    cancel.current = send(text, reply => { setMessages(previous => [...previous, { role: 'assistant', text: reply }]); setBusy(false); });
  };
  return <div className="cg-chat"><button className="cg-chat-launch" aria-expanded={open} aria-controls="cropguard-chat" onClick={() => setOpen(!open)}>{open ? 'Close assistant' : '✦ Ask DEM3T3R V1'}</button>{open && <section id="cropguard-chat" className="cg-chat-panel" aria-label="DEM3T3R V1 chat"><header><div><strong>DEM3T3R V1</strong><p>Your growing companion · {crop}</p></div><button aria-label="Close chat" onClick={() => setOpen(false)}>✕</button></header><div className="cg-chat-messages" role="log" aria-live="polite">{!messages.length && <div className="cg-chat-welcome"><h3>Let’s care for your crops.</h3><p>Ask about diseases, nutrition, recovery, or using your rover. Advice only; chat does not operate the robot.</p>{['Explain the latest detected disease', 'How should I plan fertilizer use?', 'How do I connect my rover?'].map(text => <button key={text} disabled={!connected} onClick={() => submit(text)}>{text} ↗</button>)}</div>}{messages.map((message, index) => <div key={index} className={`cg-chat-message ${message.role}`}><small>{message.role === 'user' ? 'You' : 'DEM3T3R V1'}</small><p>{message.text}</p></div>)}{busy && <p role="status">Preparing a reply…</p>}<div ref={end} /></div><form onSubmit={event => { event.preventDefault(); submit(draft); }}><label htmlFor="cropguard-question">{connected ? 'Ask about your selected crop' : 'Connect the dashboard service to chat'}</label><div><textarea id="cropguard-question" value={draft} onChange={event => setDraft(event.target.value)} maxLength={2000} rows={2} placeholder="How can I help this crop recover?" disabled={busy || !connected} /><button type="submit" disabled={busy || !connected || !draft.trim()}>Send ↑</button></div><small>Uses your configured AI service. Verify product labels before treatment.</small></form></section>}</div>;
}
