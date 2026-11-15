import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  UploadCloud,
  Trophy,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Sparkles,
} from 'lucide-react';
import JdInputView from './components/JdInputView';
import ResumeUploadView from './components/ResumeUploadView';
import RankingDashboardView from './components/RankingDashboardView';
import CandidateDetailDrawer from './components/CandidateDetailDrawer';
import {
  getHealth,
  getJobRankings,
  getCandidateDetail,
  triggerJobMatch,
} from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState(1);
  const [currentJob, setCurrentJob] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [backendHealth, setBackendHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Drawer state
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerError, setDrawerError] = useState(null);
  const [rankingLoading, setRankingLoading] = useState(false);

  // Check health on load
  useEffect(() => {
    getHealth()
      .then((data) => {
        setBackendHealth(data);
        setHealthLoading(false);
      })
      .catch((err) => {
        setBackendHealth({ status: 'offline', error: err.message });
        setHealthLoading(false);
      });
  }, []);

  // When job is created/selected
  const handleJobCreated = (job) => {
    setCurrentJob(job);
    setActiveTab(2); // Advance to resume upload
  };

  // When upload completes
  const handleUploadComplete = (uploadData) => {
    // Ready for matching
  };

  // When matching completes
  const handleMatchingComplete = (matchData) => {
    setRankings(matchData.rankings || []);
    setActiveTab(3); // Advance to dashboard
  };

  // Reload rankings
  const handleReloadRankings = async () => {
    if (!currentJob?.id) return;
    setRankingLoading(true);
    try {
      const matchData = await triggerJobMatch(currentJob.id);
      setRankings(matchData.rankings || []);
    } catch (err) {
      console.error('Failed to recalculate rankings', err);
    } finally {
      setRankingLoading(false);
    }
  };

  // Open candidate drawer
  const handleSelectCandidate = async (candidateId) => {
    setIsDrawerOpen(true);
    setDrawerLoading(true);
    setDrawerError(null);
    try {
      const detail = await getCandidateDetail(candidateId);
      setSelectedCandidate(detail);
    } catch (err) {
      setDrawerError(err.response?.data?.detail || err.message || 'Could not load candidate details');
    } finally {
      setDrawerLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100/70 text-slate-900 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-black shadow-md shadow-blue-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-extrabold text-slate-900 tracking-tight">
                AI Resume Matching &amp; Ranking System
              </h1>
              <p className="text-[10px] text-slate-500 font-medium">
                Deterministic NLP • Semantic Embeddings • Multi-factor Scoring
              </p>
            </div>
          </div>

          {/* System Health Pill */}
          <div className="flex items-center space-x-2 text-xs">
            {healthLoading ? (
              <span className="text-slate-500 text-[11px]">Connecting...</span>
            ) : backendHealth?.status === 'healthy' ? (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-500" />
                API Online (v{backendHealth.version})
              </span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                <AlertCircle className="w-3.5 h-3.5 mr-1 text-rose-500" />
                Backend Offline
              </span>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8 -mb-px">
            <button
              onClick={() => setActiveTab(1)}
              className={`py-3 px-1 border-b-2 text-xs font-bold flex items-center space-x-2 transition-all ${
                activeTab === 1
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              <span>1. Job Description</span>
              {currentJob && (
                <span className="w-2 h-2 rounded-full bg-emerald-500 ml-1" />
              )}
            </button>

            <button
              onClick={() => setActiveTab(2)}
              className={`py-3 px-1 border-b-2 text-xs font-bold flex items-center space-x-2 transition-all ${
                activeTab === 2
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <UploadCloud className="w-4 h-4" />
              <span>2. Batch Resumes</span>
            </button>

            <button
              onClick={() => setActiveTab(3)}
              className={`py-3 px-1 border-b-2 text-xs font-bold flex items-center space-x-2 transition-all ${
                activeTab === 3
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <Trophy className="w-4 h-4" />
              <span>3. Rankings Dashboard</span>
              {rankings.length > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-blue-100 text-blue-800 font-bold ml-1">
                  {rankings.length}
                </span>
              )}
            </button>
          </nav>
        </div>
      </header>

      {/* Main View Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {activeTab === 1 && (
          <JdInputView onJobCreated={handleJobCreated} currentJob={currentJob} />
        )}

        {activeTab === 2 && (
          <ResumeUploadView
            currentJob={currentJob}
            onUploadComplete={handleUploadComplete}
            onMatchingComplete={handleMatchingComplete}
          />
        )}

        {activeTab === 3 && (
          <RankingDashboardView
            rankings={rankings}
            currentJob={currentJob}
            onSelectCandidate={handleSelectCandidate}
            onRecalculate={handleReloadRankings}
            loading={rankingLoading}
          />
        )}
      </main>

      {/* Module 5: Candidate Detail Slide-Over Drawer */}
      <CandidateDetailDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        candidate={selectedCandidate}
        loading={drawerLoading}
        error={drawerError}
      />
    </div>
  );
}
