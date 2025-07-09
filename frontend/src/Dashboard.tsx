import React, { useState } from 'react';
import { Building, TrendingUp, Users, FileText } from 'lucide-react';
import { TabType, MemberStatisticsResponse } from './types';
import { LoadingSpinner, ErrorMessage } from './components/ui';
import { OverviewPage, MemberStatsPage, BillStatsPage } from './pages';
import { useMembers, useBillStats } from './hooks';
import { TABS } from './constants';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedMember, setSelectedMember] = useState<MemberStatisticsResponse | null>(null);
  const [selectedAge, setSelectedAge] = useState<string>('22'); // 기본값: 22대

  // 데이터 페칭
  const { members, loading: membersLoading, error: membersError } = useMembers(selectedAge);
  // const { billStats, loading: billsLoading, error: billsError } = useBillStats();

  const loading = membersLoading;
  const error = membersError;
  // const loading = membersLoading || billsLoading;
  // const error = membersError || billsError;

  // 의원 선택 핸들러
  const handleMemberSelect = (member: MemberStatisticsResponse) => {
    setSelectedMember(member);
    setActiveTab('member-stats');
  };

  // 연령대 변경 핸들러
  const handleAgeChange = (age: string) => {
    setSelectedAge(age);
    setSelectedMember(null); // 필터 변경 시 선택된 의원 초기화
  };

  // 탭 변경 핸들러
  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    if (tab !== 'member-stats') {
      setSelectedMember(null);
    }
  };

  // 로딩 상태
  if (loading) {
    return <LoadingSpinner message="데이터를 불러오는 중..." />;
  }

  // 에러 상태
  if (error) {
    return <ErrorMessage message={error} onRetry={() => window.location.reload()} />;
  }

  // 탭 아이콘 컴포넌트 매핑
  const getTabIcon = (iconName: string) => {
    switch (iconName) {
      case 'TrendingUp':
        return TrendingUp;
      case 'Users':
        return Users;
      case 'FileText':
        return FileText;
      default:
        return TrendingUp;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <Building className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">
                국회 의원 및 의안 통계 대시보드
              </h1>
            </div>
            <div className="text-sm text-gray-500">
              {selectedAge ? `${selectedAge}대 국회` : '전체 국회'}
            </div>
          </div>
        </div>
      </header>

      {/* 탭 네비게이션 */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {TABS.map((tab) => {
              const Icon = getTabIcon(tab.icon);
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id as TabType)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
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
        {activeTab === 'overview' && (
          <OverviewPage
            members={members}
            // bills={billStats}
            selectedAge={selectedAge}
            onAgeChange={handleAgeChange}
            onMemberSelect={handleMemberSelect}
          />
        )}
        
        {activeTab === 'member-stats' && (
          <MemberStatsPage
            members={members}
            selectedMember={selectedMember}
            onMemberSelect={setSelectedMember}
            selectedAge={selectedAge}
            onAgeChange={handleAgeChange}
          />
        )}
        
        {/* {activeTab === 'bill-stats' && (
          <BillStatsPage
            bills={billStats}
            members={members}
            selectedAge={selectedAge}
            onAgeChange={handleAgeChange}
          />
        )} */}
      </main>

      {/* 푸터 */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-gray-500">
            국회 의원 및 의안 통계 대시보드 - 데이터 기준: {selectedAge ? `${selectedAge}대 국회` : '전체 국회'}
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;