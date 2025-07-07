// src/services/api.ts
const API_BASE_URL = 'http://0.0.0.0:8001'; // 백엔드 URL

// 타입 정의
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

export const apiService = {
  // 의원 목록 조회
  async getMembers(): Promise<MemberStatisticsResponse[]> {
    const response = await fetch(`${API_BASE_URL}/members?age=22`);
    const data = await response.json();
    return data.data;
  },

  // 의원 상세 정보
  async getMember(memberId: string): Promise<MemberStatisticsResponse> {
    const response = await fetch(`${API_BASE_URL}/members/${memberId}`);
    const data = await response.json();
    return data.data;
  },

  // 의안 통계
  async getBillStats(): Promise<BillStatisticsResponse[]> {
    const response = await fetch(`${API_BASE_URL}/bills/statistics`);
    const data = await response.json();
    return data.data;
  }
};