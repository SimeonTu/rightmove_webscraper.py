/**
 * PropertyCharts Component
 * Displays various charts and graphs for property data analysis
 */

import React, { useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
} from 'recharts';
import { PropertyData, PropertyStats } from '../types';
import {
  distributionToChartData,
  createPriceRangeData,
  createSizeRangeData,
  createPricePerSqmData,
} from '../utils/dataUtils';

interface PropertyChartsProps {
  properties: PropertyData[];
  stats: PropertyStats;
}

const COLORS = [
  '#8884d8',
  '#82ca9d',
  '#ffc658',
  '#ff7300',
  '#00ff00',
  '#0088fe',
  '#00c49f',
  '#ffbb28',
  '#ff8042',
  '#8884d8',
];

const PropertyCharts: React.FC<PropertyChartsProps> = ({ properties, stats }) => {
  // Prepare chart data
  const bedroomData = useMemo(() => 
    distributionToChartData(stats.bedroomDistribution), 
    [stats.bedroomDistribution]
  );

  const propertyTypeData = useMemo(() => 
    distributionToChartData(stats.propertyTypeDistribution), 
    [stats.propertyTypeDistribution]
  );

  const postcodeData = useMemo(() => 
    distributionToChartData(stats.postcodeDistribution).slice(0, 10), 
    [stats.postcodeDistribution]
  );

  const priceRangeData = useMemo(() => 
    createPriceRangeData(properties, 8), 
    [properties]
  );

  const sizeRangeData = useMemo(() => 
    createSizeRangeData(properties, 8), 
    [properties]
  );

  const pricePerSqmData = useMemo(() => 
    createPricePerSqmData(properties, 8), 
    [properties]
  );

  // Price vs Size scatter data - convert weekly prices to monthly
  const priceSizeData = useMemo(() => {
    return properties
      .filter(p => p.price !== null && p.property_size_sqm !== null && p.property_size_sqm > 0)
      .map(p => {
        const price = Number(p.price);
        const frequency = p.frequency?.toLowerCase();
        
        // Convert weekly prices to monthly for consistent comparison
        const monthlyPrice = frequency === 'weekly' ? price * 4.33 : price;
        
        return {
          price: monthlyPrice,
          size: p.property_size_sqm!,
          bedrooms: p.bedrooms || 0,
          property_type: p.property_type || 'Unknown',
          property_url: p.property_url,
          address: p.address || 'Unknown Address',
        };
      });
  }, [properties]);

  // Handle dot click to open property page
  const handleDotClick = (data: any) => {
    if (data && data.property_url) {
      window.open(data.property_url, '_blank', 'noopener,noreferrer');
    }
  };

  // Scaling mode state
  const [scalingMode, setScalingMode] = useState<'auto' | 'full'>('auto');

  // Calculate Y-axis domain based on scaling mode
  const getYAxisDomain = () => {
    if (scalingMode === 'auto' && priceSizeData.length > 0) {
      const prices = priceSizeData.map(d => d.price);
      const minPrice = Math.min(...prices);
      const maxPrice = Math.max(...prices);
      const padding = (maxPrice - minPrice) * 0.1; // 10% padding
      return [Math.max(0, minPrice - padding), maxPrice + padding] as [number, number];
    } else if (scalingMode === 'full') {
      return [0, 'dataMax'] as [number, string];
    }
    return ['dataMin', 'dataMax'] as [string, string];
  };

  // Price per sqm by bedrooms
  const pricePerSqmByBedrooms = useMemo(() => {
    const bedroomGroups: Record<number, number[]> = {};
    
    properties
      .filter(p => p.price !== null && p.property_size_sqm !== null && p.property_size_sqm > 0 && p.bedrooms !== null)
      .forEach(p => {
        const bedrooms = p.bedrooms!;
        const pricePerSqm = p.price! / p.property_size_sqm!;
        
        if (!bedroomGroups[bedrooms]) {
          bedroomGroups[bedrooms] = [];
        }
        bedroomGroups[bedrooms].push(pricePerSqm);
      });

    return Object.entries(bedroomGroups).map(([bedrooms, prices]) => ({
      bedrooms: parseInt(bedrooms),
      average: prices.reduce((a, b) => a + b, 0) / prices.length,
      median: prices.sort((a, b) => a - b)[Math.floor(prices.length / 2)],
      count: prices.length,
    })).sort((a, b) => a.bedrooms - b.bedrooms);
  }, [properties]);

  if (properties.length === 0) {
    return (
      <div className="empty-state">
        <p>No data available for charts. Upload a CSV file to get started.</p>
      </div>
    );
  }

  return (
    <div className="charts-container">
      <div className="charts-grid">
        {/* Price Distribution */}
        <div className="chart-card">
          <h3>Price Distribution</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={priceRangeData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={11}
                  interval={0}
                />
                <YAxis fontSize={12} />
                <Tooltip 
                  formatter={(value: any) => [`${value} properties`, 'Count']}
                  labelFormatter={(label) => `Price Range: ${label}`}
                />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Size Distribution */}
        <div className="chart-card">
          <h3>Property Size Distribution</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sizeRangeData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={11}
                  interval={0}
                />
                <YAxis fontSize={12} />
                <Tooltip 
                  formatter={(value: any) => [`${value} properties`, 'Count']}
                  labelFormatter={(label) => `Size Range: ${label}`}
                />
                <Bar dataKey="value" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bedroom Distribution */}
        <div className="chart-card">
          <h3>Bedroom Distribution</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <Pie
                  data={bedroomData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} beds (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={70}
                  fill="#8884d8"
                  dataKey="value"
                >
                      {bedroomData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                </Pie>
                <Tooltip 
                  formatter={(value: any, _: string, props: any) => [
                    `${value} properties`,
                    props.payload.name
                  ]}
                  labelFormatter={(label: string, payload: any) => {
                    if (payload && payload[0]) {
                      const data = payload[0].payload;
                      const percentage = ((data.value / properties.length) * 100).toFixed(1);
                      return `${data.name} bed${data.name === '1' ? '' : 's'} (${percentage}%)`;
                    }
                    return label;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Property Type Distribution */}
        <div className="chart-card">
          <h3>Property Type Distribution</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <Pie
                  data={propertyTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={70}
                  fill="#8884d8"
                  dataKey="value"
                >
                      {propertyTypeData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                </Pie>
                <Tooltip 
                  formatter={(value: any, _: string, props: any) => [
                    `${value} properties`,
                    props.payload.name
                  ]}
                  labelFormatter={(label: string, payload: any) => {
                    if (payload && payload[0]) {
                      const data = payload[0].payload;
                      const percentage = ((data.value / properties.length) * 100).toFixed(1);
                      return `${data.name} (${percentage}%)`;
                    }
                    return label;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Price vs Size Scatter */}
        <div className="chart-card chart-wide">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>Price vs Property Size <span style={{ fontSize: '12px', fontWeight: 'normal', color: '#666' }}>(Click dots to view properties)</span></h3>
            <div className="chart-controls">
              <span style={{ fontSize: '14px', color: '#666' }}>Scaling:</span>
              <button
                onClick={() => setScalingMode('auto')}
                className={`scaling-mode-button ${scalingMode === 'auto' ? 'active' : ''}`}
              >
                Auto Scale
              </button>
              <button
                onClick={() => setScalingMode('full')}
                className={`scaling-mode-button ${scalingMode === 'full' ? 'active' : ''}`}
              >
                0-100
              </button>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart data={priceSizeData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  type="number" 
                  dataKey="size" 
                  name="Size (sq m)"
                  unit=" sq m"
                  fontSize={12}
                />
                <YAxis 
                  type="number" 
                  dataKey="price" 
                  name="Price"
                  unit=" £"
                  fontSize={12}
                  domain={getYAxisDomain()}
                />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  labelFormatter={(_, payload: any) => {
                    if (payload && payload[0]) {
                      const data = payload[0].payload;
                      return (
                        <div>
                          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                            {data.property_type} - {data.bedrooms} bed(s)
                          </div>
                          <div style={{ fontSize: '12px', color: '#666', marginBottom: '2px' }}>
                            <strong>Price:</strong> £{data.price.toLocaleString()}
                          </div>
                          <div style={{ fontSize: '12px', color: '#666', marginBottom: '2px' }}>
                            <strong>Size:</strong> {data.size} sq m
                          </div>
                          <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                            {data.address}
                          </div>
                          <div style={{ fontSize: '11px', color: '#888', fontStyle: 'italic' }}>
                            Click dot to view property
                          </div>
                        </div>
                      );
                    }
                    return '';
                  }}
                />
                <Scatter 
                  dataKey="price" 
                  fill="#8884d8"
                  fillOpacity={0.6}
                  onClick={handleDotClick}
                  shape={(props: any) => {
                    const { cx, cy, payload } = props;
                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={6}
                        fill="#8884d8"
                        fillOpacity={0.6}
                        stroke="#5a5a5a"
                        strokeWidth={1}
                        style={{ cursor: 'pointer' }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.fillOpacity = '0.8';
                          e.currentTarget.style.strokeWidth = '2';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.fillOpacity = '0.6';
                          e.currentTarget.style.strokeWidth = '1';
                        }}
                        onClick={() => handleDotClick(payload)}
                      />
                    );
                  }}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Price per sqm by Bedrooms */}
        <div className="chart-card">
          <h3>Price per sqm by Bedrooms</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pricePerSqmByBedrooms} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bedrooms" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip 
                  formatter={(value: any, name: string) => [
                    `£${value.toFixed(0)}/sqm`,
                    name === 'average' ? 'Average' : 'Median'
                  ]}
                  labelFormatter={(label) => `${label} bedrooms`}
                />
                <Bar dataKey="average" fill="#8884d8" name="average" />
                <Bar dataKey="median" fill="#82ca9d" name="median" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Postcodes */}
        <div className="chart-card">
          <h3>Top 10 Postcodes</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={postcodeData} layout="horizontal" margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" fontSize={12} />
                <YAxis dataKey="name" type="category" width={80} fontSize={11} />
                <Tooltip 
                  formatter={(value: any) => [`${value} properties`, 'Count']}
                  labelFormatter={(label) => `Postcode: ${label}`}
                />
                <Bar dataKey="value" fill="#ffc658" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Price per sqm Distribution */}
        <div className="chart-card">
          <h3>Price per sqm Distribution</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pricePerSqmData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={11}
                  interval={0}
                />
                <YAxis fontSize={12} />
                <Tooltip 
                  formatter={(value: any) => [`${value} properties`, 'Count']}
                  labelFormatter={(label) => `Price per sqm: ${label}`}
                />
                <Bar dataKey="value" fill="#ff7300" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Letting Details Analysis */}
        {Object.keys(stats.lettingDetailsStats).length > 0 && (
          <div className="chart-card chart-wide">
            <h3>Letting Details Analysis</h3>
            <div className="letting-details-charts">
              {Object.entries(stats.lettingDetailsStats).slice(0, 4).map(([detailType, values]) => {
                const chartData = Object.entries(values)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 8)
                  .map(([value, count]) => ({
                    name: value,
                    value: count,
                    count: count,
                  }));

                return (
                  <div key={detailType} className="letting-detail-chart">
                    <h4>{detailType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                    <ResponsiveContainer width="100%" height={180}>
                      <BarChart data={chartData} layout="horizontal" margin={{ top: 10, right: 20, left: 20, bottom: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" fontSize={10} />
                        <YAxis dataKey="name" type="category" width={80} fontSize={10} />
                        <Tooltip 
                          formatter={(value: any) => [`${value} properties`, 'Count']}
                          labelFormatter={(label) => `${detailType}: ${label}`}
                        />
                        <Bar dataKey="value" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Data Quality Overview */}
        <div className="chart-card">
          <h3>Data Quality Overview</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                {
                  name: 'Price Data',
                  value: properties.filter(p => p.price !== null).length,
                  total: properties.length,
                  percentage: (properties.filter(p => p.price !== null).length / properties.length) * 100
                },
                {
                  name: 'Size Data',
                  value: properties.filter(p => p.property_size_sqm !== null).length,
                  total: properties.length,
                  percentage: (properties.filter(p => p.property_size_sqm !== null).length / properties.length) * 100
                },
                {
                  name: 'Letting Details',
                  value: properties.filter(p => p.letting_details && Object.keys(p.letting_details).length > 0).length,
                  total: properties.length,
                  percentage: (properties.filter(p => p.letting_details && Object.keys(p.letting_details).length > 0).length / properties.length) * 100
                },
                {
                  name: 'Postcode Data',
                  value: properties.filter(p => p.postcode !== null).length,
                  total: properties.length,
                  percentage: (properties.filter(p => p.postcode !== null).length / properties.length) * 100
                }
              ]} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip 
                  formatter={(value: any, _, props) => [
                    `${value}/${props.payload.total} (${props.payload.percentage.toFixed(1)}%)`,
                    'Properties'
                  ]}
                />
                <Bar dataKey="value" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertyCharts;
