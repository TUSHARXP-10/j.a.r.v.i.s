import React, { useState, useEffect } from 'react';
import './ScheduleModal.css';

const ScheduleModal = ({ isOpen, onClose, onSave, schedule = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    cron_expression: '',
    input_data: '{}',
    is_active: true
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (schedule) {
      setFormData({
        name: schedule.name,
        cron_expression: schedule.cron_expression,
        input_data: JSON.stringify(schedule.input_data || {}, null, 2),
        is_active: schedule.is_active
      });
    } else {
      setFormData({
        name: '',
        cron_expression: '',
        input_data: '{}',
        is_active: true
      });
    }
  }, [schedule]);

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Schedule name is required';
    }
    
    if (!formData.cron_expression.trim()) {
      newErrors.cron_expression = 'Cron expression is required';
    } else {
      // Basic cron validation (5 parts: min hour day month weekday)
      const cronParts = formData.cron_expression.split(' ');
      if (cronParts.length !== 5) {
        newErrors.cron_expression = 'Cron expression must have 5 parts (min hour day month weekday)';
      }
    }
    
    try {
      JSON.parse(formData.input_data);
    } catch (e) {
      newErrors.input_data = 'Invalid JSON format';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      try {
        const inputData = JSON.parse(formData.input_data);
        onSave({
          ...formData,
          input_data: inputData
        });
        onClose();
      } catch (e) {
        console.error('Error parsing JSON:', e);
      }
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error for this field
    setErrors(prev => ({
      ...prev,
      [field]: ''
    }));
  };

  const cronExamples = [
    { label: 'Every hour', value: '0 * * * *' },
    { label: 'Every day at midnight', value: '0 0 * * *' },
    { label: 'Every Monday at 9 AM', value: '0 9 * * 1' },
    { label: 'Every 15 minutes', value: '*/15 * * * *' },
    { label: 'Every 30 minutes', value: '*/30 * * * *' }
  ];

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{schedule ? 'Edit Schedule' : 'Create Schedule'}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Schedule Name:</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={errors.name ? 'error' : ''}
              placeholder="e.g., Daily Report Generation"
            />
            {errors.name && <span className="error-message">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="cron_expression">Cron Expression:</label>
            <input
              type="text"
              id="cron_expression"
              value={formData.cron_expression}
              onChange={(e) => handleInputChange('cron_expression', e.target.value)}
              className={errors.cron_expression ? 'error' : ''}
              placeholder="e.g., 0 9 * * 1 (Every Monday at 9 AM)"
            />
            {errors.cron_expression && <span className="error-message">{errors.cron_expression}</span>}
            
            <div className="cron-examples">
              <small>Common examples:</small>
              <div className="example-buttons">
                {cronExamples.map((example, index) => (
                  <button
                    key={index}
                    type="button"
                    className="example-button"
                    onClick={() => handleInputChange('cron_expression', example.value)}
                  >
                    {example.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="input_data">Input Data (JSON):</label>
            <textarea
              id="input_data"
              value={formData.input_data}
              onChange={(e) => handleInputChange('input_data', e.target.value)}
              className={errors.input_data ? 'error' : ''}
              rows={6}
              placeholder='{\n  "param1": "value1",\n  "param2": "value2"\n}'
            />
            {errors.input_data && <span className="error-message">{errors.input_data}</span>}
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => handleInputChange('is_active', e.target.checked)}
              />
              Active
            </label>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {schedule ? 'Update' : 'Create'} Schedule
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ScheduleModal;