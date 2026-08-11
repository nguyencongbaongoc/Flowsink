import { useState } from 'react';
import { Activity, Brain, Clock, Settings, User, Key } from 'lucide-react';
import { analyzeScheduleWithGemini } from './services/gemini';
import SurveyForm from './components/SurveyForm';
import Dashboard from './components/Dashboard';
import FocusMode from './components/FocusMode';
import Schedule from './components/Schedule';
import './App.css'; // Remove or empty this if we are using index.css primarily

function App() {
  const [activeTab, setActiveTab] = useState('survey');
  const [surveyData, setSurveyData] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  const [apiKey, setApiKey] = useState(import.meta.env.VITE_GEMINI_API_KEY || '');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleSurveySubmit = async (data) => {
    setSurveyData(data);

    const trimmedKey = (apiKey || '').trim();

    if (!trimmedKey) {
      alert("Vui lòng nhập Gemini API Key ở góc trên bên phải trước khi phân tích!");
      return;
    }

    setIsAnalyzing(true);
    setActiveTab('dashboard');

    try {
      const result = await analyzeScheduleWithGemini(data, trimmedKey);
      setAnalysisResult(result);
    } catch (error) {
      alert(error.message);
      setAnalysisResult(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="container">
      <header className="glass-panel flex justify-between items-center mb-8">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-blue-500 rounded-lg text-white" style={{ background: 'var(--primary)' }}>
            <Activity size={28} />
          </div>
          <div>
            <h1 style={{ margin: 0 }}>FocusMate</h1>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: 0 }}>AI Health & Routine Optimizer</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-800/50 px-3 py-1.5 rounded-lg border border-slate-700">
            <Key size={16} className="text-primary" />
            <input
              type="password"
              placeholder="Nhập Gemini API Key..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: 'white', outline: 'none', width: '200px', fontSize: '0.9rem' }}
            />
          </div>
          <button className="btn btn-outline"><User size={18} /> Hồ sơ</button>
        </div>
      </header>

      <main>
        <div className="tabs glass-panel" style={{ padding: '0 1rem', borderBottomLeftRadius: 0, borderBottomRightRadius: 0, marginBottom: 0 }}>
          <div
            className={`tab flex items-center gap-2 ${activeTab === 'survey' ? 'active' : ''}`}
            onClick={() => setActiveTab('survey')}
          >
            <Brain size={18} /> Khảo sát Lịch trình
          </div>
          <div
            className={`tab flex items-center gap-2 ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={18} /> Đánh giá Sức khỏe
          </div>
          <div
            className={`tab flex items-center gap-2 ${activeTab === 'schedule' ? 'active' : ''}`}
            onClick={() => setActiveTab('schedule')}
          >
            <Clock size={18} /> Lịch đề xuất mới
          </div>
          <div
            className={`tab flex items-center gap-2 ${activeTab === 'focus' ? 'active' : ''}`}
            onClick={() => setActiveTab('focus')}
          >
            <Clock size={18} /> Focus Mode (Eye Care)
          </div>
        </div>

        <div className="glass-panel" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0, borderTop: 'none' }}>
          {activeTab === 'survey' && <SurveyForm onSubmit={handleSurveySubmit} />}
          {activeTab === 'dashboard' && <Dashboard data={surveyData} result={analysisResult} isAnalyzing={isAnalyzing} />}
          {activeTab === 'schedule' && <Schedule data={surveyData} aiSchedule={analysisResult?.schedule} />}
          {activeTab === 'focus' && <FocusMode />}
        </div>
      </main>
    </div>
  );
}

export default App;
