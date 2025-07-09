import { SelectOption, SortCriteria } from '../types';

// 차트 색상
export const CHART_COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658'];

// 대수 옵션
export const AGE_OPTIONS: SelectOption[] = [
  { value: '', label: '전체' },
  { value: '20', label: '20대' },
  { value: '21', label: '21대' },
  { value: '22', label: '22대' },
];

// 정렬 기준 옵션 (의원용)
export const MEMBER_SORT_OPTIONS: SelectOption[] = [
  { value: 'name', label: '이름순' },
  { value: 'total_count', label: '총 의안 수' },
  { value: 'total_pass_rate', label: '통과율' },
  { value: 'lead_count', label: '대표발의 수' },
  { value: 'party', label: '정당별' },
];

// 정렬 기준 옵션 (의안용)
export const BILL_SORT_OPTIONS: SelectOption[] = [
  { value: 'bill_name', label: '의안명' },
  { value: 'bill_count', label: '발의 건수' },
  { value: 'bill_pass_rate', label: '통과율' },
  { value: 'bill_committee', label: '위원회' },
];

// 탭 정의
export const TABS = [
  { id: 'overview', name: '전체 개요', icon: 'TrendingUp' },
  { id: 'member-stats', name: '의원 통계', icon: 'Users' },
  { id: 'bill-stats', name: '의안 통계', icon: 'FileText' },
] as const;

// 색상 클래스 매핑
export const COLOR_CLASSES = {
  blue: {
    border: 'border-blue-500',
    text: 'text-blue-500',
    bg: 'bg-blue-100',
  },
  green: {
    border: 'border-green-500',
    text: 'text-green-500',
    bg: 'bg-green-100',
  },
  purple: {
    border: 'border-purple-500',
    text: 'text-purple-500',
    bg: 'bg-purple-100',
  },
  orange: {
    border: 'border-orange-500',
    text: 'text-orange-500',
    bg: 'bg-orange-100',
  },
  red: {
    border: 'border-red-500',
    text: 'text-red-500',
    bg: 'bg-red-100',
  },
} as const;

// 디폴트 필터 상태
export const DEFAULT_FILTER = {
  age: '',
  party: '',
  committee: '',
  sortBy: 'name' as SortCriteria,
};

// API 기본 URL
export const API_BASE_URL = 'http://0.0.0.0:8001';