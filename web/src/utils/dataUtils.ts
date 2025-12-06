/**
 * Data utility functions for property analysis
 */

import { PropertyData, PropertyStats, ChartData } from '../types';

/**
 * Calculate comprehensive statistics for a set of properties
 */
export function calculateStats(properties: PropertyData[]): PropertyStats {
  if (properties.length === 0) {
    return {
      totalProperties: 0,
      averagePrice: 0,
      medianPrice: 0,
      minPrice: 0,
      maxPrice: 0,
      averageSize: 0,
      medianSize: 0,
      minSize: 0,
      maxSize: 0,
      averagePricePerSqm: 0,
      medianPricePerSqm: 0,
      successRate: 0,
      bedroomDistribution: {},
      propertyTypeDistribution: {},
      postcodeDistribution: {},
      lettingDetailsStats: {},
    };
  }

  // Price statistics - convert weekly prices to monthly for consistent comparison
  const prices = properties
    .filter(p => p.price !== null && p.price !== undefined && p.price > 0)
    .map(p => {
      const price = Number(p.price);
      const frequency = p.frequency?.toLowerCase();
      
      // Convert weekly prices to monthly (multiply by 4.33 weeks per month)
      if (frequency === 'weekly') {
        return price * 4.33;
      }
      
      // Monthly prices remain as-is
      return price;
    });
  
  const averagePrice = prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : 0;
  const sortedPrices = [...prices].sort((a, b) => a - b);
  const medianPrice = sortedPrices.length > 0 
    ? sortedPrices[Math.floor(sortedPrices.length / 2)] 
    : 0;
  const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
  const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;

  // Size statistics
  const sizes = properties
    .map(p => p.property_size_sqm)
    .filter((size): size is number => size !== null && size !== undefined && size > 0)
    .map(size => Number(size)); // Ensure all values are numbers
  
  
  const averageSize = sizes.length > 0 ? sizes.reduce((a, b) => a + b, 0) / sizes.length : 0;
  const sortedSizes = [...sizes].sort((a, b) => a - b);
  const medianSize = sortedSizes.length > 0 
    ? sortedSizes[Math.floor(sortedSizes.length / 2)] 
    : 0;
  const minSize = sizes.length > 0 ? Math.min(...sizes) : 0;
  const maxSize = sizes.length > 0 ? Math.max(...sizes) : 0;

  // Price per square meter - using converted monthly prices
  const pricePerSqm = properties
    .filter(p => p.price !== null && p.property_size_sqm !== null && p.property_size_sqm > 0)
    .map(p => {
      const price = Number(p.price);
      const frequency = p.frequency?.toLowerCase();
      
      // Convert weekly prices to monthly for consistent comparison
      const monthlyPrice = frequency === 'weekly' ? price * 4.33 : price;
      
      return monthlyPrice / p.property_size_sqm!;
    });
  
  const averagePricePerSqm = pricePerSqm.length > 0 
    ? pricePerSqm.reduce((a, b) => a + b, 0) / pricePerSqm.length 
    : 0;
  const sortedPricePerSqm = [...pricePerSqm].sort((a, b) => a - b);
  const medianPricePerSqm = sortedPricePerSqm.length > 0 
    ? sortedPricePerSqm[Math.floor(sortedPricePerSqm.length / 2)] 
    : 0;

  // Success rate
  const successfulScrapes = properties.filter(p => p.scraping_success).length;
  const successRate = properties.length > 0 ? (successfulScrapes / properties.length) * 100 : 0;

  // Bedroom distribution
  const bedroomDistribution: Record<number, number> = {};
  properties.forEach(p => {
    if (p.bedrooms !== null) {
      bedroomDistribution[p.bedrooms] = (bedroomDistribution[p.bedrooms] || 0) + 1;
    }
  });

  // Property type distribution
  const propertyTypeDistribution: Record<string, number> = {};
  properties.forEach(p => {
    if (p.property_type) {
      propertyTypeDistribution[p.property_type] = (propertyTypeDistribution[p.property_type] || 0) + 1;
    }
  });

  // Postcode distribution
  const postcodeDistribution: Record<string, number> = {};
  properties.forEach(p => {
    if (p.postcode && p.postcode.trim() !== '') {
      // Include values that look like postcodes (letters followed by numbers)
      const postcode = p.postcode.trim();
      // Match both full postcodes and partial postcodes (like E13, SE14, etc.)
      if (/^[A-Z]{1,2}[0-9]{1,2}[A-Z]?[0-9]?[A-Z]{2}$/i.test(postcode) || 
          /^[A-Z]{1,2}[0-9]{1,2}[A-Z]?[0-9]?[A-Z]{2}\s?[0-9][A-Z]{2}$/i.test(postcode) ||
          /^[A-Z]{1,2}[0-9]{1,2}[A-Z]?$/i.test(postcode)) {
        postcodeDistribution[postcode] = (postcodeDistribution[postcode] || 0) + 1;
      }
    }
  });

  // Letting details statistics
  const lettingDetailsStats: Record<string, Record<string, number>> = {};
  properties.forEach(p => {
    if (p.letting_details && typeof p.letting_details === 'object') {
      Object.entries(p.letting_details).forEach(([key, value]) => {
        if (!lettingDetailsStats[key]) {
          lettingDetailsStats[key] = {};
        }
        lettingDetailsStats[key][value] = (lettingDetailsStats[key][value] || 0) + 1;
      });
    }
  });

  return {
    totalProperties: properties.length,
    averagePrice,
    medianPrice,
    minPrice,
    maxPrice,
    averageSize,
    medianSize,
    minSize,
    maxSize,
    averagePricePerSqm,
    medianPricePerSqm,
    successRate,
    bedroomDistribution,
    propertyTypeDistribution,
    postcodeDistribution,
    lettingDetailsStats,
  };
}


/**
 * Convert distribution data to chart format
 */
export function distributionToChartData(distribution: Record<string | number, number>): ChartData[] {
  return Object.entries(distribution)
    .map(([name, value]) => ({
      name: String(name),
      value,
      count: value,
    }))
    .sort((a, b) => b.value - a.value);
}

/**
 * Create price range data for charts
 */
export function createPriceRangeData(properties: PropertyData[], buckets: number = 10): ChartData[] {
  const prices = properties
    .filter(p => p.price !== null && p.price !== undefined)
    .map(p => {
      const price = Number(p.price);
      const frequency = p.frequency?.toLowerCase();
      
      // Convert weekly prices to monthly for consistent comparison
      return frequency === 'weekly' ? price * 4.33 : price;
    });
  
  if (prices.length === 0) return [];

  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const bucketSize = (max - min) / buckets;

  const buckets_data: Record<string, number> = {};
  
  for (let i = 0; i < buckets; i++) {
    const bucketMin = min + (i * bucketSize);
    const bucketMax = min + ((i + 1) * bucketSize);
    const bucketName = `£${Math.round(bucketMin)}-£${Math.round(bucketMax)}`;
    buckets_data[bucketName] = 0;
  }

  prices.forEach(price => {
    const bucketIndex = Math.min(Math.floor((price - min) / bucketSize), buckets - 1);
    const bucketMin = min + (bucketIndex * bucketSize);
    const bucketMax = min + ((bucketIndex + 1) * bucketSize);
    const bucketName = `£${Math.round(bucketMin)}-£${Math.round(bucketMax)}`;
    buckets_data[bucketName]++;
  });

  return distributionToChartData(buckets_data);
}

/**
 * Create size range data for charts
 */
export function createSizeRangeData(properties: PropertyData[], buckets: number = 10): ChartData[] {
  const sizes = properties
    .map(p => p.property_size_sqm)
    .filter((size): size is number => size !== null && size !== undefined);
  
  if (sizes.length === 0) return [];

  const min = Math.min(...sizes);
  const max = Math.max(...sizes);
  const bucketSize = (max - min) / buckets;

  const buckets_data: Record<string, number> = {};
  
  for (let i = 0; i < buckets; i++) {
    const bucketMin = min + (i * bucketSize);
    const bucketMax = min + ((i + 1) * bucketSize);
    const bucketName = `${Math.round(bucketMin)}-${Math.round(bucketMax)} sq m`;
    buckets_data[bucketName] = 0;
  }

  sizes.forEach(size => {
    const bucketIndex = Math.min(Math.floor((size - min) / bucketSize), buckets - 1);
    const bucketMin = min + (bucketIndex * bucketSize);
    const bucketMax = min + ((bucketIndex + 1) * bucketSize);
    const bucketName = `${Math.round(bucketMin)}-${Math.round(bucketMax)} sq m`;
    buckets_data[bucketName]++;
  });

  return distributionToChartData(buckets_data);
}

/**
 * Create price per square meter data for charts
 */
export function createPricePerSqmData(properties: PropertyData[], buckets: number = 10): ChartData[] {
  const pricePerSqm = properties
    .filter(p => p.price !== null && p.property_size_sqm !== null && p.property_size_sqm > 0)
    .map(p => {
      const price = Number(p.price);
      const frequency = p.frequency?.toLowerCase();
      
      // Convert weekly prices to monthly for consistent comparison
      const monthlyPrice = frequency === 'weekly' ? price * 4.33 : price;
      
      return monthlyPrice / p.property_size_sqm!;
    });
  
  if (pricePerSqm.length === 0) return [];

  const min = Math.min(...pricePerSqm);
  const max = Math.max(...pricePerSqm);
  const bucketSize = (max - min) / buckets;

  const buckets_data: Record<string, number> = {};
  
  for (let i = 0; i < buckets; i++) {
    const bucketMin = min + (i * bucketSize);
    const bucketMax = min + ((i + 1) * bucketSize);
    const bucketName = `£${Math.round(bucketMin)}-£${Math.round(bucketMax)}/sqm`;
    buckets_data[bucketName] = 0;
  }

  pricePerSqm.forEach(price => {
    const bucketIndex = Math.min(Math.floor((price - min) / bucketSize), buckets - 1);
    const bucketMin = min + (bucketIndex * bucketSize);
    const bucketMax = min + ((bucketIndex + 1) * bucketSize);
    const bucketName = `£${Math.round(bucketMin)}-£${Math.round(bucketMax)}/sqm`;
    buckets_data[bucketName]++;
  });

  return distributionToChartData(buckets_data);
}
