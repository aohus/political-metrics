import { MemberStatisticsResponse, BillStatisticsResponse } from '../types';
import { API_BASE_URL } from '../constants';

export const apiService = {
  // 의원 목록 조회 (age 파라미터 추가)
  async getMembers(age?: string): Promise<MemberStatisticsResponse[]> {
    const url = `${API_BASE_URL}/members?age=${age}&limit=300`
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.data || [];
  },

  // 의원 상세 정보
  async getMember(memberId: string): Promise<MemberStatisticsResponse> {
    const response = await fetch(`${API_BASE_URL}/members/${memberId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.data;
  },

  // 의안 통계 (필터 파라미터 추가)
  async getBillStats(filters?: {
    age?: string;
    committee?: string;
    sortBy?: string;
  }): Promise<BillStatisticsResponse[]> {
    const params = new URLSearchParams();
    
    if (filters?.age) params.append('age', filters.age);
    if (filters?.committee) params.append('committee', filters.committee);
    if (filters?.sortBy) params.append('sort_by', filters.sortBy);
    
    const url = `${API_BASE_URL}/ranking/bills${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.data || [];
  },

  // 정당 목록 조회
  async getParties(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/parties`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.data || [];
  },

  // 위원회 목록 조회
  async getCommittees(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/committees`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.data || [];
  }
};