import { useState } from 'react';
import { Send, Clock, Droplets, Moon, Activity } from 'lucide-react';

export default function SurveyForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    sleepTime: '23:00',
    wakeTime: '06:30',
    waterIntake: 2,
    meals: '3',
    showerTime: '19:00',
    screenTime: 5
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="animate-fade-in">
      <h2 className="flex items-center gap-2 text-primary mb-6">
        <Activity size={24} /> Nhật ký sinh hoạt
      </h2>
      <p style={{ color: '#cbd5e1', marginBottom: '2rem' }}>
        AI sẽ phân tích các thói quen dưới đây để dự báo nguy cơ và đưa ra các lời khuyên sức khỏe dành riêng cho bạn.
      </p>

      <form onSubmit={handleSubmit} className="grid-2">
        <div className="form-group">
          <label className="form-label flex items-center gap-2"><Moon size={16}/> Giờ đi ngủ thường xuyên</label>
          <input 
            type="time" 
            name="sleepTime" 
            className="form-input" 
            value={formData.sleepTime}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label className="form-label flex items-center gap-2"><Clock size={16}/> Giờ thức dậy</label>
          <input 
            type="time" 
            name="wakeTime" 
            className="form-input"
            value={formData.wakeTime}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label className="form-label flex items-center gap-2"><Droplets size={16}/> Lượng nước uống (lít/ngày)</label>
          <input 
            type="number" 
            name="waterIntake" 
            step="0.1" 
            min="0" 
            max="10"
            className="form-input"
            value={formData.waterIntake}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label className="form-label flex items-center gap-2"><Activity size={16}/> Số bữa ăn chính (bữa/ngày)</label>
          <select name="meals" className="form-input" value={formData.meals} onChange={handleChange}>
            <option value="1">1 bữa (Thường xuyên bỏ bữa)</option>
            <option value="2">2 bữa</option>
            <option value="3">3 bữa (Tiêu chuẩn)</option>
            <option value="4+">Nhiều hơn 3 bữa</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label flex items-center gap-2"><Droplets size={16}/> Giờ tắm thường xuyên</label>
          <input 
            type="time" 
            name="showerTime" 
            className="form-input"
            value={formData.showerTime}
            onChange={handleChange}
          />
          <small style={{ color: '#94a3b8', display: 'block', marginTop: '0.25rem' }}>Tắm khuya rất nguy hiểm</small>
        </div>

        <div className="form-group">
          <label className="form-label flex items-center gap-2"><Clock size={16}/> Thời gian nhìn màn hình (giờ/ngày)</label>
          <input 
            type="number" 
            name="screenTime" 
            min="0" 
            max="24"
            className="form-input"
            value={formData.screenTime}
            onChange={handleChange}
          />
        </div>

        <div className="form-group" style={{ gridColumn: '1 / -1', marginTop: '1rem' }}>
          <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
            <Send size={18} /> Phân tích Lịch trình
          </button>
        </div>
      </form>
    </div>
  );
}
