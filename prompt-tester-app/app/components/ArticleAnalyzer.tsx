"use client";

import { useState, useEffect } from "react";
import { Link2, FileText, Loader2, Search, RotateCcw, Send } from "./icons";

interface ArticleAnalyzerProps {
  onScrape: (url: string) => Promise<{
    title: string;
    body: string;
    author: string | null;
    editor?: string | null;
    media_group?: string | null;
    url: string;
  } | null>;
  onAnalyze: (
    title: string,
    body: string,
    author: string,
    url: string,
    editor?: string | null,
    mediaGroup?: string | null
  ) => Promise<void>;
  onAnalyzeWithData?: (data: {
    title: string;
    body: string;
    author: string | null;
    editor: string | null;
    media_group: string | null;
    url: string;
  }) => Promise<void>;
  onReset: () => void;
  loading: boolean;
  activeTab: "url" | "text";
  setActiveTab: (tab: "url" | "text") => void;
}

export function ArticleAnalyzer({
  onScrape,
  onAnalyze,
  onAnalyzeWithData,
  onReset,
  loading,
  activeTab,
  setActiveTab,
}: ArticleAnalyzerProps) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [author, setAuthor] = useState("");
  const [scrapeLoading, setScrapeLoading] = useState(false);

  const handleScrape = async () => {
    if (!url.trim()) return;
    setScrapeLoading(true);
    const result = await onScrape(url);
    if (result) {
      setTitle(result.title);
      setBody(result.body);
      setAuthor(result.author || "");
      // Auto-analizar después de scrape exitoso con datos completos
      const dataWithDefaults = {
        ...result,
        editor: result.editor ?? null,
        media_group: result.media_group ?? null,
      };
      if (onAnalyzeWithData) {
        await onAnalyzeWithData(dataWithDefaults);
      } else {
        await onAnalyze(result.title, result.body, result.author || "", result.url, result.editor, result.media_group);
      }
    }
    setScrapeLoading(false);
  };

  const handleAnalyze = () => {
    if (!title.trim() || !body.trim()) return;
    onAnalyze(title, body, author, url, null, null);
  };

  const handleReset = () => {
    setUrl("");
    setTitle("");
    setBody("");
    setAuthor("");
    onReset();
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab("url")}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === "url"
              ? "text-primary-600 border-b-2 border-primary-600 bg-primary-50/50"
              : "text-slate-600 hover:text-slate-800 hover:bg-slate-50"
          }`}
        >
          <Link2 className="w-4 h-4" />
          Desde URL
        </button>
        <button
          onClick={() => setActiveTab("text")}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === "text"
              ? "text-primary-600 border-b-2 border-primary-600 bg-primary-50/50"
              : "text-slate-600 hover:text-slate-800 hover:bg-slate-50"
          }`}
        >
          <FileText className="w-4 h-4" />
          Texto manual
        </button>
      </div>

      <div className="p-6 space-y-4">
        {/* URL Input */}
        {activeTab === "url" && (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-700">
              URL de la noticia
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://ejemplo.com/noticia"
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all"
                disabled={scrapeLoading || loading}
              />
              <button
                onClick={handleScrape}
                disabled={!url.trim() || scrapeLoading || loading}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {scrapeLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                Extraer
              </button>
            </div>
          </div>
        )}

        {/* Title Input */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700">
            Título
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Título de la noticia"
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all"
            disabled={loading}
          />
        </div>

        {/* Author Input */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700">
            Autor
          </label>
          <input
            type="text"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Nombre del autor (opcional)"
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all"
            disabled={loading}
          />
        </div>

        {/* Body Textarea */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700">
            Cuerpo de la noticia
          </label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Contenido completo de la noticia..."
            rows={10}
            className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all resize-vertical font-mono text-sm"
            disabled={loading}
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button
            onClick={handleAnalyze}
            disabled={!title.trim() || !body.trim() || loading}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analizando...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Analizar
              </>
            )}
          </button>
          <button
            onClick={handleReset}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-3 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Limpiar
          </button>
        </div>
      </div>
    </div>
  );
}
