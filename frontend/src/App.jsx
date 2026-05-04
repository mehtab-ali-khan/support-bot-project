import { useState, useRef, useEffect } from "react";
import {
  Upload, Send, FileText, Bot, User,
  Loader2, ChevronDown, ChevronUp, Wrench, X
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [error, setError] = useState("");
  const [expandedSources, setExpandedSources] = useState({});
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are allowed");
      return;
    }

    setError("");
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/upload/`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Upload failed");
        setUploadedFile(null);
        setMessages([]);
        return;
      }

      setUploadedFile({
        name: file.name,
        pages: data.pages,
        chunks: data.total_chunks,
      });

      setMessages([{
        role: "bot",
        text: `Document ready! Processed ${file.name} — ${data.pages} pages, ${data.total_chunks} chunks. What would you like to know?`,
        sources: [],
        tools_used: [],
      }]);

    } catch {
      setError("Could not connect to server.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleAsk = async () => {
    const currentQuestion = question.trim();
    if (!currentQuestion || asking) return;

    setMessages((prev) => [...prev, {
      role: "user",
      text: currentQuestion,
      sources: [],
      tools_used: []
    }]);
    setQuestion("");
    setAsking(true);
    setError("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      const response = await fetch(`${API_URL}/ask/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: currentQuestion }),
      });

      const data = await response.json();

      setMessages((prev) => [...prev, {
        role: "bot",
        text: response.ok ? data.answer : (data.error || "Something went wrong"),
        sources: data.sources || [],
        tools_used: data.tools_used || [],
      }]);

    } catch {
      setMessages((prev) => [...prev, {
        role: "bot",
        text: "Could not connect to server.",
        sources: [],
        tools_used: []
      }]);
    } finally {
      setAsking(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const handleTextareaChange = (e) => {
    setQuestion(e.target.value);
    // Auto resize textarea
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
  };

  const toggleSources = (index) => {
    setExpandedSources((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">

      {/* Top Nav */}
      <nav className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shrink-0">
            <Bot size={17} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-gray-900 text-base">DocBot</span>
              <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full">AI</span>
            </div>
            {uploadedFile && (
              <div className="flex items-center gap-1 mt-0.5">
                <FileText size={11} className="text-indigo-400" />
                <span className="text-xs text-gray-400 truncate max-w-40">
                  {uploadedFile.name}
                </span>
                <span className="text-xs text-gray-300">·</span>
                <span className="text-xs text-gray-400">
                  {uploadedFile.pages}p
                </span>
              </div>
            )}
          </div>
        </div>

        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex items-center gap-1.5 text-sm bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white px-3 py-2 rounded-lg transition-colors font-medium shrink-0"
        >
          <Upload size={14} />
          <span className="hidden sm:inline">
            {uploadedFile ? "Change PDF" : "Upload PDF"}
          </span>
          <span className="sm:hidden">PDF</span>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileUpload}
          className="hidden"
        />
      </nav>

      {/* Error */}
      {error && (
        <div className="mx-4 mt-3 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <span>⚠️</span>
            {error}
          </div>
          <button onClick={() => setError("")}>
            <X size={14} className="text-red-400" />
          </button>
        </div>
      )}

      {/* Upload State */}
      {!uploadedFile && (
        <div
          className="flex-1 flex flex-col items-center justify-center gap-5 m-4 border-2 border-dashed border-gray-300 rounded-2xl cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 active:bg-indigo-100 transition-all bg-white"
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="w-20 h-20 bg-indigo-50 rounded-3xl flex items-center justify-center">
            {uploading
              ? <Loader2 size={32} className="text-indigo-500 spinning" />
              : <Upload size={32} className="text-indigo-500" />
            }
          </div>
          <div className="text-center px-8">
            <p className="text-gray-800 font-semibold text-lg">
              {uploading ? "Processing document..." : "Upload a PDF"}
            </p>
            <p className="text-gray-400 text-sm mt-1 leading-relaxed">
              {uploading
                ? "Chunking and embedding your document..."
                : "Your document will be chunked, embedded, and made searchable using AI"
              }
            </p>
          </div>
          {!uploading && (
            <span className="text-sm text-indigo-600 font-medium bg-indigo-50 border border-indigo-200 px-5 py-2.5 rounded-xl">
              Browse Files
            </span>
          )}
        </div>
      )}

      {/* Chat Messages */}
      {uploadedFile && (
        <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-2.5 items-start ${msg.role === "user" ? "flex-row-reverse" : ""}`}
            >
              {/* Avatar */}
              <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${msg.role === "user"
                ? "bg-indigo-600"
                : "bg-white border-2 border-gray-200 shadow-sm"
                }`}>
                {msg.role === "user"
                  ? <User size={13} className="text-white" />
                  : <Bot size={13} className="text-indigo-600" />
                }
              </div>

              {/* Content */}
              <div className={`flex flex-col gap-1.5 ${msg.role === "user" ? "items-end" : "items-start"
                } max-w-[82%] sm:max-w-[75%]`}>

                {/* Bubble */}
                <div className={`px-4 py-3 rounded-2xl shadow-sm ${msg.role === "user"
                  ? "bg-indigo-600 text-white rounded-tr-sm"
                  : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm"
                  }`}>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                    {msg.text}
                  </p>

                  {/* Tools used */}
                  {msg.tools_used?.length > 0 && (
                    <div className="flex gap-1.5 flex-wrap mt-2 pt-2 border-t border-white/20">
                      {msg.tools_used.map((tool, i) => (
                        <span
                          key={i}
                          className="flex items-center gap-1 text-xs px-2 py-0.5 bg-indigo-50 border border-indigo-100 rounded-full text-indigo-600 font-medium"
                        >
                          <Wrench size={9} />
                          {tool}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Sources toggle */}
                {msg.sources?.length > 0 && (
                  <div className="w-full">
                    <button
                      className="flex items-center gap-1 text-xs text-gray-400 hover:text-indigo-500 active:text-indigo-600 transition-colors py-1"
                      onClick={() => toggleSources(index)}
                    >
                      {expandedSources[index]
                        ? <ChevronUp size={12} />
                        : <ChevronDown size={12} />
                      }
                      <span>{msg.sources.length} source chunks</span>
                    </button>

                    {expandedSources[index] && (
                      <div className="flex flex-col gap-2 mt-1">
                        {msg.sources.map((source, si) => (
                          <div
                            key={si}
                            className="p-3 bg-white border border-gray-200 rounded-xl shadow-sm"
                          >
                            <div className="flex items-center gap-2 flex-wrap mb-1.5">
                              <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                                Page {source.page}
                              </span>
                              <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                                Chunk {source.chunk_index}
                              </span>
                              {Number.isFinite(Number(source.score)) && (
                                <span className="text-xs bg-blue-50 text-blue-500 px-2 py-0.5 rounded-full">
                                  {Number(source.score).toFixed(3)}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-500 leading-relaxed break-words">
                              {source.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {asking && (
            <div className="flex gap-2.5 items-start">
              <div className="w-7 h-7 rounded-full bg-white border-2 border-gray-200 flex items-center justify-center shadow-sm shrink-0">
                <Bot size={13} className="text-indigo-600" />
              </div>
              <div className="px-4 py-3.5 bg-white border border-gray-200 rounded-2xl rounded-tl-sm shadow-sm">
                <div className="flex gap-1 items-center">
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Input Area */}
      {uploadedFile && (
        <div className="shrink-0 px-4 pb-4 pt-2">
          <div className="bg-white border border-gray-200 rounded-2xl shadow-sm flex items-end gap-2 p-3">
            <textarea
              ref={textareaRef}
              className="flex-1 outline-none text-gray-800 text-sm resize-none leading-relaxed placeholder-gray-400 bg-transparent max-h-28 min-h-[24px]"
              value={question}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your document..."
              rows={1}
            />
            <button
              className={`p-2.5 rounded-xl flex items-center justify-center shrink-0 transition-all ${asking || !question.trim()
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-indigo-600 text-white hover:bg-indigo-700 active:bg-indigo-800 shadow-sm"
                }`}
              onClick={handleAsk}
              disabled={asking || !question.trim()}
            >
              <Send size={15} />
            </button>
          </div>
          <p className="text-center text-xs text-gray-300 mt-2">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      )}
    </div>
  );
}
