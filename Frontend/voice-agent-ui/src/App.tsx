import { useState, useRef, useEffect } from 'react';
import Results from './Results'; // Ensure you have created Results.tsx

// Define the shape of a chat message
interface Message {
  sender: 'bot' | 'user';
  text: string;
}

// Define the shape of the data panel state
interface SidebarData {
  type: 'orders' | 'products' | null;
  items: any[];
}


function App() {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'bot', text: 'System Online. Neural Link Established.' }
  ]);
  
  // New state to hold data for the Results.tsx panel
  const [sidebarData, setSidebarData] = useState<SidebarData>({
    type: null,
    items: []
  });

  useEffect(() => {
  const clearAIContext = async () => {
    try {
      console.log("🚀 Initializing Session: Clearing Backend Context...");
      await fetch("http://127.0.0.1:8000/reset-chat");
    } catch (error) {
      console.error("Failed to reset AI context on refresh:", error);
    }
  };

  clearAIContext();
}, []); // Empty array means this runs once on mount/refresh
  
  const endOfChatRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    endOfChatRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = (sender: 'bot' | 'user', text: string) => {
    setMessages(prev => [...prev, { sender, text }]);
  };

  // --- THE BACKEND CONNECTION ---
  const toggleMic = async () => {
    if (isListening) return;

    setIsListening(true);
    
    try {
      // 1. Call Python FastAPI Server
      const response = await fetch("http://127.0.0.1:8000/run-agent");
      
      if (!response.ok) {
        throw new Error(`Server Error: {response.status}`);
      }

      const data = await response.json();
      
      // 2. Display User Transcription
      if (data.user_text) {
        addMessage('user', data.user_text);
      } else {
        addMessage('user', "(Silence)");
      }

      // 3. Display AI Response
      if (data.bot_text) {
        addMessage('bot', data.bot_text);
      }

      // 4. Update Results Sidebar with structured data if present
      // Expecting backend to return { type: 'orders' | 'products', items: [...] }
      if (data.type && data.items) {
        setSidebarData({
          type: data.type,
          items: data.items
        });
      }

    } catch (error) {
      console.error("Connection failed:", error);
      addMessage('bot', "⚠️ Error: Connection to Python Brain failed. Ensure server.py is running.");
    } finally {
      setIsListening(false); 
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] flex items-center justify-center p-6">
      
      {/* OUTER WRAPPER: Responsive Layout */}
      <div className="w-full max-w-6xl flex flex-col lg:flex-row gap-6 items-start justify-center">
        
        {/* LEFT COLUMN: THE VOICE AGENT CHAT */}
        <div className="w-full max-w-lg flex flex-col items-center">
          <div className="w-full bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden relative">
            
            {/* TOP BAR */}
            <div className="bg-slate-800 p-4 border-b border-slate-700 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className={`h-3 w-3 rounded-full ${isListening ? 'bg-red-500 animate-pulse shadow-[0_0_10px_red]' : 'bg-emerald-500'}`}></div>
                <h1 className="text-lg font-bold text-cyan-400 tracking-widest uppercase">A.I. Voice Agent</h1>
              </div>
              <div className="text-xs text-slate-500 font-mono">NEURAL_LINK_ACTIVE</div>
            </div>

            {/* CHAT HISTORY */}
            <div className="h-[450px] overflow-y-auto p-4 space-y-4 bg-[#0B1120] scrollbar-thin scrollbar-thumb-slate-700">
              {messages.map((msg, index) => (
                <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] p-3 text-sm rounded-xl font-mono leading-relaxed ${
                    msg.sender === 'user' 
                      ? 'bg-cyan-900/40 text-cyan-100 border border-cyan-700/50 rounded-br-none' 
                      : 'bg-slate-800 text-slate-300 border border-slate-700 rounded-bl-none'
                  }`}>
                    {msg.sender === 'bot' && <span className="text-[10px] text-cyan-500 block mb-1 font-bold uppercase tracking-tighter">Agent // Output</span>}
                    {msg.text}
                  </div>
                </div>
              ))}
              <div ref={endOfChatRef} />
            </div>

            {/* BOTTOM CONTROLS */}
            <div className="bg-slate-800 p-6 border-t border-slate-700 flex justify-center relative">
              
              {/* Visual Pulse Wave */}
              {isListening && (
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500 to-transparent animate-pulse"></div>
              )}

              <button 
                onClick={toggleMic}
                disabled={isListening}
                className={`
                  h-20 w-20 rounded-full flex items-center justify-center transition-all duration-300 border-4 outline-none
                  ${isListening 
                    ? 'bg-red-500/10 border-red-500 text-red-500 cursor-wait' 
                    : 'bg-slate-700 border-slate-600 text-cyan-400 hover:bg-slate-600 hover:scale-105 hover:border-cyan-400 cursor-pointer'}
                `}
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={`w-8 h-8 ${isListening ? 'animate-bounce' : ''}`}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 1.5a3 3 0 013 3v4.5a3 3 0 01-6 0v-4.5a3 3 0 013-3z" />
                </svg>
              </button>
            </div>
          </div>
          
          <p className="mt-4 text-slate-600 text-[10px] font-mono tracking-widest uppercase">
            Local Link: 127.0.0.1:8000 // Status: Secure
          </p>
        </div>

        {/* RIGHT COLUMN: THE DATA PANEL */}
        <div className="w-full md:w-[450px] h-[635px] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
          <div className="bg-slate-800/50 p-4 border-b border-slate-700 flex justify-between items-center">
            <h2 className="text-xs font-bold text-slate-400 tracking-[0.2em] uppercase">Data Stream // Results</h2>
            {sidebarData.type && (
              <span className="text-[10px] bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded border border-cyan-500/20 animate-pulse">
                LIVE_DATA
              </span>
            )}
          </div>
          
          {/* Injecting the Results Component */}
          <div className="flex-1 overflow-hidden">
            <Results data={sidebarData} />
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;