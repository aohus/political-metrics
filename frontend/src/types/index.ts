// API 관련 타입들
export interface MemberResponse {
  MEMBER_ID: string;
  NAAS_NM: string;
  BIRDY_DT?: string;
  PLPT_NM?: string;
  ELECD_DIV_NM?: string;
  CMIT_NM?: string;
  NAAS_PIC?: string;
}

export interface MemberBillStatistics {
  total_count: number;
  total_pass_rate: number;
  lead_count: number;
  lead_pass_rate: number;
  co_count: number;
  co_pass_rate: number;
}

export interface MemberCommitteeStatistics {
  active_committee: string;
  total_count: number;
  lead_count: number;
  co_count: number;
}

export interface MemberStatisticsResponse {
  member_info: MemberResponse;
  bill_stats: MemberBillStatistics;
  committee_stats: MemberCommitteeStatistics[];
}

export interface BillStatisticsResponse {
  bill_code: string;
  bill_name: string;
  bill_committee: string;
  bill_count: number;
  bill_pass_rate: number;
}

// 필터 관련 타입들
export interface FilterState {
  age?: string;
  party?: string;
  committee?: string;
  sortBy?: SortCriteria;
}

export type SortCriteria =  
    | 'name' 
    | 'total_count' 
    | 'total_pass_rate' 
    | 'lead_count' 
    | 'party' 
    | 'bill_name'
    | 'bill_count'
    | 'bill_pass_rate'
    | 'bill_committee'

export type TabType = 'overview' | 'member-stats' | 'bill-stats';

// 통계 관련 타입들
export interface OverallStats {
  totalMembers: number;
  totalLeadBills: number;
  avgLeadBillCount: number;
  avgLeadPassRate: number;
  totalBills: number;
}

export interface PartyStats {
  name: string;
  count: number;
  totalLeadBills: number;
  avgLeadBillCount: number;
  avgLeadPassRate: number;
  topMembers: MemberStatisticsResponse[];
}

export interface TopBill {
  bill_name: string;
  bill_committee: string;
  bill_count: number;
  bill_pass_rate: number;
}

// UI 컴포넌트 Props 타입들
export interface StatCardProps {
  icon: React.ElementType;
  title: string;
  value: React.ReactNode;
  subtitle?: string;
  color?: string;
}

export interface MemberCardProps {
  member: MemberStatisticsResponse;
  onClick: () => void;
  isCompact?: boolean;
}

export interface FilterDropdownProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}

export interface ChartContainerProps {
  title: string;
  children: React.ReactNode;
}

// 옵션 타입들
export interface SelectOption {
  value: string;
  label: string;
}