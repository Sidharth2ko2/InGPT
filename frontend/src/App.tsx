import { useEffect, useRef, useState } from "react";
import { Trash2, Pencil, Send, Plus } from "lucide-react";

type Message = { role: "user" | "assistant"; content: string };
type Session = { id: string; title: string; isEditing?: boolean };

const API = "http://localhost:8000";

export default function App() {
  /* ---------------- 1. INITIAL STATE (Brand New Session on Refresh) ---------------- */
  const [sessions, setSessions] = useState<Session[]>(() => {
    const stored = localStorage.getItem("sessions");
    return stored ? JSON.parse(stored) : [];
  });

  // Always initialize with a fresh ID so refresh = new chat
  const [activeSession, setActiveSession] = useState<string>(`sess_${Date.now()}`);
  const [messages, setMessages] = useState<Message[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  /* ---------------- 2. PERSISTENCE ---------------- */
  useEffect(() => {
    localStorage.setItem("sessions", JSON.stringify(sessions));
  }, [sessions]);

  /* ---------------- 3. HISTORY SYNC ---------------- */
  useEffect(() => {
    const syncHistory = async () => {
      if (!activeSession) return;

      const cached = localStorage.getItem(`cache_${activeSession}`);
      if (cached) setMessages(JSON.parse(cached));
      else setMessages([]);

      try {
        const res = await fetch(`${API}/history/${activeSession}`);
        if (res.ok) {
          const data = await res.json();
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
            localStorage.setItem(`cache_${activeSession}`, JSON.stringify(data.messages));
          }
        }
      } catch (err) {
        console.error("Sync failed:", err);
      }
    };
    syncHistory();
  }, [activeSession]);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  /* ---------------- 4. ACTIONS ---------------- */
  const startNewChat = () => {
    const id = `sess_${Date.now()}`;
    setActiveSession(id);
    setMessages([]);
    setSessions(prev => [{ id, title: "New Chat" }, ...prev]);
  };

  const deleteSession = async (id: string) => {
    const filtered = sessions.filter(s => s.id !== id);
    setSessions(filtered);
    localStorage.removeItem(`cache_${id}`);
    
    if (activeSession === id) {
      if (filtered.length > 0) setActiveSession(filtered[0].id);
      else startNewChat();
    }

    try {
      await fetch(`${API}/history/${id}`, { method: "DELETE" });
    } catch (e) { console.error("Delete failed"); }
  };

  const renameSession = (id: string, newTitle: string) => {
    setSessions(prev => prev.map(s => 
      s.id === id ? { ...s, title: newTitle || "New Chat", isEditing: false } : s
    ));
  };

  /* ---------------- 5. SEND LOGIC ---------------- */
  const send = async () => {
    if (!q.trim() || loading) return;
    const userText = q;
    setQ("");
    setLoading(true);

    const updatedMessages: Message[] = [...messages, { role: "user", content: userText }];
    setMessages(updatedMessages);

    setSessions(prev => {
      const exists = prev.find(s => s.id === activeSession);
      if (!exists) return [{ id: activeSession, title: userText.slice(0, 25) }, ...prev];
      return prev.map(s => 
        s.id === activeSession && s.title === "New Chat" 
        ? { ...s, title: userText.slice(0, 25) } : s
      );
    });

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: activeSession, question: userText, mode: "ask" }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let assistantText = "";
      setMessages(prev => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;
        const chunk = decoder.decode(value).split("\n");
        for (const line of chunk) {
          if (line.startsWith("data: ")) {
            const payload = line.replace("data: ", "").trim();
            if (payload === "[DONE]") continue;
            try {
              const json = JSON.parse(payload);
              assistantText += json.chunk.replace(/\\n/g, "\n");
              setMessages(prev => {
                const copy = [...prev];
                copy[copy.length - 1].content = assistantText;
                return copy;
              });
            } catch {}
          }
        }
      }
      localStorage.setItem(`cache_${activeSession}`, JSON.stringify([...updatedMessages, { role: "assistant", content: assistantText }]));
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Error: InGPT server unreachable." }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="flex h-screen bg-white font-sans text-gray-900 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 bg-[#171717] text-gray-300 p-4 flex flex-col shadow-2xl">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center text-black font-bold">In</div>
          <h1 className="text-xl font-bold text-white tracking-tight">InGPT</h1>
        </div>

        <button 
          onClick={startNewChat} 
          className="flex items-center justify-center gap-2 p-3 border border-gray-700 rounded-xl mb-6 hover:bg-gray-800 transition-all font-medium text-sm text-white"
        >
          <Plus size={16} /> New Chat
        </button>

        <div className="flex-1 overflow-y-auto space-y-1">
          <p className="text-[10px] text-gray-500 font-bold uppercase px-2 mb-2 tracking-widest">History</p>
          {sessions.map(s => (
            <div 
              key={s.id} 
              onClick={() => setActiveSession(s.id)}
              className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                s.id === activeSession ? "bg-[#2f2f2f] text-white" : "hover:bg-[#212121]"
              }`}
            >
              {s.isEditing ? (
                <input 
                  autoFocus 
                  className="bg-transparent outline-none w-full text-white" 
                  defaultValue={s.title} 
                  onBlur={e => renameSession(s.id, e.target.value)} 
                  onKeyDown={e => e.key === 'Enter' && renameSession(s.id, e.currentTarget.value)} 
                />
              ) : (
                <>
                  <span className="truncate flex-1 text-sm">{s.title}</span>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
                    <button onClick={(e) => {e.stopPropagation(); setSessions(prev => prev.map(x => x.id === s.id ? {...x, isEditing: true} : x))}}><Pencil size={14} /></button>
                    <button onClick={(e) => {e.stopPropagation(); deleteSession(s.id)}} className="hover:text-red-400"><Trash2 size={14} /></button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col items-center bg-[#fdfdfd]">
        <div ref={scrollRef} className="flex-1 w-full max-w-3xl p-8 overflow-y-auto space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center opacity-30 mt-32">
              <div className="w-16 h-16 bg-black rounded-2xl flex items-center justify-center text-white text-3xl font-bold mb-4 shadow-lg">In</div>
              <h2 className="text-4xl font-bold text-black">InGPT</h2>
              <p className="mt-2 text-gray-600 font-medium">Internal Corporate Intelligence</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`p-4 rounded-2xl max-w-[85%] shadow-sm ${
                m.role === "user" ? "bg-black text-white" : "bg-white border border-gray-200 text-gray-800"
              }`}>
                {m.content}
              </div>
            </div>
          ))}
        </div>
        
        <div className="p-8 w-full max-w-3xl relative">
          <div className="relative flex items-center shadow-2xl rounded-2xl">
            <textarea 
              className="w-full p-4 pr-14 bg-white border border-gray-100 rounded-2xl resize-none outline-none focus:border-gray-300 transition-all" 
              rows={1} 
              value={q} 
              onChange={e => setQ(e.target.value)} 
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())} 
              placeholder="Message InGPT..." 
            />
            <button 
              onClick={send} 
              disabled={loading} 
              className={`absolute right-3 bottom-3 h-9 w-9 rounded-xl flex items-center justify-center transition-all ${
                loading ? "bg-gray-100" : "bg-black text-white hover:scale-105"
              }`}
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-center text-[10px] text-gray-400 mt-4 font-bold uppercase tracking-widest">
            Powered by InGPT Secure Intelligence
          </p>
        </div>
      </main>
    </div>
  );
}
