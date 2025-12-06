/**
 * LettingDetailsModal Component
 * Displays full letting details in a modal dialog
 */

import React from 'react';
import { LettingDetailsModalProps } from '../types';
import { X, Calendar, DollarSign, Clock, Home, Shield, FileText } from 'lucide-react';

const LettingDetailsModal: React.FC<LettingDetailsModalProps> = ({
  isOpen,
  onClose,
  lettingDetails,
  propertyAddress
}) => {
  if (!isOpen) return null;

  const getIconForKey = (key: string) => {
    const lowerKey = key.toLowerCase();
    if (lowerKey.includes('date') || lowerKey.includes('available')) {
      return <Calendar size={16} />;
    } else if (lowerKey.includes('deposit') || lowerKey.includes('price')) {
      return <DollarSign size={16} />;
    } else if (lowerKey.includes('tenancy') || lowerKey.includes('min')) {
      return <Clock size={16} />;
    } else if (lowerKey.includes('type') || lowerKey.includes('furnish')) {
      return <Home size={16} />;
    } else if (lowerKey.includes('council') || lowerKey.includes('tax')) {
      return <Shield size={16} />;
    } else {
      return <FileText size={16} />;
    }
  };

  const formatValue = (key: string, value: string) => {
    // Handle null/undefined values
    if (!value || typeof value !== 'string') {
      return 'N/A';
    }
    
    // Clean up deposit values that have extra text (fallback for any missed cases)
    if (key.toLowerCase().includes('deposit')) {
      return value
        .replace(/A deposit provides security for a landlord.*$/i, '')
        .replace(/Read moreaboutdepositin our glossary page.*$/i, '')
        .replace(/Read more about deposit in our glossary page.*$/i, '')
        .replace(/Read more.*glossary.*$/i, '')
        .replace(/aboutdepositin.*$/i, '')
        .trim();
    }
    return value;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Letting Details</h3>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        <div className="modal-body">
          <div className="property-address">
            <strong>{propertyAddress}</strong>
          </div>
          
          <div className="letting-details-grid">
            {Object.entries(lettingDetails).map(([key, value]) => (
              <div key={key} className="letting-detail-row">
                <div className="letting-detail-key">
                  {getIconForKey(key)}
                  <span>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                </div>
                <div className="letting-detail-value">
                  {formatValue(key, value)}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default LettingDetailsModal;
