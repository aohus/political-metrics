import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line } from 'recharts';
import { BillStatisticsResponse, FilterState, MemberStatisticsResponse } from '../types';
import { 
  FilterDropdown, 
  ChartContainer, 
  SearchInput, 
  EmptyState, 
  PassRateBadge 
} from '../components/ui';
import { useFilteredBills, useUniqueOptions } from '../hooks';
import { AGE_OPTIONS, BILL_SORT_OPTIONS, DEFAULT_FILTER } from '../constants';
import { filterBySearchTerm, formatNumber, formatPercent, truncateText } from '../utils';

interface BillStatsPageProps {
  bills: BillStatisticsResponse[];
  members: MemberStatisticsResponse[];
  selectedAge: string;
  onAgeChange: (age: string) => void;
}

export const BillStatsPage: React.FC<BillStatsPageProps> = ({
  bills,
  members,
  selectedAge,
  onAgeChange,
}) => {
  const [filter, setFilter] = useState<FilterState>(DEFAULT_FILTER);
  const [searchTerm, setSearchTerm] = useState('');

  const { committeeOptions } = useUniqueOptions(members);
  const filteredBills = useFilteredBills(bills, filter);
  const searchedBills = filterBySearchTerm(
    filteredBills, 
    searchTerm, 
    ['bill_name', 'bill_committee']
  );

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilter(prev => ({ ...prev, [key]: value }));
  };

  // 위원회별 통계 계산
  const committeeStats = React.useMemo(() => {
    const committeeMap = new Map<string, { name: string; count: number; totalBills: number; avgPassRate: number }>();
    
    searchedBills.forEach(bill => {
      if (!committeeMap.has(bill.bill_committee)) {
        committeeMap.set(bill.bill_committee, {
          name: bill.bill_committee,
          count: 0,
          totalBills: 0,
          avgPassRate: 0,
        });
      }
      
      const committee = committeeMap.get(bill.bill_committee)!;
      committee.count += 1;
      committee.totalBills += bill.bill_count;
      committee.avgPassRate += bill.bill_pass_rate;
    });

    return Array.from(committeeMap.values()).map(committee => ({
      ...committee,
      avgPassRate: Math.round((committee.avgPassRate / committee.count) * 10) / 10,
    }));
  }, [searchedBills]);

  return (
    <div className="space-y-6">
      {/* 필터 및 검색 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">의안 통계 필터</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <SearchInput
            value={searchTerm}
            onChange={setSearchTerm}
            placeholder="의안명, 위원회 검색..."
          />
          <FilterDropdown
            label="대수"
            value={selectedAge}
            options={AGE_OPTIONS}
            onChange={onAgeChange}
          />
          <FilterDropdown
            label="위원회"
            value={filter.committee || ''}
            options={committeeOptions}
            onChange={(value) => handleFilterChange('committee', value)}
          />
          <FilterDropdown
            label="정렬 기준"
            value={filter.sortBy || 'bill_name'}
            options={BILL_SORT_OPTIONS}
            onChange={(value) => handleFilterChange('sortBy', value)}
          />
        </div>
      </div>

      {/* 의안 통계 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 위원회별 의안 수 */}
        <ChartContainer title="위원회별 의안 수">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={committeeStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45} 
                textAnchor="end" 
                height={100}
                interval={0}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="totalBills" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* 위원회별 평균 통과율 */}
        <ChartContainer title="위원회별 평균 통과율">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={committeeStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45} 
                textAnchor="end" 
                height={100}
                interval={0}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="avgPassRate" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* 상위 의안 차트 */}
      <ChartContainer title="의안별 발의 건수 & 통과율 (상위 20개)">
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={searchedBills.slice(0, 20)}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="bill_name" 
              angle={-45} 
              textAnchor="end" 
              height={150}
              interval={0}
              tickFormatter={(value) => truncateText(value, 15)}
            />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip 
              labelFormatter={(value) => `의안: ${value}`}
              formatter={(value, name) => [
                name === '발의 건수' ? formatNumber(value as number) : formatPercent(value as number),
                name
              ]}
            />
            <Legend />
            <Bar yAxisId="left" dataKey="bill_count" fill="#8884d8" name="발의 건수" />
            <Bar yAxisId="right" dataKey="bill_pass_rate" fill="#82ca9d" name="통과율(%)" />
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>

      {/* 의안 목록 테이블 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            의안 목록 ({formatNumber(searchedBills.length)}개)
          </h3>
        </div>

        {searchedBills.length === 0 ? (
          <EmptyState message="조건에 맞는 의안이 없습니다." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    의안명
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    소관위원회
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    발의 건수
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    통과율
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {searchedBills.map((bill, index) => (
                  <tr key={`${bill.bill_code}-${index}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      <div className="max-w-xs truncate" title={bill.bill_name}>
                        {bill.bill_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {bill.bill_committee}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatNumber(bill.bill_count)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <PassRateBadge passRate={bill.bill_pass_rate} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 요약 통계 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">총 의안 수</h4>
          <p className="text-3xl font-bold text-blue-600">{formatNumber(searchedBills.length)}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">총 발의 건수</h4>
          <p className="text-3xl font-bold text-green-600">
            {formatNumber(searchedBills.reduce((sum, bill) => sum + bill.bill_count, 0))}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">평균 통과율</h4>
          <p className="text-3xl font-bold text-purple-600">
            {formatPercent(
              searchedBills.length > 0 
                ? searchedBills.reduce((sum, bill) => sum + bill.bill_pass_rate, 0) / searchedBills.length
                : 0
            )}
          </p>
        </div>
      </div>
    </div>
  );
};