import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Users, FileText, TrendingUp, Award } from 'lucide-react';
import { MemberStatisticsResponse, BillStatisticsResponse, PartyStats, TopBill } from '../types';
import { StatCard, ChartContainer, MemberCard, FilterDropdown } from '../components/ui';
import { useOverallStats, usePartyStats, useTopBills } from '../hooks';
import { CHART_COLORS, AGE_OPTIONS } from '../constants';
import { formatNumber, formatPercent, chunkArray } from '../utils';

interface OverviewPageProps {
  members: MemberStatisticsResponse[];
  // bills: BillStatisticsResponse[];
  selectedAge: string;
  onAgeChange: (age: string) => void;
  onMemberSelect: (member: MemberStatisticsResponse) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  members,
  // bills,
  selectedAge,
  onAgeChange,
  onMemberSelect,
}) => {
  const overallStats = useOverallStats(members);
  const partyStats = usePartyStats(members);
  // const topBills = useTopBills(bills);

  // 차트 데이터 준비
  const partyDistributionData = partyStats.map(party => ({
    name: party.name,
    value: party.count,
  }));

  const partyPerformanceData = partyStats.map(party => ({
    name: party.name,
    avgBillCount: party.avgLeadBillCount,
    avgPassRate: party.avgLeadPassRate,
  }));

  return (
    <div className="space-y-6">
      {/* 필터 섹션 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-wrap gap-4">
          <FilterDropdown
            label="대수"
            value={selectedAge}
            options={AGE_OPTIONS}
            onChange={onAgeChange}
          />
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={Users}
          title="총 의원 수"
          value={formatNumber(overallStats.totalMembers)}
          subtitle="등록된 의원"
          color="blue"
        />
        <StatCard
          icon={FileText}
          title="총 의안 수"
          value={formatNumber(overallStats.totalLeadBills)}
          subtitle="발의된 의안"
          color="green"
        />
        <StatCard
          icon={TrendingUp}
          title="평균 대표 발의 수"
          value={formatNumber(overallStats.avgLeadBillCount)}
          subtitle="의원당 평균"
          color="purple"
        />
        <StatCard
          icon={Award}
          title="평균 통과율"
          value={formatPercent(overallStats.avgLeadPassRate)}
          subtitle="전체 평균"
          color="orange"
        />
      </div>

      {/* 차트 영역 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 정당별 의원 분포 */}
        <ChartContainer title="정당별 의원 분포">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={partyDistributionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} (${value})`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {partyDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* 정당별 평균 발의 수 & 통과율 */}
        <ChartContainer title="정당별 평균 발의 수 & 통과율">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={partyPerformanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="avgBillCount" fill="#8884d8" name="평균 발의 수" />
              <Bar yAxisId="right" dataKey="avgPassRate" fill="#82ca9d" name="평균 통과율(%)" />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* 정당별 상위 의원 2명씩 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">정당별 상위 의원 (대표 발의 건수 기준)</h3>
        <div className="space-y-6">
          {partyStats.map((party) => (
            <div key={party.name}>
              <h4 className="text-md font-medium text-gray-700 mb-3 flex items-center">
                <span className="inline-block w-3 h-3 rounded-full mr-2" 
                      style={{ backgroundColor: CHART_COLORS[partyStats.indexOf(party) % CHART_COLORS.length] }}></span>
                {party.name} ({party.count}명)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {party.topMembers.map((member) => (
                  <MemberCard
                    key={member.member_info.MEMBER_ID}
                    member={member}
                    onClick={() => onMemberSelect(member)}
                    isCompact={true}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 많이 발의된 의안 Top 3 */}
      {/* <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">많이 발의된 의안 Top 3</h3>
        <div className="space-y-4">
          {topBills.map((bill, index) => (
            <div key={index} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-800 text-sm font-medium">
                      {index + 1}
                    </span>
                    <h4 className="text-lg font-medium text-gray-900">{bill.bill_name}</h4>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{bill.bill_committee}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">발의 건수</p>
                  <p className="text-xl font-bold text-blue-600">{formatNumber(bill.bill_count)}</p>
                  <p className="text-sm text-green-600">통과율 {formatPercent(bill.bill_pass_rate)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div> */}
    </div>
  );
};