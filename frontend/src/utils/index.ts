// 숫자 포맷팅 함수
export const formatNumber = (num: number): string => {
  return num.toLocaleString('ko-KR');
};

// 백분율 포맷팅 함수
export const formatPercent = (num: number): string => {
  return `${Math.round(num * 10) / 10}%`;
};

// 날짜 포맷팅 함수
export const formatDate = (dateString?: string): string => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR');
  } catch {
    return dateString;
  }
};

// 정당명 단축 함수
export const getShortPartyName = (fullPartyName?: string): string => {
  if (!fullPartyName) return '무소속';
  return fullPartyName.split('/').pop() || '무소속';
};

// 통과율에 따른 색상 클래스 반환
export const getPassRateColorClass = (passRate: number): string => {
  if (passRate >= 70) return 'bg-green-100 text-green-800';
  if (passRate >= 60) return 'bg-yellow-100 text-yellow-800';
  return 'bg-red-100 text-red-800';
};

// 텍스트 트러케이션
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
};

// 빈 값 처리
export const getValueOrDefault = (value: any, defaultValue: string = '-'): string => {
  return value !== null && value !== undefined && value !== '' ? String(value) : defaultValue;
};

// 차트 데이터 변환
export const transformChartData = (data: any[], keyMap: Record<string, string>) => {
  return data.map(item => {
    const transformed: any = {};
    Object.entries(keyMap).forEach(([originalKey, newKey]) => {
      transformed[newKey] = item[originalKey];
    });
    return transformed;
  });
};

// 배열을 청크로 나누기
export const chunkArray = <T>(array: T[], chunkSize: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += chunkSize) {
    chunks.push(array.slice(i, i + chunkSize));
  }
  return chunks;
};

// 객체 깊은 복사
export const deepClone = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj));
};

// 중첩된 객체에서 값 가져오기
const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((current, key) => current?.[key], obj);
};

// 검색어로 필터링 (중첩된 객체 경로 지원)
export const filterBySearchTerm = <T>(
  items: T[], 
  searchTerm: string, 
  searchPaths: string[]
): T[] => {
  if (!searchTerm.trim()) return items;
  
  const term = searchTerm.toLowerCase();
  return items.filter(item =>
    searchPaths.some(path => {
      const value = getNestedValue(item, path);
      return String(value || '').toLowerCase().includes(term);
    })
  );
};

// 정렬 함수
export const sortBy = <T>(
  items: T[], 
  key: keyof T, 
  direction: 'asc' | 'desc' = 'asc'
): T[] => {
  return [...items].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      const result = aVal.localeCompare(bVal);
      return direction === 'asc' ? result : -result;
    }
    
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      const result = aVal - bVal;
      return direction === 'asc' ? result : -result;
    }
    
    return 0;
  });
};