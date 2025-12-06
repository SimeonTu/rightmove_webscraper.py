/**
 * Type definitions for Rightmove Property Data
 */

export interface PropertyData {
  id: string;
  price: number | null;
  price_display: string | null;
  frequency: string | null;
  property_type: string | null;
  bedrooms: number | null;
  bathrooms: number | null;
  address: string | null;
  summary: string | null;
  property_url: string;
  contact_url: string | null;
  branch: string | null;
  branch_id: string | null;
  added_or_reduced: string | null;
  first_visible_date: string | null;
  let_type: string | null;
  postcode: string | null;
  search_date: string;
  
  // Enhanced data from individual page scraping
  letting_details: Record<string, string>;
  property_size_sqft: number | null;
  property_size_sqm: number | null;
  scraping_success: boolean;
  scraping_error: string | null;
}

export interface LettingDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  lettingDetails: Record<string, string>;
  propertyAddress: string;
}

export interface PropertyStats {
  totalProperties: number;
  averagePrice: number;
  medianPrice: number;
  minPrice: number;
  maxPrice: number;
  averageSize: number;
  medianSize: number;
  minSize: number;
  maxSize: number;
  averagePricePerSqm: number;
  medianPricePerSqm: number;
  successRate: number;
  bedroomDistribution: Record<number, number>;
  propertyTypeDistribution: Record<string, number>;
  postcodeDistribution: Record<string, number>;
  lettingDetailsStats: Record<string, Record<string, number>>;
}

export interface ChartData {
  name: string;
  value: number;
  count?: number;
}


export type SortField = keyof PropertyData;
export type SortDirection = 'asc' | 'desc';
