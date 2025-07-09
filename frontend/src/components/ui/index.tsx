import React from 'react';
import { Users } from 'lucide-react';
import { 
  StatCardProps, 
  MemberCardProps, 
  FilterDropdownProps, 
  ChartContainerProps,
  MemberStatisticsResponse 
} from '../../types';
import { COLOR_CLASSES } from '../../constants';
import { formatNumber, formatPercent, getShortPartyName, getPassRateColorClass } from '../../utils';

// 통계 카드 컴포넌트
export const StatCard: React.FC<StatCardProps> = ({
  icon: Icon,
  title,
  value,
  subtitle,
  color = 'blue',
}) => {
  const colorClass = COLOR_CLASSES[color as keyof typeof COLOR_CLASSES] || COLOR_CLASSES.blue;

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 border-l-4 ${colorClass.border}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
        <Icon className={`h-8 w-8 ${colorClass.text}`} />
      </div>
    </div>
  );
};

// 의원 카드 컴포넌트
export const MemberCard: React.FC<MemberCardProps> = ({
  member,
  onClick,
  isCompact = false,
}) => {
  const partyName = getShortPartyName(member.member_info.PLPT_NM);

  if (isCompact) {
    return (
      <div
        className="bg-white rounded-lg shadow-sm p-4 cursor-pointer hover:shadow-md transition-shadow border"
        onClick={onClick}
      >
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
            <Users className="w-4 h-4 text-gray-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-gray-900 truncate">
              {member.member_info.NAAS_NM}
            </h4>
            <p className="text-xs text-gray-600 truncate">{partyName}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">대표 발의 의안 / 가결률</p>
            <p className="text-sm font-bold text-blue-600">
              {member.bill_stats.lead_count} / {member.bill_stats.lead_pass_rate} %
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow border"
      onClick={onClick}
    >
      <div className="flex items-center space-x-4">
        <div className="w-12 h-12 bg-gray-300 rounded-full flex items-center justify-center">
          <Users className="w-6 h-6 text-gray-600" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">
            {member.member_info.NAAS_NM}
          </h3>
          <p className="text-sm text-gray-600">{partyName}</p>
          <p className="text-sm text-gray-500">{member.member_info.ELECD_DIV_NM}</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-600">총 의안</p>
          <p className="text-xl font-bold text-blue-600">
            {formatNumber(member.bill_stats.total_count)}
          </p>
          <p className="text-sm text-green-600">
            가결률 {formatPercent(member.bill_stats.total_pass_rate)}
          </p>
        </div>
      </div>
    </div>
  );
};

// 필터 드롭다운 컴포넌트
export const FilterDropdown: React.FC<FilterDropdownProps> = ({
  label,
  value,
  options,
  onChange,
}) => {
  return (
    <div className="flex flex-col space-y-1">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};

// 차트 컨테이너 컴포넌트
export const ChartContainer: React.FC<ChartContainerProps> = ({ title, children }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      {children}
    </div>
  );
};

// 로딩 스피너 컴포넌트
export const LoadingSpinner: React.FC<{ message?: string }> = ({ 
  message = '데이터를 불러오는 중...' 
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <span className="text-gray-500 text-lg">{message}</span>
      </div>
    </div>
  );
};

// 에러 메시지 컴포넌트
export const ErrorMessage: React.FC<{ message: string; onRetry?: () => void }> = ({ 
  message, 
  onRetry 
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="text-red-500 text-lg mb-4">{message}</div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            다시 시도
          </button>
        )}
      </div>
    </div>
  );
};

// 빈 상태 컴포넌트
export const EmptyState: React.FC<{ message: string }> = ({ message }) => {
  return (
    <div className="text-center py-12">
      <div className="text-gray-500 text-lg">{message}</div>
    </div>
  );
};

// 통과율 배지 컴포넌트
export const PassRateBadge: React.FC<{ passRate: number }> = ({ passRate }) => {
  const colorClass = getPassRateColorClass(passRate);
  
  return (
    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${colorClass}`}>
      {formatPercent(passRate)}
    </span>
  );
};

// 검색 입력 컴포넌트
export const SearchInput: React.FC<{
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}> = ({ value, onChange, placeholder = '검색...' }) => {
  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>
  );
};