/**
 * PropertyStatsPanel Component
 * Displays detailed statistics and analysis
 */

import React from 'react';
import { PropertyData, PropertyStats } from '../types';
import { TrendingUp, Home, DollarSign, Ruler } from 'lucide-react';

interface PropertyStatsPanelProps {
  stats: PropertyStats;
  properties: PropertyData[];
}

const PropertyStatsPanel: React.FC<PropertyStatsPanelProps> = ({ stats, properties }) => {
  const formatCurrency = (value: number) => `£${value.toLocaleString()}`;
  const formatNumber = (value: number, decimals: number = 0) => value.toFixed(decimals);

  const statCards = [
    {
      title: 'Total Properties',
      value: stats.totalProperties,
      icon: <Home size={24} />,
      color: 'blue',
    },
    {
      title: 'Average Price',
      value: formatCurrency(stats.averagePrice),
      icon: <DollarSign size={24} />,
      color: 'green',
    },
    {
      title: 'Median Price',
      value: formatCurrency(stats.medianPrice),
      icon: <DollarSign size={24} />,
      color: 'green',
    },
    {
      title: 'Price Range',
      value: `${formatCurrency(stats.minPrice)} - ${formatCurrency(stats.maxPrice)}`,
      icon: <TrendingUp size={24} />,
      color: 'purple',
    },
    {
      title: 'Average Size',
      value: `${formatNumber(stats.averageSize, 1)} sq m`,
      icon: <Ruler size={24} />,
      color: 'orange',
    },
    {
      title: 'Median Size',
      value: `${formatNumber(stats.medianSize, 1)} sq m`,
      icon: <Ruler size={24} />,
      color: 'orange',
    },
    {
      title: 'Size Range',
      value: `${formatNumber(stats.minSize, 1)} - ${formatNumber(stats.maxSize, 1)} sq m`,
      icon: <TrendingUp size={24} />,
      color: 'purple',
    },
    {
      title: 'Avg Price per sqm',
      value: formatCurrency(stats.averagePricePerSqm),
      icon: <DollarSign size={24} />,
      color: 'green',
    },
    {
      title: 'Median Price per sqm',
      value: formatCurrency(stats.medianPricePerSqm),
      icon: <DollarSign size={24} />,
      color: 'green',
    },
    {
      title: 'Scraping Success Rate',
      value: `${formatNumber(stats.successRate, 1)}%`,
      icon: <TrendingUp size={24} />,
      color: stats.successRate > 80 ? 'green' : stats.successRate > 60 ? 'orange' : 'red',
    },
  ];

  return (
    <div className="stats-panel">
      {/* Key Statistics Cards */}
      <div className="stats-grid">
        {statCards.map((card, index) => (
          <div key={index} className={`stat-card stat-card-${card.color}`}>
            <div className="stat-icon">{card.icon}</div>
            <div className="stat-content">
              <div className="stat-title">{card.title}</div>
              <div className="stat-value">{card.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Detailed Breakdowns */}
      <div className="stats-breakdown">
        {/* Bedroom Distribution */}
        <div className="breakdown-section">
          <h3>Bedroom Distribution</h3>
          <div className="breakdown-content">
            {Object.entries(stats.bedroomDistribution)
              .sort(([a], [b]) => parseInt(a) - parseInt(b))
              .map(([bedrooms, count]) => (
                <div key={bedrooms} className="breakdown-item">
                  <div className="breakdown-label">
                    {bedrooms} bedroom{bedrooms !== '1' ? 's' : ''}
                  </div>
                  <div className="breakdown-bar">
                    <div 
                      className="breakdown-fill"
                      style={{ 
                        width: `${(count / stats.totalProperties) * 100}%` 
                      }}
                    />
                  </div>
                  <div className="breakdown-value">
                    {count} ({((count / stats.totalProperties) * 100).toFixed(1)}%)
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Property Type Distribution */}
        <div className="breakdown-section">
          <h3>Property Type Distribution</h3>
          <div className="breakdown-content">
            {Object.entries(stats.propertyTypeDistribution)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => (
                <div key={type} className="breakdown-item">
                  <div className="breakdown-label">{type}</div>
                  <div className="breakdown-bar">
                    <div 
                      className="breakdown-fill"
                      style={{ 
                        width: `${(count / stats.totalProperties) * 100}%` 
                      }}
                    />
                  </div>
                  <div className="breakdown-value">
                    {count} ({((count / stats.totalProperties) * 100).toFixed(1)}%)
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Top Postcodes */}
        <div className="breakdown-section">
          <h3>Top Postcodes</h3>
          <div className="breakdown-content">
            {Object.entries(stats.postcodeDistribution)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 10)
              .map(([postcode, count]) => (
                <div key={postcode} className="breakdown-item">
                  <div className="breakdown-label">{postcode}</div>
                  <div className="breakdown-bar">
                    <div 
                      className="breakdown-fill"
                      style={{ 
                        width: `${(count / stats.totalProperties) * 100}%` 
                      }}
                    />
                  </div>
                  <div className="breakdown-value">
                    {count} ({((count / stats.totalProperties) * 100).toFixed(1)}%)
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Letting Details Analysis */}
        {Object.keys(stats.lettingDetailsStats).length > 0 && (
          <div className="breakdown-section">
            <h3>Letting Details Analysis</h3>
            <div className="letting-details-analysis">
              {Object.entries(stats.lettingDetailsStats).map(([detailType, values]) => (
                <div key={detailType} className="letting-detail-section">
                  <h4>{detailType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                  <div className="letting-detail-values">
                    {Object.entries(values)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 5)
                      .map(([value, count]) => (
                        <div key={value} className="letting-detail-item">
                          <span className="letting-value">{value}</span>
                          <span className="letting-count">{count}</span>
                        </div>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Data Quality Analysis */}
        <div className="breakdown-section">
          <h3>Data Quality Analysis</h3>
          <div className="data-quality-grid">
            <div className="quality-item">
              <div className="quality-label">Properties with Price Data</div>
              <div className="quality-value">
                {properties.filter(p => p.price !== null).length} / {properties.length}
                <span className="quality-percentage">
                  ({((properties.filter(p => p.price !== null).length / properties.length) * 100).toFixed(1)}%)
                </span>
              </div>
            </div>
            <div className="quality-item">
              <div className="quality-label">Properties with Size Data</div>
              <div className="quality-value">
                {properties.filter(p => p.property_size_sqm !== null).length} / {properties.length}
                <span className="quality-percentage">
                  ({((properties.filter(p => p.property_size_sqm !== null).length / properties.length) * 100).toFixed(1)}%)
                </span>
              </div>
            </div>
            <div className="quality-item">
              <div className="quality-label">Properties with Letting Details</div>
              <div className="quality-value">
                {properties.filter(p => p.letting_details && Object.keys(p.letting_details).length > 0).length} / {properties.length}
                <span className="quality-percentage">
                  ({((properties.filter(p => p.letting_details && Object.keys(p.letting_details).length > 0).length / properties.length) * 100).toFixed(1)}%)
                </span>
              </div>
            </div>
            <div className="quality-item">
              <div className="quality-label">Properties with Postcode</div>
              <div className="quality-value">
                {properties.filter(p => p.postcode !== null).length} / {properties.length}
                <span className="quality-percentage">
                  ({((properties.filter(p => p.postcode !== null).length / properties.length) * 100).toFixed(1)}%)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertyStatsPanel;
