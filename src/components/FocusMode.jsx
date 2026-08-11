import { useState, useEffect } from 'react';
import { Eye, Coffee, Play, Square } from 'lucide-react';

export default function FocusMode() {
  const [isActive, setIsActive] = useState(false);
  const [mode, setMode] = useState('work'); // 'work' | 'rest'
  const [timeLeft, setTimeLeft] = useState(45 * 60);

  useEffect(() => {
    let interval = null;
    if (isActive && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((time) => time - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      if (mode === 'work') {
        setMode('rest');
        setTimeLeft(5 * 60);
      } else {
        setMode('work');
        setTimeLeft(45 * 60);
      }
    }
    return () => clearInterval(interval);
  }, [isActive, timeLeft, mode]);

  const toggleTimer = () => setIsActive(!isActive);
  
  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="animate-fade-in flex flex-col items-center">
      <h2 className="text-primary mb-2">Góc Tập Trung (Pomodoro 45/5)</h2>
      <p style={{ color: '#cbd5e1', marginBottom: '2rem', textAlign: 'center', maxWidth: '600px' }}>
        Phương pháp học 45 phút, nghỉ 5 phút kết hợp với các bài tập thư giãn giúp bảo vệ mắt và cột sống khỏi các tác hại của việc ngồi lâu.
      </p>

      {/* Timer Circle */}
      <div 
        className="flex items-center justify-center mb-8 mt-4"
        style={{
          width: '280px',
          height: '280px',
          borderRadius: '50%',
          border: `8px solid ${mode === 'work' ? 'var(--primary)' : 'var(--success)'}`,
          background: 'rgba(15, 23, 42, 0.6)',
          boxShadow: `0 0 40px ${mode === 'work' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)'}`,
          transition: 'all 0.5s ease'
        }}
      >
        <div className="text-center">
          <div style={{ fontSize: '4.5rem', fontWeight: 'bold', lineHeight: 1 }}>
            {formatTime(timeLeft)}
          </div>
          <div style={{ color: mode === 'work' ? 'var(--primary)' : 'var(--success)', marginTop: '1rem', fontWeight: '500', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '1.2rem' }}>
            {mode === 'work' ? <><Play size={20}/> Đang học tập</> : <><Coffee size={20}/> Đang nghỉ ngơi</>}
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        <button 
          className={`btn ${isActive ? 'btn-outline' : 'btn-primary'}`}
          onClick={toggleTimer}
          style={{ width: '150px' }}
        >
          {isActive ? <><Square size={18}/> Tạm dừng</> : <><Play size={18}/> Bắt đầu</>}
        </button>
        <button 
          className="btn btn-outline"
          onClick={() => { setIsActive(false); setTimeLeft(45*60); setMode('work'); }}
        >
          Làm mới
        </button>
      </div>
      
      {mode === 'rest' && (
        <div className="mt-8 p-6 glass-panel w-full animate-fade-in" style={{ maxWidth: '600px', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.3)' }}>
          <h3 className="text-success mb-4 flex items-center gap-2 justify-center">
            <Coffee size={24} /> Đã đến giờ giải lao (5 phút)
          </h3>
          <div className="grid-2 gap-4">
            <div className="glass-panel" style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '1rem' }}>
              <h4 className="flex items-center gap-2 text-primary mb-2"><Eye size={18} /> Thư giãn Mắt (20-20-20)</h4>
              <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>Rời mắt khỏi màn hình, nhìn ra xa ít nhất 6 mét (20 feet) trong vòng 20 giây và chớp mắt liên tục.</p>
            </div>
            <div className="glass-panel" style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '1rem' }}>
              <h4 className="flex items-center gap-2 text-primary mb-2"><Activity size={18} /> Vận động Cột sống</h4>
              <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>Đứng dậy khỏi ghế, vươn vai cao, đi vặn mình nhẹ nhàng và uống 1 ngụm nước lọc.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
