/**
 * PropertyTable Component
 * Displays properties in a sortable table with pagination
 */

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { PropertyData, SortField, SortDirection } from '../types';
import { ExternalLink, ArrowUpDown, ArrowUp, ArrowDown, Phone, AlertCircle, Eye, EyeOff } from 'lucide-react';
import LettingDetailsModal from './LettingDetailsModal';

interface PropertyTableProps {
  properties: PropertyData[];
}

const PropertyTable: React.FC<PropertyTableProps> = ({ properties }) => {
  const [sortField, setSortField] = useState<SortField>('price');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  const [selectedProperty, setSelectedProperty] = useState<PropertyData | null>(null);
  const [showLettingDetails, setShowLettingDetails] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Handle column header click for sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
    setCurrentPage(1);
  };

  // Sort properties based on current sort field and direction
  const sortedProperties = useMemo(() => {
    const sorted = [...properties].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      // Handle null/undefined values
      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      // Compare values
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return aValue.localeCompare(bValue);
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return aValue - bValue;
      }

      if (typeof aValue === 'boolean' && typeof bValue === 'boolean') {
        return aValue === bValue ? 0 : aValue ? -1 : 1;
      }

      return 0;
    });

    return sortDirection === 'desc' ? sorted.reverse() : sorted;
  }, [properties, sortField, sortDirection]);

  // Pagination calculations
  const totalPages = Math.ceil(sortedProperties.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedProperties = sortedProperties.slice(startIndex, endIndex);

  // Pagination handlers
  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  };

  // Reset to first page when properties change
  React.useEffect(() => {
    setCurrentPage(1);
  }, [properties.length]);

  // Refs for scroll synchronization
  const tableContainerRef = useRef<HTMLDivElement>(null);
  const stickyScrollbarRef = useRef<HTMLDivElement>(null);

  // Sync scroll positions between table and sticky scrollbar
  useEffect(() => {
    const tableContainer = tableContainerRef.current;
    const stickyScrollbar = stickyScrollbarRef.current;

    if (!tableContainer || !stickyScrollbar) return;

    const handleTableScroll = () => {
      stickyScrollbar.scrollLeft = tableContainer.scrollLeft;
    };

    const handleStickyScroll = () => {
      tableContainer.scrollLeft = stickyScrollbar.scrollLeft;
    };

    tableContainer.addEventListener('scroll', handleTableScroll);
    stickyScrollbar.addEventListener('scroll', handleStickyScroll);

    return () => {
      tableContainer.removeEventListener('scroll', handleTableScroll);
      stickyScrollbar.removeEventListener('scroll', handleStickyScroll);
    };
  }, []);

  // Render sort indicator
  const renderSortIndicator = (field: SortField) => {
    if (sortField !== field) return <ArrowUpDown size={14} />;
    return sortDirection === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />;
  };

  // Format price
  const formatPrice = (price: number | null) => {
    if (price === null) return 'N/A';
    return `£${price.toLocaleString()}`;
  };

  // Format size
  const formatSize = (size: number | null) => {
    if (size === null) return 'N/A';
    return `${size} sq m`;
  };

  // Format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  // Toggle row expansion
  const toggleRowExpansion = (propertyId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(propertyId)) {
      newExpanded.delete(propertyId);
    } else {
      newExpanded.add(propertyId);
    }
    setExpandedRows(newExpanded);
  };

  // Handle letting details modal
  const handleLettingDetailsClick = (property: PropertyData) => {
    setSelectedProperty(property);
    setShowLettingDetails(true);
  };

  // Truncate text
  const truncateText = (text: string | null, maxLength: number = 100) => {
    if (!text) return 'N/A';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  if (properties.length === 0) {
    return (
      <div className="empty-state">
        <p>No properties to display. Upload a CSV file to get started.</p>
      </div>
    );
  }

  return (
    <>
      {/* Pagination Controls - Top */}
      {totalPages > 1 && (
        <div className="pagination-controls pagination-top">
          <div className="pagination-info">
            <span>
              Showing {startIndex + 1}-{Math.min(endIndex, sortedProperties.length)} of {sortedProperties.length} properties
            </span>
          </div>
          <div className="pagination-buttons">
            <button
              onClick={() => goToPage(1)}
              disabled={currentPage === 1}
              className="pagination-btn"
              title="First page"
            >
              ««
            </button>
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="pagination-btn"
              title="Previous page"
            >
              «
            </button>
            
            {/* Page numbers */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }
              
              return (
                <button
                  key={pageNum}
                  onClick={() => goToPage(pageNum)}
                  className={`pagination-btn ${currentPage === pageNum ? 'active' : ''}`}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="pagination-btn"
              title="Next page"
            >
              »
            </button>
            <button
              onClick={() => goToPage(totalPages)}
              disabled={currentPage === totalPages}
              className="pagination-btn"
              title="Last page"
            >
              »»
            </button>
          </div>
          <div className="pagination-size">
            <label htmlFor="items-per-page">Items per page:</label>
            <select
              id="items-per-page"
              value={itemsPerPage}
              onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
              className="items-per-page-select"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
      )}

      <div className="table-wrapper">
        <div className="table-container" ref={tableContainerRef}>
          <table className="property-table">
            <thead>
              <tr>
                <th>#</th>
                    <th onClick={() => handleSort('address')} className="sortable">
                      <div className="sort-content">
                        Address {renderSortIndicator('address')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('price')} className="sortable">
                      <div className="sort-content">
                        Price {renderSortIndicator('price')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('frequency')} className="sortable">
                      <div className="sort-content">
                        Frequency {renderSortIndicator('frequency')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('bedrooms')} className="sortable">
                      <div className="sort-content">
                        Beds {renderSortIndicator('bedrooms')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('bathrooms')} className="sortable">
                      <div className="sort-content">
                        Baths {renderSortIndicator('bathrooms')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('property_type')} className="sortable">
                      <div className="sort-content">
                        Type {renderSortIndicator('property_type')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('property_size_sqm')} className="sortable">
                      <div className="sort-content">
                        Size {renderSortIndicator('property_size_sqm')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('branch')} className="sortable">
                      <div className="sort-content">
                        Agent {renderSortIndicator('branch')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('scraping_success')} className="sortable">
                      <div className="sort-content">
                        Status {renderSortIndicator('scraping_success')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('first_visible_date')} className="sortable">
                      <div className="sort-content">
                        Listed {renderSortIndicator('first_visible_date')}
                      </div>
                    </th>
                    <th onClick={() => handleSort('let_type')} className="sortable">
                      <div className="sort-content">
                        Let Type {renderSortIndicator('let_type')}
                      </div>
                    </th>
                <th>Summary</th>
                <th>Letting Details</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedProperties.map((property, index) => (
                <React.Fragment key={`${property.id}-${index}`}>
                  <tr>
                  <td>{startIndex + index + 1}</td>
                  <td className="address-cell">
                    <div className="address-content">
                      <div className="address-main">{property.address}</div>
                      {property.postcode && (
                        <div className="address-postcode">{property.postcode}</div>
                      )}
                    </div>
                  </td>
                  <td className="price-cell">
                    <div className="price-content">
                      <div className="price-main">{formatPrice(property.price)}</div>
                      {property.price_display && (
                        <div className="price-display">{property.price_display}</div>
                      )}
                      {property.frequency && (
                        <div className={`frequency-badge frequency-${property.frequency.toLowerCase()}`}>
                          {property.frequency === 'weekly' ? 'Weekly (converted to monthly)' : 'Monthly'}
                        </div>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className="frequency-badge">
                      {property.frequency || 'N/A'}
                    </span>
                  </td>
                  <td>{property.bedrooms || 'N/A'}</td>
                  <td>{property.bathrooms || 'N/A'}</td>
                  <td>{property.property_type || 'N/A'}</td>
                  <td className="size-cell">
                    <div className="size-content">
                      <div>{formatSize(property.property_size_sqm)}</div>
                      {property.property_size_sqft && (
                        <div className="size-sqft">({property.property_size_sqft} sq ft)</div>
                      )}
                    </div>
                  </td>
                  <td>{property.branch || 'N/A'}</td>
                  <td>
                    <div className="status-cell">
                      <span className={`status-badge ${property.scraping_success ? 'success' : 'error'}`}>
                        {property.scraping_success ? '✓' : '✗'}
                      </span>
                      {!property.scraping_success && property.scraping_error && property.scraping_error.trim() !== '' && (
                        <div className="error-tooltip" title={property.scraping_error}>
                          <AlertCircle size={12} />
                        </div>
                      )}
                    </div>
                  </td>
                      <td className="date-cell">
                        {property.first_visible_date ? (
                          <div className="date-content">
                            <div className="date-main">
                              {formatDate(property.first_visible_date)}
                            </div>
                            {property.added_or_reduced && (
                              <div className={`date-badge date-badge-${property.added_or_reduced.toLowerCase().replace(/\s+/g, '-')}`}>
                                {property.added_or_reduced}
                              </div>
                            )}
                          </div>
                        ) : (
                          'N/A'
                        )}
                      </td>
                  <td>
                    <span className="let-type-badge">
                      {property.let_type || 'N/A'}
                    </span>
                  </td>
                  <td className="summary-cell">
                    <div className="summary-content">
                      {truncateText(property.summary, 80)}
                      {property.summary && property.summary.length > 80 && (
                        <button 
                          className="expand-summary-btn"
                          onClick={() => toggleRowExpansion(property.id)}
                        >
                          {expandedRows.has(property.id) ? <EyeOff size={12} /> : <Eye size={12} />}
                        </button>
                      )}
                    </div>
                  </td>
                  <td>
                    {property.letting_details && Object.keys(property.letting_details).length > 0 ? (
                      <div className="letting-details-preview">
                        {Object.entries(property.letting_details).slice(0, 2).map(([key, value]) => (
                          <div key={key} className="letting-detail-item">
                            <span className="letting-key">{key}:</span>
                            <span className="letting-value">{value}</span>
                          </div>
                        ))}
                        {Object.keys(property.letting_details).length > 2 && (
                          <div className="letting-more">+{Object.keys(property.letting_details).length - 2} more</div>
                        )}
                      </div>
                    ) : (
                      <span className="no-details">No details</span>
                    )}
                  </td>
                  <td className="actions-cell">
                    <div className="action-buttons">
                      <a
                        href={property.property_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="action-btn"
                        title="View Property"
                      >
                        <ExternalLink size={16} />
                      </a>
                      {property.contact_url && (
                        <a
                          href={property.contact_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="action-btn"
                          title="Contact Agent"
                        >
                          <Phone size={16} />
                        </a>
                      )}
                      {property.letting_details && Object.keys(property.letting_details).length > 0 && (
                        <button
                          className="action-btn"
                          onClick={() => handleLettingDetailsClick(property)}
                          title="View Full Letting Details"
                        >
                          <Eye size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                  </tr>
                  
                  {/* Expanded Summary Row */}
                  {expandedRows.has(property.id) && property.summary && (
                    <tr className="expanded-row">
                      <td colSpan={13}>
                        <div className="expanded-summary">
                          <h4>Property Summary</h4>
                          <p>{property.summary}</p>
                          <div className="expanded-meta">
                            <span>Search Date: {formatDate(property.search_date)}</span>
                            {property.branch_id && (
                              <span>Branch ID: {property.branch_id}</span>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Sticky horizontal scrollbar */}
        <div className="sticky-scrollbar-container" ref={stickyScrollbarRef}>
          <div 
            className="sticky-scrollbar-content"
            style={{ width: '1400px' }}
          />
        </div>
      </div>

      {/* Pagination Controls - Bottom */}
      {totalPages > 1 && (
        <div className="pagination-controls pagination-bottom">
          <div className="pagination-info">
            <span>
              Showing {startIndex + 1}-{Math.min(endIndex, sortedProperties.length)} of {sortedProperties.length} properties
            </span>
          </div>
          <div className="pagination-buttons">
            <button
              onClick={() => goToPage(1)}
              disabled={currentPage === 1}
              className="pagination-btn"
              title="First page"
            >
              ««
            </button>
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="pagination-btn"
              title="Previous page"
            >
              «
            </button>
            
            {/* Page numbers */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }
              
              return (
                <button
                  key={pageNum}
                  onClick={() => goToPage(pageNum)}
                  className={`pagination-btn ${currentPage === pageNum ? 'active' : ''}`}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="pagination-btn"
              title="Next page"
            >
              »
            </button>
            <button
              onClick={() => goToPage(totalPages)}
              disabled={currentPage === totalPages}
              className="pagination-btn"
              title="Last page"
            >
              »»
            </button>
          </div>
          <div className="pagination-size">
            <label htmlFor="items-per-page-bottom">Items per page:</label>
            <select
              id="items-per-page-bottom"
              value={itemsPerPage}
              onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
              className="items-per-page-select"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
      )}

      {/* Letting Details Modal */}
      {selectedProperty && (
        <LettingDetailsModal
          isOpen={showLettingDetails}
          onClose={() => setShowLettingDetails(false)}
          lettingDetails={selectedProperty.letting_details}
          propertyAddress={selectedProperty.address || 'Unknown Address'}
        />
      )}
    </>
  );
};

export default PropertyTable;
