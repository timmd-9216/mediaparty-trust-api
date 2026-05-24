"use client";

import { useState } from "react";
import { ArticleAnalyzer } from "./components/ArticleAnalyzer";
import { MetricsResults } from "./components/MetricsResults";
import { ScrapeResults } from "./components/ScrapeResults";
import { API_BASE_URL } from "./config";

interface Metric {
  id: number;
  criteria_name: string;
  explanation: string;
  flag: -1 | 0 | 1;
  score: number;
}

interface ScrapedData {
  title: string;
  body: string;
  author: string | null;
  editor: string | null;
  media_group: string | null;
  url: string;
}

export default function Home() {
  const [scrapedData, setScrapedData] = useState<ScrapedData | null>(null);
  const [metrics, setMetrics] = useState<Metric[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"url" | "text">("url");

  const handleScrape = async (url: string) => {
    setLoading(true);
    setError(null);
    setMetrics(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/scrape?url=${encodeURIComponent(url)}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setScrapedData(data);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al extraer el artículo");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (
    title: string,
    body: string,
    author: string,
    url: string
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title,
          body,
          author,
          link: url || "https://example.com",
          date: new Date().toISOString().split("T")[0],
          media_type: "news",
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al analizar el artículo");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setScrapedData(null);
    setMetrics(null);
    setError(null);
  };

  return (
    <main className="min-h-screen p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <header className="mb-8 text-center">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-800 mb-2">
            Prompt Tester
          </h1>
          <p className="text-slate-600">
            Itera y prueba métricas de análisis de noticias
          </p>
        </header>

        <ArticleAnalyzer
          onScrape={handleScrape}
          onAnalyze={handleAnalyze}
          onReset={handleReset}
          loading={loading}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 font-medium">Error</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}

        {scrapedData && (
          <ScrapeResults
            data={scrapedData}
            onEdit={(data) => setScrapedData(data)}
          />
        )}

        {metrics && <MetricsResults metrics={metrics} />}

        <footer className="mt-12 text-center text-slate-400 text-sm">
          <p>MediaParty Trust API - Herramienta de desarrollo de prompts</p>
        </footer>
      </div>
    </main>
  );
}
