import { useState, useEffect } from 'react';
import { Clock, Calendar, CheckCircle, Edit2, Save, Plus, Trash2 } from 'lucide-react';

export default function Schedule({ data, aiSchedule }) {
  const [scheduleItems, setScheduleItems] = useState([]);
  const [isEditing, setIsEditing] = useState(false);

  // Generate a smart schedule based on user's input
  useEffect(() => {
    if (aiSchedule && aiSchedule.length > 0) {
      setScheduleItems(aiSchedule);
    } else if (data) {
      // Basic AI-like mock logic to adjust unhealthy times if AI fails or isn't ready
      let wakeTime = data.wakeTime || '06:30';
      let sleepTime = data.sleepTime || '23:00';
      let showerTime = data.showerTime || '19:00';
      
      // Prevent late sleeping
      if (sleepTime > '23:30' || sleepTime < '05:00') {
        sleepTime = '23:00';
      }
      // Prevent late showering
      if (showerTime > '21:30' || showerTime < '05:00') {
        showerTime = '20:00';
      }

      const generated = [
        { id: 1, time: wakeTime, activity: 'Thức dậy & Uống 1 cốc nước ấm', type: 'health' },
        { id: 2, time: addMinutes(wakeTime, 15), activity: 'Tập thể dục nhẹ nhàng (15p) - Khởi động cơ thể', type: 'health' },
        { id: 3, time: addMinutes(wakeTime, 45), activity: 'Ăn sáng đầy đủ dinh dưỡng', type: 'meal' },
        { id: 4, time: '08:30', activity: 'Học tập / Làm việc (Focus Mode 45p)', type: 'work' },
        { id: 5, time: '09:15', activity: 'Nghỉ giải lao 5p: Nhìn xa 20m, chớp mắt 20 lần', type: 'relax' },
        { id: 6, time: '09:20', activity: 'Học tập / Làm việc (Focus Mode 45p)', type: 'work' },
        { id: 7, time: '12:00', activity: 'Ăn trưa & Nghỉ trưa', type: 'meal' },
        { id: 8, time: '13:30', activity: 'Học tập chiều (Focus Mode 45p)', type: 'work' },
        { id: 9, time: '14:15', activity: 'Nghỉ 5p: Đứng dậy vươn vai, uống nước', type: 'relax' },
        { id: 10, time: '17:30', activity: 'Hoạt động thể thao ngoài trời', type: 'health' },
        { id: 11, time: showerTime, activity: 'Tắm nước ấm (Đã điều chỉnh tránh tắm khuya)', type: 'health' },
        { id: 12, time: '19:30', activity: 'Ăn tối nhẹ nhàng', type: 'meal' },
        { id: 13, time: addMinutes(sleepTime, -60), activity: 'Thư giãn: Không dùng thiết bị điện tử, đọc sách', type: 'relax' },
        { id: 14, time: sleepTime, activity: 'Đi ngủ', type: 'health' },
      ];
      setScheduleItems(generated);
    } else {
      // Default if no survey data
      setScheduleItems([
        { id: 1, time: '06:00', activity: 'Thức dậy & Uống 1 cốc nước ấm', type: 'health' },
        { id: 2, time: '08:00', activity: 'Học tập / Làm việc (Focus Mode)', type: 'work' },
        { id: 3, time: '08:45', activity: 'Nghỉ giải lao: Vận động nhẹ, cho mắt nghỉ', type: 'relax' },
        { id: 4, time: '12:00', activity: 'Ăn trưa & Nghỉ ngơi', type: 'meal' },
        { id: 5, time: '17:30', activity: 'Hoạt động thể thao', type: 'health' },
        { id: 6, time: '22:30', activity: 'Đi ngủ', type: 'health' },
      ]);
    }
  }, [data, aiSchedule]);

  // Helper to add minutes to a "HH:MM" string
  const addMinutes = (timeStr, minsToAdd) => {
    if (!timeStr) return '';
    let [h, m] = timeStr.split(':').map(Number);
    let date = new Date();
    date.setHours(h, m + minsToAdd, 0, 0);
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  };

  const getColor = (type) => {
    switch(type) {
      case 'health': return 'var(--success)';
      case 'meal': return 'var(--warning)';
      case 'work': return 'var(--primary)';
      case 'relax': return '#a855f7'; // purple
      default: return '#94a3b8';
    }
  };

  const handleItemChange = (id, field, value) => {
    setScheduleItems(items => items.map(item => 
      item.id === id ? { ...item, [field]: value } : item
    ));
  };

  const handleDelete = (id) => {
    setScheduleItems(items => items.filter(item => item.id !== id));
  };

  const handleAdd = () => {
    const newId = Math.max(...scheduleItems.map(i => i.id), 0) + 1;
    setScheduleItems([...scheduleItems, { id: newId, time: '12:00', activity: 'Hoạt động mới', type: 'health' }]);
  };

  // Sort before displaying if not editing
  const sortedItems = [...scheduleItems].sort((a, b) => a.time.localeCompare(b.time));

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="flex items-center gap-2 text-success mb-2">
            <Calendar size={24} /> Lịch Trình Healthy Đề Xuất
          </h2>
          <p style={{ color: '#cbd5e1', margin: 0 }}>
            {data ? 'AI đã dựa trên khung giờ của bạn để chèn thêm các hoạt động bảo vệ mắt và sức khỏe.' : 'Đây là lịch trình mẫu. Hãy làm khảo sát để AI tối ưu riêng cho bạn!'}
          </p>
        </div>
        <button 
          className={`btn ${isEditing ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setIsEditing(!isEditing)}
        >
          {isEditing ? <><Save size={18} /> Lưu Lịch trình</> : <><Edit2 size={18} /> Chỉnh sửa</>}
        </button>
      </div>

      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        {(isEditing ? scheduleItems : sortedItems).map((item, index) => (
          <div 
            key={item.id} 
            className="flex items-center gap-4" 
            style={{ 
              padding: '1rem 1.5rem', 
              borderBottom: index < scheduleItems.length - 1 ? '1px solid var(--glass-border)' : 'none',
              background: index % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
              transition: 'all 0.2s'
            }}
          >
            {isEditing ? (
              <>
                <input 
                  type="time" 
                  value={item.time} 
                  onChange={(e) => handleItemChange(item.id, 'time', e.target.value)}
                  className="form-input"
                  style={{ width: '120px', padding: '0.5rem' }}
                />
                <input 
                  type="text" 
                  value={item.activity} 
                  onChange={(e) => handleItemChange(item.id, 'activity', e.target.value)}
                  className="form-input"
                  style={{ flex: 1, padding: '0.5rem' }}
                />
                <select 
                  value={item.type} 
                  onChange={(e) => handleItemChange(item.id, 'type', e.target.value)}
                  className="form-input"
                  style={{ width: '140px', padding: '0.5rem' }}
                >
                  <option value="health">Sức khỏe</option>
                  <option value="work">Học tập</option>
                  <option value="meal">Ăn uống</option>
                  <option value="relax">Thư giãn</option>
                </select>
                <button 
                  onClick={() => handleDelete(item.id)}
                  style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: '0.5rem' }}
                >
                  <Trash2 size={20} />
                </button>
              </>
            ) : (
              <>
                <div style={{ color: getColor(item.type), fontWeight: 'bold', width: '60px' }}>
                  {item.time}
                </div>
                <div style={{ flex: 1 }}>
                  {item.activity}
                </div>
                <CheckCircle size={18} style={{ color: '#475569', cursor: 'pointer' }} />
              </>
            )}
          </div>
        ))}
      </div>
      
      {isEditing && (
        <div className="mt-4">
          <button className="btn btn-outline" onClick={handleAdd} style={{ width: '100%', borderStyle: 'dashed' }}>
            <Plus size={18} /> Thêm hoạt động
          </button>
        </div>
      )}
      
      {!isEditing && (
        <div className="mt-8 text-center">
          <button className="btn btn-success">Áp dụng Lịch trình này vào Focus Mode</button>
        </div>
      )}
    </div>
  );
}
