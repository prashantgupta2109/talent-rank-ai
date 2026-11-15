import React from 'react';
import {
  X,
  Mail,
  Phone,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Sparkles,
  Quote,
} from 'lucide-react';
import CircularScoreGauge from './CircularScoreGauge';
import ScoreBreakdownBar from './ScoreBreakdownBar';

export default function CandidateDetailDrawer({
  isOpen,
  onClose,
  candidate,
  loading,
  error,
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-sm transition-opacity">
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-white shadow-2xl border-l border-slate-200 flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/80">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                  Candidate Analysis
                </span>
                {candidate?.filename && (
                  <span className="text-xs text-slate-500 flex items-center">
                    <FileText className="w-3 h-3 mr-1" />
                    {candidate.filename}
                  </span>
                )}
              </div>
              <h2 className="text-xl font-bold text-slate-900 mt-1">
                {candidate?.name || 'Candidate Details'}
              </h2>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 mt-2">
                {candidate?.email && (
                  <span className="flex items-center">
                    <Mail className="w-3.5 h-3.5 mr-1 text-slate-500" />
                    {candidate.email}
                  </span>
                )}
                {candidate?.phone && (
                  <span className="flex items-center">
                    <Phone className="w-3.5 h-3.5 mr-1 text-slate-500" />
                    {candidate.phone}
                  </span>
                )}
                <span className="flex items-center font-medium text-slate-700">
                  <Clock className="w-3.5 h-3.5 mr-1 text-slate-500" />
                  {candidate?.total_years_experience?.toFixed(1) || '0.0'} Years Experience
                </span>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {loading ? (
              <div className="space-y-4 animate-pulse">
                <div className="h-28 bg-slate-100 rounded-xl" />
                <div className="h-40 bg-slate-100 rounded-xl" />
                <div className="h-32 bg-slate-100 rounded-xl" />
              </div>
            ) : error ? (
              <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start space-x-3">
                <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-500" />
                <div>
                  <p className="font-semibold">Failed to load candidate analysis</p>
                  <p className="text-xs mt-1 text-rose-600">{error}</p>
                </div>
              </div>
            ) : candidate ? (
              <>
                {/* Score Section */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-5 bg-gradient-to-br from-slate-50 to-white rounded-xl border border-slate-200/80 shadow-sm">
                  <div className="flex items-center justify-center border-b md:border-b-0 md:border-r border-slate-200/80 pb-4 md:pb-0 md:pr-4">
                    <CircularScoreGauge score={candidate.match_analysis?.overall_score || 0} />
                  </div>
                  <div className="md:col-span-2 space-y-1">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                      Scoring Factor Breakdown
                    </h3>
                    <ScoreBreakdownBar
                      skillScore={candidate.match_analysis?.skill_score || 0}
                      semanticScore={candidate.match_analysis?.semantic_score || 0}
                      experienceScore={candidate.match_analysis?.experience_score || 0}
                      educationScore={candidate.match_analysis?.education_score || 0}
                    />
                  </div>
                </div>

                {/* Why this score? */}
                {candidate.match_analysis?.reasons?.length > 0 && (
                  <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-100">
                    <div className="flex items-center space-x-2 mb-3">
                      <Sparkles className="w-4 h-4 text-blue-600" />
                      <h3 className="text-sm font-bold text-blue-900">
                        Why this matching score?
                      </h3>
                    </div>
                    <ul className="space-y-2">
                      {candidate.match_analysis.reasons.map((reason, idx) => (
                        <li key={idx} className="text-xs text-blue-950 flex items-start space-x-2">
                          <span className="text-blue-500 font-bold">•</span>
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Experience Comparison */}
                {candidate.match_analysis?.experience_comparison && (
                  <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Experience Comparison
                    </h3>
                    <div className="grid grid-cols-3 gap-4 text-center pt-2">
                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                        <div className="text-lg font-bold text-slate-800">
                          {candidate.match_analysis.experience_comparison.candidate_years} yrs
                        </div>
                        <div className="text-[11px] text-slate-500">Candidate Experience</div>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                        <div className="text-lg font-bold text-slate-800">
                          {candidate.match_analysis.experience_comparison.required_years} yrs
                        </div>
                        <div className="text-[11px] text-slate-500">Required Minimum</div>
                      </div>
                      <div className={`p-2.5 rounded-lg border ${
                        candidate.match_analysis.experience_comparison.meets_requirement
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50 border-rose-200 text-rose-800'
                      }`}>
                        <div className="text-lg font-bold">
                          {candidate.match_analysis.experience_comparison.difference > 0 ? '+' : ''}
                          {candidate.match_analysis.experience_comparison.difference} yrs
                        </div>
                        <div className="text-[11px]">
                          {candidate.match_analysis.experience_comparison.meets_requirement
                            ? 'Meets Criteria'
                            : 'Deficit'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Skills Analysis: Matched vs Missing */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Matched Skills */}
                  <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/30 space-y-3">
                    <div className="flex items-center space-x-1.5 text-emerald-800">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <h3 className="text-xs font-bold uppercase tracking-wider">
                        Matched Skills ({(candidate.match_analysis?.matched_skills?.length || 0) + (candidate.match_analysis?.semantically_matched_skills?.length || 0)})
                      </h3>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {candidate.match_analysis?.matched_skills?.map((skill) => (
                        <span
                          key={skill}
                          className="px-2.5 py-1 text-xs font-medium rounded-md bg-emerald-100 text-emerald-800 border border-emerald-200"
                        >
                          {skill}
                        </span>
                      ))}
                      {/* Semantically matched skills */}
                      {candidate.match_analysis?.semantically_matched_skills?.map((sem, idx) => (
                        <span
                          key={idx}
                          title={`Matched via semantic similarity (${Math.round(sem.similarity * 100)}%) with resume skill '${sem.resume_skill}'`}
                          className="px-2.5 py-1 text-xs font-medium rounded-md bg-teal-100 text-teal-800 border border-teal-300 flex items-center space-x-1 cursor-help"
                        >
                          <span>{sem.jd_skill}</span>
                          <span className="text-[10px] text-teal-600 font-semibold">
                            ≈ {sem.resume_skill}
                          </span>
                        </span>
                      ))}
                      {(!candidate.match_analysis?.matched_skills?.length &&
                        !candidate.match_analysis?.semantically_matched_skills?.length) && (
                        <span className="text-xs text-slate-500 italic">No matching skills detected</span>
                      )}
                    </div>
                  </div>

                  {/* Missing Skills */}
                  <div className="p-4 rounded-xl border border-rose-200 bg-rose-50/30 space-y-3">
                    <div className="flex items-center space-x-1.5 text-rose-800">
                      <XCircle className="w-4 h-4 text-rose-600" />
                      <h3 className="text-xs font-bold uppercase tracking-wider">
                        Missing Skills ({candidate.match_analysis?.missing_skills?.length || 0})
                      </h3>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {candidate.match_analysis?.missing_skills?.map((skill) => (
                        <span
                          key={skill}
                          className="px-2.5 py-1 text-xs font-medium rounded-md bg-rose-100 text-rose-800 border border-rose-200"
                        >
                          {skill}
                        </span>
                      ))}
                      {!candidate.match_analysis?.missing_skills?.length && (
                        <span className="text-xs text-emerald-700 font-medium">All required skills present!</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Evidence Chunks */}
                {candidate.match_analysis?.top_evidence_chunks?.length > 0 && (
                  <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3">
                    <div className="flex items-center space-x-1.5 text-slate-700">
                      <Quote className="w-4 h-4 text-slate-500" />
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        Top Semantic Evidence From Resume
                      </h3>
                    </div>
                    <div className="space-y-2.5">
                      {candidate.match_analysis.top_evidence_chunks.map((ev, i) => (
                        <div key={i} className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs space-y-1">
                          <p className="font-semibold text-slate-700">
                            JD: {ev.jd_requirement}
                          </p>
                          <p className="text-slate-600 italic bg-white p-2 rounded border border-slate-200/60">
                            "{ev.resume_snippet}"
                          </p>
                          <div className="text-[10px] text-right font-medium text-blue-600">
                            Similarity: {Math.round(ev.similarity_score * 100)}%
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-white hover:bg-slate-700 transition-colors shadow-sm"
            >
              Close Drawer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
