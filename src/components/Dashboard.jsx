import { AlertTriangle, ShieldCheck, HeartPulse, Activity } from 'lucide-react';

export default function Dashboard({ data, result, isAnalyzing }) {
  if (isAnalyzing || !result) {
    return (
      <div className="text-center animate-fade-in" style={{ padding: '4rem 0' }}>
        <Activity size={48} className="text-primary mb-4" style={{ animation: 'pulse 2s infinite' }} />
        <h3>{isAnalyzing ? 'AI đang phân tích dữ liệu...' : 'Chưa có dữ liệu phân tích'}</h3>
        <p style={{ color: '#94a3b8' }}>{isAnalyzing ? 'Quá trình này có thể mất vài giây. Vui lòng đợi.' : 'Hãy hoàn thành bài khảo sát để xem kết quả.'}</p>
      </div>
    );
  }

  const getRiskColor = (prob) => {
    if (prob === 'Cao') return 'text-danger';
    if (prob === 'Trung bình') return 'text-warning';
    return 'text-success';
  };

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-6">
        <h2 className="flex items-center gap-2 text-primary">
          <HeartPulse size={24} /> Báo cáo Sức khỏe AI
        </h2>
        <div className="glass-panel" style={{ padding: '0.5rem 1rem' }}>
          Điểm sức khỏe: <span className={result.score < 50 ? 'text-danger' : 'text-success'} style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{result.score}/100</span>
        </div>
      </div>

      <div className="glass-panel mb-8" style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
        <h3 className="flex items-center gap-2 text-danger mb-4">
          <AlertTriangle size={20} /> Các Nguy Cơ Tiềm Ẩn (Theo Lịch Trình Hiện Tại)
        </h3>
        <div className="grid-2">
          {result.risks.map((risk, index) => (
            <div key={index} className="glass-panel" style={{ background: 'rgba(15, 23, 42, 0.8)' }}>
              <div className="flex justify-between items-center mb-2">
                <strong style={{ fontSize: '1.1rem' }}>{risk.name}</strong>
                <span className={getRiskColor(risk.probability)} style={{ fontSize: '0.85rem', padding: '0.2rem 0.5rem', background: 'rgba(255,255,255,0.1)', borderRadius: '4px' }}>
                  Nguy cơ: {risk.probability}
                </span>
              </div>
              <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>
                Nguyên nhân: {risk.reason}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-panel" style={{ background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.3)' }}>
        <h3 className="flex items-center gap-2 text-success mb-2">
          <ShieldCheck size={20} /> Lời khuyên từ Chuyên gia AI
        </h3>
        <p style={{ color: '#f8fafc', lineHeight: 1.6 }}>
          {result.advice}
        </p>
      </div>
    </div>
  );
}
