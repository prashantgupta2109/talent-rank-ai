import React from 'react';
import { Cpu, Brain, Clock, GraduationCap } from 'lucide-react';

export default function ScoreBreakdownBar({
  skillScore = 0,
  semanticScore = 0,
  experienceScore = 0,
  educationScore = 0,
}) {
  const factors = [
    {
      name: 'Skills Overlap',
      weight: '40%',
      score: skillScore,
      icon: Cpu,
      color: 'bg-indigo-600',
      barBg: 'bg-indigo-100',
    },
    {
      name: 'Semantic Alignment',
      weight: '30%',
      score: semanticScore,
      icon: Brain,
      color: 'bg-blue-600',
      barBg: 'bg-blue-100',
    },
    {
      name: 'Experience Depth',
      weight: '20%',
      score: experienceScore,
      icon: Clock,
      color: 'bg-emerald-600',
      barBg: 'bg-emerald-100',
    },
    {
      name: 'Education Match',
      weight: '10%',
      score: educationScore,
      icon: GraduationCap,
      color: 'bg-purple-600',
      barBg: 'bg-purple-100',
    },
  ];

  return (
    <div className="space-y-4">
      {factors.map((f) => {
        const Icon = f.icon;
        const val = Math.max(0, Math.min(100, f.score || 0));
        return (
          <div key={f.name} className="space-y-1">
            <div className="flex items-center justify-between text-xs font-medium">
              <div className="flex items-center space-x-1.5 text-slate-700">
                <Icon className="w-3.5 h-3.5 text-slate-500" />
                <span>{f.name}</span>
                <span className="text-[10px] text-slate-500">({f.weight})</span>
              </div>
              <span className="font-bold text-slate-800">{Math.round(val)}%</span>
            </div>
            <div className={`w-full h-2.5 rounded-full ${f.barBg} overflow-hidden`}>
              <div
                className={`h-full rounded-full ${f.color} transition-all duration-700 ease-out`}
                style={{ width: `${val}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
