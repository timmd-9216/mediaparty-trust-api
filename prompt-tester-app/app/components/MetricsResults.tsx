"use client";

import { ThumbsUp, ThumbsDown, Minus, Award, AlertTriangle, FileText, Sparkles, Zap } from "./icons";

interface Metric {
  id: number;
  criteria_name: string;
  explanation: string;
  flag: -1 | 0 | 1;
  score: number;
}

interface MetricsResultsProps {
  metrics: Metric[];
}

const metricIcons: Record<string, React.ReactNode> = {
  "Adjective": <Sparkles className="w-5 h-5" />,
  "Word": <FileText className="w-5 h-5" />,
  "Sentence": <Zap className="w-5 h-5" />,
  "Verb": <Award className="w-5 h-5" />,
  "Title": <AlertTriangle className="w-5 h-5" />,
};

function getIconForMetric(name: string) {
  for (const [key, icon] of Object.entries(metricIcons)) {
    if (name.toLowerCase().includes(key.toLowerCase())) {
      return icon;
    }
  }
  return <Award className="w-5 h-5" />;
}

function FlagBadge({ flag }: { flag: -1 | 0 | 1 }) {
  if (flag === 1) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
        <ThumbsUp className="w-3 h-3" />
        Positivo
      </span>
    );
  }
  if (flag === -1) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
        <ThumbsDown className="w-3 h-3" />
        Negativo
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">
      <Minus className="w-3 h-3" />
      Neutral
    </span>
  );
}

function ScoreBar({ score }: { score: number }) {
  const percentage = Math.round(score * 100);
  let colorClass = "bg-slate-500";
  if (score >= 0.7) colorClass = "bg-green-500";
  else if (score >= 0.4) colorClass = "bg-amber-500";
  else colorClass = "bg-red-500";

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClass} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-sm font-medium text-slate-700 w-12 text-right">
        {percentage}%
      </span>
    </div>
  );
}

export function MetricsResults({ metrics }: MetricsResultsProps) {
  const averageScore = metrics.reduce((sum, m) => sum + m.score, 0) / metrics.length;

  return (
    <div className="mt-6">
      {/* Overall Score */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-700 rounded-xl p-6 text-white mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Puntuación general</h3>
            <p className="text-slate-300 text-sm">
              Promedio de todas las métricas evaluadas
            </p>
          </div>
          <div className="text-right">
            <span className="text-4xl font-bold">
              {Math.round(averageScore * 100)}%
            </span>
          </div>
        </div>
        <div className="mt-4 h-3 bg-slate-600 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              averageScore >= 0.7
                ? "bg-green-400"
                : averageScore >= 0.4
                ? "bg-amber-400"
                : "bg-red-400"
            }`}
            style={{ width: `${Math.round(averageScore * 100)}%` }}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 gap-4">
        {metrics.map((metric) => (
          <div
            key={metric.id}
            className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-4">
              <div className="p-2 bg-slate-100 rounded-lg text-slate-600">
                {getIconForMetric(metric.criteria_name)}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-slate-800">
                    {metric.criteria_name}
                  </h4>
                  <FlagBadge flag={metric.flag} />
                </div>
                <p className="text-slate-600 text-sm mb-3 leading-relaxed">
                  {metric.explanation}
                </p>
                <ScoreBar score={metric.score} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
