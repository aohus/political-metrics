// src/services/api.ts
const API_BASE_URL = 'http://localhost:8000/api'; // 백엔드 URL

export const apiService = {
  // 의원 목록 조회
  async getMembers(): Promise<MemberStatisticsResponse[]> {
    const response = await fetch(`${API_BASE_URL}/members`);
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