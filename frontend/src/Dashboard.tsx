import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { Users, FileText, TrendingUp, Award, Calendar, Building } from 'lucide-react';

// 타입 정의
interface MemberResponse {
  MEMBER_ID: string;
  NAAS_NM: string;
  BIRDY_DT?: string;
  PLPT_NM?: string;
  ELECD_DIV_NM?: string;
  CMIT_NM?: string;
  NAAS_PIC?: string;
}

interface MemberBillStatistics {
  total_count: number;
  total_pass_rate: number;
  lead_count: number;
  lead_pass_rate: number;
  co_count: number;
  co_pass_rate: number;
}

interface MemberCommitteeStatistics {
  active_committee: string;
  total_count: number;
  lead_count: number;
  co_count: number;
}

interface MemberStatisticsResponse {
  member_info: MemberResponse;
  bill_stats: MemberBillStatistics;
  committee_stats: MemberCommitteeStatistics[];
}

interface BillStatisticsResponse {
  bill_code: string;
  bill_name: string;
  bill_committee: string;
  bill_count: number;
  bill_pass_rate: number;
}

// 샘플 데이터
const sampleMembers: MemberStatisticsResponse[] = [
  {
    member_info: {
      MEMBER_ID: "M001",
      NAAS_NM: "김철수",
      BIRDY_DT: "1965-03-15",
      PLPT_NM: "더불어민주당",
      ELECD_DIV_NM: "서울특별시 강남구 갑",
      CMIT_NM: "법제사법위원회"
    },
    bill_stats: {
      total_count: 45,
      total_pass_rate: 67.5,
      lead_count: 28,
      lead_pass_rate: 72.1,
      co_count: 17,
      co_pass_rate: 58.8
    },
    committee_stats: [
      { active_committee: "법제사법위원회", total_count: 32, lead_count: 20, co_count: 12 },
      { active_committee: "정무위원회", total_count: 13, lead_count: 8, co_count: 5 }
    ]
  },
  {
    member_info: {
      MEMBER_ID: "M002",
      NAAS_NM: "박영희",
      BIRDY_DT: "1972-08-22",
      PLPT_NM: "국민의힘",
      ELECD_DIV_NM: "부산광역시 해운대구",
      CMIT_NM: "기획재정위원회"
    },
    bill_stats: {
      total_count: 38,
      total_pass_rate: 71.2,
      lead_count: 22,
      lead_pass_rate: 77.3,
      co_count: 16,
      co_pass_rate: 62.5
    },
    committee_stats: [
      { active_committee: "기획재정위원회", total_count: 28, lead_count: 18, co_count: 10 },
      { active_committee: "산업통상자원중소벤처기업위원회", total_count: 10, lead_count: 4, co_count: 6 }
    ]
  },
  {
    member_info: {
      MEMBER_ID: "M003",
      NAAS_NM: "이민수",
      BIRDY_DT: "1968-12-03",
      PLPT_NM: "정의당",
      ELECD_DIV_NM: "경기도 성남시 분당구",
      CMIT_NM: "보건복지위원회"
    },
    bill_stats: {
      total_count: 52,
      total_pass_rate: 63.4,
      lead_count: 35,
      lead_pass_rate: 68.6,
      co_count: 17,
      co_pass_rate: 52.9
    },
    committee_stats: [
      { active_committee: "보건복지위원회", total_count: 40, lead_count: 28, co_count: 12 },
      { active_committee: "여성가족위원회", total_count: 12, lead_count: 7, co_count: 5 }
    ]
  }
];

const sampleBillStats: BillStatisticsResponse[] = [
  { bill_code: "B001", bill_name: "민법 일부개정법률안", bill_committee: "법제사법위원회", bill_count: 15, bill_pass_rate: 73.3 },
  { bill_code: "B002", bill_name: "소득세법 일부개정법률안", bill_committee: "기획재정위원회", bill_count: 22, bill_pass_rate: 68.2 },
  { bill_code: "B003", bill_name: "의료법 일부개정법률안", bill_committee: "보건복지위원회", bill_count: 18, bill_pass_rate: 77.8 },
  { bill_code: "B004", bill_name: "교육기본법 일부개정법률안", bill_committee: "교육위원회", bill_count: 12, bill_pass_rate: 58.3 },
  { bill_code: "B005", bill_name: "환경정책기본법 일부개정법률안", bill_committee: "환경노동위원회", bill_count: 20, bill_pass_rate: 65.0 }
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedMember, setSelectedMember] = useState<MemberStatisticsResponse | null>(null);

  // 통계 계산
  const overallStats = useMemo(() => {
    const totalMembers = sampleMembers.length;
    const totalBills = sampleMembers.reduce((sum, member) => sum + member.bill_stats.total_count, 0);
    const avgPassRate = sampleMembers.reduce((sum, member) => sum + member.bill_stats.total_pass_rate, 0) / totalMembers;
    const totalLeadBills = sampleMembers.reduce((sum, member) => sum + member.bill_stats.lead_count, 0);

    return {
      totalMembers,
      totalBills,
      avgPassRate: Math.round(avgPassRate * 10) / 10,
      totalLeadBills
    };
  }, []);

  // 정당별 통계
  const partyStats = useMemo(() => {
    const partyMap = new Map();
    sampleMembers.forEach(member => {
      const party = member.member_info.PLPT_NM || '무소속';
      if (!partyMap.has(party)) {
        partyMap.set(party, { name: party, count: 0, bills: 0, passRate: 0 });
      }
      const partyData = partyMap.get(party);
      partyData.count += 1;
      partyData.bills += member.bill_stats.total_count;
      partyData.passRate += member.bill_stats.total_pass_rate;
    });

    return Array.from(partyMap.values()).map(party => ({
      ...party,
      passRate: Math.round((party.passRate / party.count) * 10) / 10
    }));
  }, []);

  const StatCard = ({ icon: Icon, title, value, subtitle, color = "blue" }: any) => (
    <div className={`bg-white rounded-lg shadow-md p-6 border-l-4 border-${color}-500`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
        <Icon className={`h-8 w-8 text-${color}-500`} />
      </div>
    </div>
  );

  const MemberCard = ({ member, onClick }: { member: MemberStatisticsResponse, onClick: () => void }) => (
    <div 
      className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow border"
      onClick={onClick}
    >
      <div className="flex items-center space-x-4">
        <div className="w-12 h-12 bg-gray-300 rounded-full flex items-center justify-center">
          <Users className="w-6 h-6 text-gray-600" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{member.member_info.NAAS_NM}</h3>
          <p className="text-sm text-gray-600">{member.member_info.PLPT_NM}</p>
          <p className="text-sm text-gray-500">{member.member_info.ELECD_DIV_NM}</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-600">총 의안</p>
          <p className="text-xl font-bold text-blue-600">{member.bill_stats.total_count}</p>
          <p className="text-sm text-green-600">가결률 {member.bill_stats.total_pass_rate}%</p>
        </div>
      </div>
    </div>
  );

  const renderOverview = () => (
    <div className="space-y-6">
      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={Users}
          title="총 의원 수"
          value={overallStats.totalMembers}
          subtitle="등록된 의원"
          color="blue"
        />
        <StatCard
          icon={FileText}
          title="총 의안 수"
          value={overallStats.totalBills}
          subtitle="발의된 의안"
          color="green"
        />
        <StatCard
          icon={TrendingUp}
          title="평균 가결률"
          value={`${overallStats.avgPassRate}%`}
          subtitle="전체 평균"
          color="purple"
        />
        <StatCard
          icon={Award}
          title="대표발의"
          value={overallStats.totalLeadBills}
          subtitle="대표발의 건수"
          color="orange"
        />
      </div>

      {/* 차트 영역 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 정당별 의원 수 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">정당별 의원 분포</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={partyStats}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} (${value})`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {partyStats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 정당별 가결률 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">정당별 평균 가결률</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={partyStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="passRate" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 의원 목록 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">의원 목록</h3>
        <div className="space-y-4">
          {sampleMembers.map((member) => (
            <MemberCard 
              key={member.member_info.MEMBER_ID} 
              member={member} 
              onClick={() => {
                setSelectedMember(member);
                setActiveTab('member-detail');
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );

  const renderMemberDetail = () => {
    if (!selectedMember) return <div>의원을 선택해주세요.</div>;

    const member = selectedMember;
    const billTypeData = [
      { name: '대표발의', value: member.bill_stats.lead_count, rate: member.bill_stats.lead_pass_rate },
      { name: '공동발의', value: member.bill_stats.co_count, rate: member.bill_stats.co_pass_rate }
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
            value={member.bill_stats.total_count}
            subtitle={`가결률 ${member.bill_stats.total_pass_rate}%`}
            color="blue"
          />
          <StatCard
            icon={Award}
            title="대표발의"
            value={member.bill_stats.lead_count}
            subtitle={`가결률 ${member.bill_stats.lead_pass_rate}%`}
            color="green"
          />
          <StatCard
            icon={Users}
            title="공동발의"
            value={member.bill_stats.co_count}
            subtitle={`가결률 ${member.bill_stats.co_pass_rate}%`}
            color="purple"
          />
        </div>

        {/* 차트 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 발의 유형별 분포 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">발의 유형별 분포</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={billTypeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* 위원회별 활동 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">위원회별 활동</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={member.committee_stats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="active_committee" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total_count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  const renderBillStats = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">의안별 통계</h3>
        
        {/* 의안 통계 차트 */}
        <div className="mb-6">
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={sampleBillStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bill_name" angle={-45} textAnchor="end" height={100} />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="bill_count" fill="#8884d8" name="의안 수" />
              <Bar yAxisId="right" dataKey="bill_pass_rate" fill="#82ca9d" name="가결률(%)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 의안 목록 테이블 */}
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
                  의안 수
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  가결률
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sampleBillStats.map((bill) => (
                <tr key={bill.bill_code} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {bill.bill_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bill.bill_committee}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bill.bill_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      bill.bill_pass_rate >= 70 ? 'bg-green-100 text-green-800' :
                      bill.bill_pass_rate >= 60 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {bill.bill_pass_rate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <Building className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">국회 의원 및 의안 통계 대시보드</h1>
            </div>
          </div>
        </div>
      </header>

      {/* 탭 네비게이션 */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'overview', name: '전체 개요', icon: TrendingUp },
              { id: 'member-detail', name: '의원 상세', icon: Users },
              { id: 'bill-stats', name: '의안 통계', icon: FileText }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* 메인 콘텐츠 */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'member-detail' && renderMemberDetail()}
        {activeTab === 'bill-stats' && renderBillStats()}
      </main>
    </div>
  );
};

export default Dashboard;