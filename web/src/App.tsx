/**
 * Main App Component for Rightmove Property Analyzer
 * Coordinates all components and manages application state
 */

import React, { useState, useMemo, useCallback } from 'react';
import Papa from 'papaparse';
import { PropertyData } from './types';
import FileUpload from './components/FileUpload';
import PropertyTable from './components/PropertyTable';
import PropertyStatsPanel from './components/PropertyStatsPanel';
import PropertyCharts from './components/PropertyCharts';
import ErrorBoundary from './components/ErrorBoundary';
import { calculateStats } from './utils/dataUtils';


const App: React.FC = () => {
  const [properties, setProperties] = useState<PropertyData[]>([]);
  const [activeTab, setActiveTab] = useState<'table' | 'charts' | 'stats'>('table');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Calculate statistics for all properties (no filtering)
  const stats = useMemo(() => {
    return calculateStats(properties);
  }, [properties]);

  // Handle file upload
  const handleFileUpload = useCallback((file: File) => {
    setIsLoading(true);
    setError(null);

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        try {
          const data: PropertyData[] = results.data.map((row: any) => {
            const property: any = {};
            
            // Process each field with proper type conversion
            Object.keys(row).forEach(header => {
              let value: any = row[header];
              
              
              // Parse specific fields based on their expected types
              if (header === 'price' && value) {
                const parsed = parseFloat(value);
                value = isNaN(parsed) ? null : parsed;
              } else if (header === 'bedrooms' && value) {
                const parsed = parseInt(value);
                value = isNaN(parsed) ? null : parsed;
              } else if (header === 'bathrooms' && value) {
                const parsed = parseInt(value);
                value = isNaN(parsed) ? null : parsed;
              } else if (header === 'property_size_sqft' && value) {
                const parsed = parseFloat(value);
                value = isNaN(parsed) ? null : parsed;
              } else if (header === 'property_size_sqm' && value) {
                const parsed = parseFloat(value);
                if (isNaN(parsed)) {
                  console.warn(`Invalid property_size_sqm value: "${value}" (type: ${typeof value})`);
                  value = null;
                } else {
                  value = parsed;
                }
              } else if (header === 'scraping_success') {
                // Handle all common boolean string formats
                value = value === 'True' || value === 'true' || value === 'TRUE' || value === '1';
              } else if (header === 'letting_details' && value) {
                try {
                  // Handle both JSON and Python dict string formats
                  if (value.startsWith('{') && value.endsWith('}')) {
                    // Try JSON first
                    try {
                      value = JSON.parse(value);
                    } catch {
                      // If JSON fails, try to parse Python dict format safely
                      try {
                        // Replace Python-style quotes with JSON-style quotes
                        const jsonString = value
                          .replace(/'/g, '"')  // Replace single quotes with double quotes
                          .replace(/\bTrue\b/g, 'true')  // Replace Python True with JSON true
                          .replace(/\bFalse\b/g, 'false')  // Replace Python False with JSON false
                          .replace(/\bNone\b/g, 'null');  // Replace Python None with JSON null
                        value = JSON.parse(jsonString);
                      } catch {
                        // If all parsing fails, return empty object
                        value = {};
                      }
                    }
                  } else {
                    value = {};
                  }
                } catch {
                  value = {};
                }
              } else if (header === 'id' && value) {
                // Ensure id is always a string
                value = String(value);
              } else if (header === 'property_url' && value) {
                // Ensure property_url is always a string
                value = String(value);
              } else if (header === 'search_date' && value) {
                // Ensure search_date is always a string
                value = String(value);
              }
              
              property[header] = value;
            });
            
            return property as PropertyData;
          });
          
          setProperties(data);
          setIsLoading(false);
        } catch (error) {
          console.error('Error processing CSV data:', error);
          setError('Failed to process CSV data');
          setIsLoading(false);
        }
      },
      error: (error) => {
        console.error('Error parsing CSV:', error);
        setError('Failed to parse CSV file');
        setIsLoading(false);
      }
    });
  }, []);


  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-main">
            <h1>Rightmove Property Analyzer</h1>
            <p className="subtitle">
              Analyze and visualize property data from Rightmove scraper
            </p>
          </div>
          {properties.length > 0 && (
            <div className="header-actions">
              <button
                onClick={() => setProperties([])}
                className="clear-data-btn"
                title="Clear all data and start over"
              >
                🗑️ Clear Data
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="app-main">
        {properties.length === 0 ? (
          <div className="welcome-section">
            <FileUpload onFileUpload={handleFileUpload} isLoading={isLoading} />
            {error && (
              <div className="error-banner">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Tab Navigation */}
            <nav className="tab-navigation">
              <button
                className={`tab-button ${activeTab === 'table' ? 'active' : ''}`}
                onClick={() => setActiveTab('table')}
              >
                📊 Data Table
              </button>
              <button
                className={`tab-button ${activeTab === 'charts' ? 'active' : ''}`}
                onClick={() => setActiveTab('charts')}
              >
                📈 Charts & Graphs
              </button>
              <button
                className={`tab-button ${activeTab === 'stats' ? 'active' : ''}`}
                onClick={() => setActiveTab('stats')}
              >
                📋 Statistics
              </button>
            </nav>

            {/* Results Summary */}
            <div className="results-summary">
              <div className="summary-stats">
                <div className="stat-item">
                  <span className="stat-label">Total Properties:</span>
                  <span className="stat-value">{properties.length}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Success Rate:</span>
                  <span className="stat-value">
                    {stats.successRate.toFixed(1)}%
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Average Price:</span>
                  <span className="stat-value">
                    £{stats.averagePrice.toLocaleString()}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Average Size:</span>
                  <span className="stat-value">
                    {stats.averageSize.toFixed(1)} sq m
                  </span>
                </div>
              </div>
              <div className="summary-actions">
                <FileUpload onFileUpload={handleFileUpload} isLoading={isLoading} />
              </div>
            </div>

            {/* Tab Content */}
            <ErrorBoundary>
              {activeTab === 'table' && (
                <PropertyTable properties={properties} />
              )}

              {activeTab === 'charts' && (
                <PropertyCharts properties={properties} stats={stats} />
              )}

              {activeTab === 'stats' && (
                <PropertyStatsPanel stats={stats} properties={properties} />
              )}
            </ErrorBoundary>
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>
          Rightmove Property Analyzer | Powered by React & Recharts
        </p>
      </footer>
    </div>
  );
};

export default App;
