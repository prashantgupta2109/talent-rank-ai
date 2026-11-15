import React, { useState } from 'react';
import {
  Trophy,
  ArrowUpDown,
  Search,
  ChevronRight,
  Download,
  Eye,
  EyeOff,
  Sliders,
  Scale,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  XCircle,
  X,
} from 'lucide-react';

export default function RankingDashboardView({
  rankings = [],
  currentJob,
  onSelectCandidate,
  onRecalculate,
  loading,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('overall_score');
  const [sortAsc, setSortAsc] = useState(false);

  // Value-add states
  const [blindScreening, setBlindScreening] = useState(false);
  const [showWeightSliders, setShowWeightSliders] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [compareCandA, setCompareCandA] = useState(null);
  const [compareCandB, setCompareCandB] = useState(null);

  // Interactive weights (default 40 / 30 / 20 / 10)
  const [weights, setWeights] = useState({
    skills: 0.40,
    semantic: 0.30,
    experience: 0.20,
    education: 0.10,
  });

  // Calculate dynamic overall score if weights were adjusted
  const computedRankings = rankings.map((cand) => {
    // If weights sum to 1.0, calculate live composite score
    const skillScore = cand.skill_score || 0;
    const semanticScore = cand.semantic_score || 0;
    const experienceScore = cand.experience_score || (Math.min((cand.experience_years || 0) / 4.0, 1.0) * 100);
    const educationScore = cand.education_score || 80;

    const dynamicScore = (
      weights.skills * skillScore +
      weights.semantic * semanticScore +
      weights.experience * experienceScore +
      weights.education * educationScore
    );

    return {
      ...cand,
      dynamicScore: Math.round(Math.max(0, Math.min(100, dynamicScore))),
    };
  });

  // Sorting
  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  // Filter candidates
  const filtered = computedRankings.filter((item) => {
    const term = searchTerm.toLowerCase();
    const nameMatch = blindScreening ? false : item.candidate_name.toLowerCase().includes(term);
    const skillMatch = item.matched_skills?.some((s) => s.toLowerCase().includes(term));
    return nameMatch || skillMatch;
  });

  // Sort candidates
  const sorted = [...filtered].sort((a, b) => {
    let aVal = sortField === 'overall_score' ? a.dynamicScore : a[sortField];
    let bVal = sortField === 'overall_score' ? b.dynamicScore : b[sortField];

    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }

    if (aVal < bVal) return sortAsc ? -1 : 1;
    if (aVal > bVal) return sortAsc ? 1 : -1;
    return 0;
  });

  // CSV Export
  const exportToCSV = () => {
    if (!sorted.length) return;
    const headers = [
      'Rank',
      'Candidate Name',
      'Experience (Years)',
      'Match Score (%)',
      'Skills Score',
      'Semantic Score',
      'Matched Skills',
      'Missing Skills',
    ];

    const rows = sorted.map((c, idx) => [
      idx + 1,
      blindScreening ? `Candidate #${idx + 1}` : `"${c.candidate_name}"`,
      c.experience_years?.toFixed(1) || '0.0',
      c.dynamicScore,
      c.skill_score || 0,
      c.semantic_score || 0,
      `"${(c.matched_skills || []).join(', ')}"`,
      `"${(c.missing_skills || []).join(', ')}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `candidate_rankings_job_${currentJob?.id || 'export'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Open side-by-side compare
  const openCompareModal = () => {
    if (sorted.length >= 2) {
      setCompareCandA(sorted[0]);
      setCompareCandB(sorted[1]);
      setShowCompareModal(true);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center">
            <Trophy className="w-5 h-5 mr-2 text-amber-500" />
            Module 4: Candidate Ranking Dashboard
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Evaluating candidates against{' '}
            <span className="font-semibold text-slate-800">{currentJob?.title || 'Selected Job'}</span>.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Blind Screening Toggle */}
          <button
            onClick={() => setBlindScreening(!blindScreening)}
            title="Toggle Blind Screening to reduce unconscious bias"
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg border flex items-center transition-colors ${
              blindScreening
                ? 'bg-purple-100 text-purple-800 border-purple-300'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
            }`}
          >
            {blindScreening ? (
              <EyeOff className="w-3.5 h-3.5 mr-1.5 text-purple-600" />
            ) : (
              <Eye className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
            )}
            <span>Blind Screening {blindScreening ? 'ON' : 'OFF'}</span>
          </button>

          {/* Weight Sliders Toggle */}
          <button
            onClick={() => setShowWeightSliders(!showWeightSliders)}
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg border flex items-center transition-colors ${
              showWeightSliders
                ? 'bg-blue-100 text-blue-800 border-blue-300'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
            }`}
          >
            <Sliders className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
            <span>Tune Weights</span>
          </button>

          {/* Side-by-side Compare */}
          <button
            onClick={openCompareModal}
            disabled={sorted.length < 2}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 flex items-center disabled:opacity-50 transition-colors"
          >
            <Scale className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
            <span>Compare 2</span>
          </button>

          {/* Export CSV */}
          <button
            onClick={exportToCSV}
            disabled={sorted.length === 0}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 flex items-center disabled:opacity-50 transition-colors"
          >
            <Download className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Adjustable Weight Sliders Panel */}
      {showWeightSliders && (
        <div className="p-4 bg-white rounded-xl border border-blue-200 shadow-sm space-y-4 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-blue-600" />
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Live Weight Tuner (Rankings re-sort automatically)
              </h3>
            </div>
            <button
              onClick={() =>
                setWeights({ skills: 0.40, semantic: 0.30, experience: 0.20, education: 0.10 })
              }
              className="text-[11px] font-semibold text-blue-600 hover:underline"
            >
              Reset to Defaults (40/30/20/10)
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span>Skills Overlap</span>
                <span className="text-blue-600">{Math.round(weights.skills * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.skills}
                onChange={(e) => setWeights({ ...weights, skills: parseFloat(e.target.value) })}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span>Semantic Similarity</span>
                <span className="text-blue-600">{Math.round(weights.semantic * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.semantic}
                onChange={(e) => setWeights({ ...weights, semantic: parseFloat(e.target.value) })}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span>Experience Alignment</span>
                <span className="text-blue-600">{Math.round(weights.experience * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.experience}
                onChange={(e) => setWeights({ ...weights, experience: parseFloat(e.target.value) })}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span>Education Match</span>
                <span className="text-blue-600">{Math.round(weights.education * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.education}
                onChange={(e) => setWeights({ ...weights, education: parseFloat(e.target.value) })}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>
          </div>
        </div>
      )}

      {/* Filter / Search Bar */}
      <div className="flex items-center justify-between">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search candidate name or skill..."
            className="text-xs pl-9 pr-3 py-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 w-72 shadow-sm"
          />
        </div>

        <div className="text-xs text-slate-500">
          Showing <span className="font-bold text-slate-800">{sorted.length}</span> candidates
        </div>
      </div>

      {/* Leaderboard Table Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider font-bold border-b border-slate-200">
              <tr>
                <th className="py-3.5 px-4 w-16 text-center">Rank</th>
                <th
                  onClick={() => handleSort('candidate_name')}
                  className="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Candidate</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('experience_years')}
                  className="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Experience</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('overall_score')}
                  className="py-3.5 px-4 cursor-pointer hover:bg-slate-100 transition-colors w-52"
                >
                  <div className="flex items-center space-x-1">
                    <span>Match %</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th className="py-3.5 px-4">Matched Skills</th>
                <th className="py-3.5 px-4 text-center w-28">Action</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="p-4 text-center"><div className="h-4 bg-slate-100 rounded w-6 mx-auto" /></td>
                    <td className="p-4"><div className="h-4 bg-slate-100 rounded w-32" /></td>
                    <td className="p-4"><div className="h-4 bg-slate-100 rounded w-16" /></td>
                    <td className="p-4"><div className="h-4 bg-slate-100 rounded w-28" /></td>
                    <td className="p-4"><div className="h-4 bg-slate-100 rounded w-48" /></td>
                    <td className="p-4"><div className="h-4 bg-slate-100 rounded w-16 mx-auto" /></td>
                  </tr>
                ))
              ) : sorted.length > 0 ? (
                sorted.map((item, index) => {
                  const score = item.dynamicScore;
                  const rank = index + 1;

                  let barColor = 'bg-emerald-500';
                  let badgeBg = 'bg-emerald-50 text-emerald-800 border-emerald-200';
                  if (score < 60) {
                    barColor = 'bg-rose-500';
                    badgeBg = 'bg-rose-50 text-rose-800 border-rose-200';
                  } else if (score < 80) {
                    barColor = 'bg-amber-500';
                    badgeBg = 'bg-amber-50 text-amber-800 border-amber-200';
                  }

                  const displayName = blindScreening
                    ? `Candidate #${rank} (Anonymous)`
                    : item.candidate_name;

                  return (
                    <tr
                      key={item.candidate_id || index}
                      onClick={() => onSelectCandidate(item.candidate_id)}
                      className="hover:bg-blue-50/40 transition-colors cursor-pointer group"
                    >
                      {/* Rank */}
                      <td className="py-3.5 px-4 text-center font-bold text-slate-700">
                        {rank === 1 ? (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-100 text-amber-800 text-[11px]">
                            🥇
                          </span>
                        ) : rank === 2 ? (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-200 text-slate-800 text-[11px]">
                            🥈
                          </span>
                        ) : rank === 3 ? (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-100 text-orange-800 text-[11px]">
                            🥉
                          </span>
                        ) : (
                          `#${rank}`
                        )}
                      </td>

                      {/* Candidate Name & File */}
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                          {displayName}
                        </div>
                        {item.filename && !blindScreening && (
                          <div className="text-[10px] text-slate-500 truncate max-w-xs">
                            {item.filename}
                          </div>
                        )}
                      </td>

                      {/* Experience */}
                      <td className="py-3.5 px-4 font-semibold text-slate-700 whitespace-nowrap">
                        {item.experience_years?.toFixed(1) || '0.0'} years
                      </td>

                      {/* Match % with colored progress bar */}
                      <td className="py-3.5 px-4">
                        <div className="space-y-1">
                          <div className="flex justify-between items-center text-xs">
                            <span className="font-extrabold text-slate-800">{score}%</span>
                            <span className={`text-[10px] font-semibold px-1.5 py-0.2 rounded border ${badgeBg}`}>
                              {score >= 80 ? 'Strong' : score >= 60 ? 'Medium' : 'Weak'}
                            </span>
                          </div>
                          <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${barColor} transition-all duration-700`}
                              style={{ width: `${score}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Matched Skills Chips */}
                      <td className="py-3.5 px-4">
                        <div className="flex flex-wrap gap-1 max-w-md">
                          {item.matched_skills?.slice(0, 5).map((skill, sIdx) => (
                            <span
                              key={sIdx}
                              className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200"
                            >
                              {skill}
                            </span>
                          ))}
                          {(item.matched_skills?.length || 0) > 5 && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium text-slate-500 bg-slate-50">
                              +{(item.matched_skills?.length || 0) - 5} more
                            </span>
                          )}
                          {!item.matched_skills?.length && (
                            <span className="text-[11px] text-slate-500 italic">None matched</span>
                          )}
                        </div>
                      </td>

                      {/* Action */}
                      <td className="py-3.5 px-4 text-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectCandidate(item.candidate_id);
                          }}
                          className="px-2.5 py-1 text-[11px] font-semibold rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors inline-flex items-center"
                        >
                          <span>Analyze</span>
                          <ChevronRight className="w-3 h-3 ml-0.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <p className="text-sm font-semibold">No candidates ranked yet</p>
                    <p className="text-xs text-slate-500 mt-1">
                      Upload resumes in Module 2 and trigger AI matching to view candidate rankings.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Side-by-Side Candidate Comparison Modal */}
      {showCompareModal && compareCandA && compareCandB && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <Scale className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">
                  Side-by-Side Candidate Comparison
                </h3>
              </div>
              <button
                onClick={() => setShowCompareModal(false)}
                className="p-1 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Selectors for comparison */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="text-[11px] font-bold text-slate-500 uppercase block mb-1">
                  Candidate A
                </label>
                <select
                  value={compareCandA.candidate_id}
                  onChange={(e) => {
                    const c = sorted.find((x) => x.candidate_id === parseInt(e.target.value));
                    if (c) setCompareCandA(c);
                  }}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 font-semibold"
                >
                  {sorted.map((c) => (
                    <option key={c.candidate_id} value={c.candidate_id}>
                      {blindScreening ? `Candidate #${c.candidate_id}` : c.candidate_name} ({c.dynamicScore}%)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-500 uppercase block mb-1">
                  Candidate B
                </label>
                <select
                  value={compareCandB.candidate_id}
                  onChange={(e) => {
                    const c = sorted.find((x) => x.candidate_id === parseInt(e.target.value));
                    if (c) setCompareCandB(c);
                  }}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 font-semibold"
                >
                  {sorted.map((c) => (
                    <option key={c.candidate_id} value={c.candidate_id}>
                      {blindScreening ? `Candidate #${c.candidate_id}` : c.candidate_name} ({c.dynamicScore}%)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Comparison Cards */}
            <div className="grid grid-cols-2 gap-6">
              {/* Candidate A Card */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-4">
                <div className="text-center pb-2 border-b border-slate-200">
                  <div className="text-3xl font-extrabold text-blue-600">
                    {compareCandA.dynamicScore}%
                  </div>
                  <div className="text-xs font-bold text-slate-800 mt-1">
                    {blindScreening ? 'Candidate A' : compareCandA.candidate_name}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {compareCandA.experience_years?.toFixed(1)} yrs experience
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between font-medium">
                    <span className="text-slate-600">Skills Overlap:</span>
                    <span className="font-bold">{compareCandA.skill_score || 0}%</span>
                  </div>
                  <div className="flex justify-between font-medium">
                    <span className="text-slate-600">Semantic Alignment:</span>
                    <span className="font-bold">{compareCandA.semantic_score || 0}%</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-emerald-800 uppercase block">
                    Matched Skills ({compareCandA.matched_skills?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {compareCandA.matched_skills?.map((s) => (
                      <span key={s} className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-100 text-emerald-800">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-rose-800 uppercase block">
                    Missing Skills ({compareCandA.missing_skills?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {compareCandA.missing_skills?.map((s) => (
                      <span key={s} className="px-1.5 py-0.5 rounded text-[10px] bg-rose-100 text-rose-800">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Candidate B Card */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-4">
                <div className="text-center pb-2 border-b border-slate-200">
                  <div className="text-3xl font-extrabold text-blue-600">
                    {compareCandB.dynamicScore}%
                  </div>
                  <div className="text-xs font-bold text-slate-800 mt-1">
                    {blindScreening ? 'Candidate B' : compareCandB.candidate_name}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {compareCandB.experience_years?.toFixed(1)} yrs experience
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between font-medium">
                    <span className="text-slate-600">Skills Overlap:</span>
                    <span className="font-bold">{compareCandB.skill_score || 0}%</span>
                  </div>
                  <div className="flex justify-between font-medium">
                    <span className="text-slate-600">Semantic Alignment:</span>
                    <span className="font-bold">{compareCandB.semantic_score || 0}%</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-emerald-800 uppercase block">
                    Matched Skills ({compareCandB.matched_skills?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {compareCandB.matched_skills?.map((s) => (
                      <span key={s} className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-100 text-emerald-800">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-rose-800 uppercase block">
                    Missing Skills ({compareCandB.missing_skills?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {compareCandB.missing_skills?.map((s) => (
                      <span key={s} className="px-1.5 py-0.5 rounded text-[10px] bg-rose-100 text-rose-800">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
