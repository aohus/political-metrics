import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell } from 'recharts';
import { Users, Award, FileText } from 'lucide-react';
import { MemberStatisticsResponse, FilterState } from '../types';
import { 
  FilterDropdown, 
  MemberCard, 
  ChartContainer, 
  SearchInput, 
  EmptyState,
  StatCard 
} from '../components/ui';
import { useFilteredMembers, useUniqueOptions } from '../hooks';
import { AGE_OPTIONS, MEMBER_SORT_OPTIONS, CHART_COLORS, DEFAULT_FILTER } from '../constants';
import { filterBySearchTerm, formatNumber, formatPercent } from '../utils';

interface MemberStatsPageProps {
  members: MemberStatisticsResponse[];
  selectedMember: MemberStatisticsResponse | null;
  onMemberSelect: (member: MemberStatisticsResponse) => void;
  selectedAge: string;
  onAgeChange: (age: string) => void;
}

export const MemberStatsPage: React.FC<MemberStatsPageProps> = ({
  members,
  selectedMember,
  onMemberSelect,
  selectedAge,
  onAgeChange,
}) => {
  const [filter, setFilter] = useState<FilterState>(DEFAULT_FILTER);
  const [searchTerm, setSearchTerm] = useState('');

  const { partyOptions, committeeOptions } = useUniqueOptions(members);
  const filteredMembers = useFilteredMembers(members, filter);
  const searchedMembers = filterBySearchTerm(
    filteredMembers, 
    searchTerm, 
    ['member_info.NAAS_NM', 'member_info.PLPT_NM', 'member_info.ELECD_DIV_NM']
  );

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilter(prev => ({ ...prev, [key]: value }));
  };

  const renderMemberList = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          의원 목록 ({formatNumber(searchedMembers.length)}명)
        </h3>
      </div>

      {/* 검색 및 필터 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <SearchInput
          value={searchTerm}
          onChange={setSearchTerm}
          placeholder="의원명, 정당, 선거구 검색..."
        />
        <FilterDropdown
          label="대수"
          value={selectedAge}
          options={AGE_OPTIONS}
          onChange={onAgeChange}
        />
        <FilterDropdown
          label="정당"
          value={filter.party || ''}
          options={partyOptions}
          onChange={(value) => handleFilterChange('party', value)}
        />
        <FilterDropdown
          label="위원회"
          value={filter.committee || ''}
          options={committeeOptions}
          onChange={(value) => handleFilterChange('committee', value)}
        />
        <FilterDropdown
          label="정렬 기준"
          value={filter.sortBy || 'name'}
          options={MEMBER_SORT_OPTIONS}
          onChange={(value) => handleFilterChange('sortBy', value)}
        />
      </div>

      {/* 의원 목록 */}
      {searchedMembers.length === 0 ? (
        <EmptyState message="조건에 맞는 의원이 없습니다." />
      ) : (
        <div className="space-y-4">
          {searchedMembers.map((member) => (
            <MemberCard
              key={member.member_info.MEMBER_ID}
              member={member}
              onClick={() => onMemberSelect(member)}
            />
          ))}
        </div>
      )}
    </div>
  );

  const renderMemberDetail = () => {
    if (!selectedMember) {
      return (
        <div className="bg-white rounded-lg shadow-md p-6">
          <EmptyState message="의원을 선택해주세요." />
        </div>
      );
    }

    const member = selectedMember;
    const billTypeData = [
      { name: '대표발의', value: member.bill_stats.lead_count, rate: member.bill_stats.lead_pass_rate },
      { name: '공동발의', value: member.bill_stats.co_count, rate: member.bill_stats.co_pass_rate },
    ];

    return (
      <div className="space-y-6">
        {/* 의원 정보 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center space-x-6">
            <div className="w-20 h-20 bg-gray-300 rounded-full flex items-center justify-center">
              <Users className="w-10 h-10 text-gray-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-gray-900">{member.member_info.NAAS_NM}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <p className="text-sm text-gray-600">소속정당</p>
                  <p className="font-medium">{member.member_info.PLPT_NM}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">선거구</p>
                  <p className="font-medium">{member.member_info.ELECD_DIV_NM}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">소속위원회</p>
                  <p className="font-medium">{member.member_info.CMIT_NM}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">생년월일</p>
                  <p className="font-medium">{member.member_info.BIRDY_DT}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 의안 통계 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            icon={FileText}
            title="총 의안 수"
            value={formatNumber(member.bill_stats.total_count)}
            subtitle={`가결률 ${formatPercent(member.bill_stats.total_pass_rate)}`}
            color="blue"
          />
          <StatCard
            icon={Award}
            title="대표발의"
            value={formatNumber(member.bill_stats.lead_count)}
            subtitle={`가결률 ${formatPercent(member.bill_stats.lead_pass_rate)}`}
            color="green"
          />
          <StatCard
            icon={Users}
            title="공동발의"
            value={formatNumber(member.bill_stats.co_count)}
            subtitle={`가결률 ${formatPercent(member.bill_stats.co_pass_rate)}`}
            color="purple"
          />
        </div>

        {/* 차트 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 발의 유형별 분포 */}
          <ChartContainer title="발의 유형별 분포">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={billTypeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>

          {/* 위원회별 활동 */}
          <ChartContainer title="위원회별 활동">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={member.committee_stats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="active_committee" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total_count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {!selectedMember ? renderMemberList() : renderMemberDetail()}
      {selectedMember && (
        <div className="flex justify-center">
          <button
            onClick={() => onMemberSelect(null as any)}
            className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            목록으로 돌아가기
          </button>
        </div>
      )}
    </div>
  );
};