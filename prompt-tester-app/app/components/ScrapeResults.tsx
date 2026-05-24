"use client";

import { CheckCircle2, X, User, Building2, PenTool, ExternalLink } from "./icons";

interface ScrapedData {
  title: string;
  body: string;
  author: string | null;
  editor: string | null;
  media_group: string | null;
  url: string;
}

interface ScrapeResultsProps {
  data: ScrapedData;
  onEdit: (data: ScrapedData) => void;
}

export function ScrapeResults({ data, onEdit }: ScrapeResultsProps) {
  const hasAuthor = data.author && data.author.trim().length > 0;
  const hasEditor = data.editor && data.editor.trim().length > 0;
  const hasMediaGroup = data.media_group && data.media_group.trim().length > 0;

  return (
    <div className="mt-6 bg-slate-50 rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-semibold text-slate-800 mb-4">
        Datos extraídos
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* URL */}
        <div className="md:col-span-2 flex items-start gap-3 p-3 bg-white rounded-lg border border-slate-200">
          <ExternalLink className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-xs text-slate-500 uppercase tracking-wide">Fuente</p>
            <a
              href={data.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary-600 hover:underline truncate block"
            >
              {data.url}
            </a>
          </div>
        </div>

        {/* Author */}
        <div className={`flex items-start gap-3 p-3 rounded-lg border ${
          hasAuthor ? "bg-green-50 border-green-200" : "bg-white border-slate-200"
        }`}>
          {hasAuthor ? (
            <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
          ) : (
            <X className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
          )}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <User className="w-3 h-3" />
              Autor
            </p>
            <p className={`text-sm font-medium ${hasAuthor ? "text-green-800" : "text-slate-400"}`}>
              {hasAuthor ? data.author : "No encontrado"}
            </p>
          </div>
        </div>

        {/* Editor */}
        <div className={`flex items-start gap-3 p-3 rounded-lg border ${
          hasEditor ? "bg-green-50 border-green-200" : "bg-white border-slate-200"
        }`}>
          {hasEditor ? (
            <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
          ) : (
            <X className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
          )}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <PenTool className="w-3 h-3" />
              Editor responsable
            </p>
            <p className={`text-sm font-medium ${hasEditor ? "text-green-800" : "text-slate-400"}`}>
              {hasEditor ? data.editor : "No encontrado"}
            </p>
          </div>
        </div>

        {/* Media Group */}
        <div className={`flex items-start gap-3 p-3 rounded-lg border md:col-span-2 ${
          hasMediaGroup ? "bg-green-50 border-green-200" : "bg-white border-slate-200"
        }`}>
          {hasMediaGroup ? (
            <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
          ) : (
            <X className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
          )}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <Building2 className="w-3 h-3" />
              Grupo de medios
            </p>
            <p className={`text-sm font-medium ${hasMediaGroup ? "text-green-800" : "text-slate-400"}`}>
              {hasMediaGroup ? data.media_group : "No encontrado"}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 text-xs text-slate-500">
        <p>Los datos extraídos automáticamente pueden editarse directamente en los campos de arriba.</p>
      </div>
    </div>
  );
}
