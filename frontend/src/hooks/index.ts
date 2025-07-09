import { useState, useEffect, useMemo } from 'react';
import { 
  MemberStatisticsResponse, 
  BillStatisticsResponse, 
  FilterState, 
  OverallStats, 
  PartyStats, 
  TopBill 
} from '../types';
import { apiService } from '../services/api';

// 의원 데이터 페칭 훅
export const useMembers = (age?: string) => {
  const [members, setMembers] = useState<MemberStatisticsResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    apiService
      .getMembers(age)
      .then((data) => {
        if (mounted) {
          setMembers(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError('의원 데이터를 불러오지 못했습니다.');
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [age]);

  return { members, loading, error };
};

// 의안 통계 데이터 페칭 훅
export const useBillStats = () => {
  const [billStats, setBillStats] = useState<BillStatisticsResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    apiService
      .getBillStats()
      .then((data) => {
        if (mounted) {
          setBillStats(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError('의안 통계 데이터를 불러오지 못했습니다.');
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  return { billStats, loading, error };
};

// 필터링된 의원 목록 훅
export const useFilteredMembers = (members: MemberStatisticsResponse[], filter: FilterState) => {
  return useMemo(() => {
    let filtered = [...members];

    // 정당 필터링
    if (filter.party) {
      filtered = filtered.filter(member => 
        member.member_info.PLPT_NM?.includes(filter.party!)
      );
    }

    // 위원회 필터링
    if (filter.committee) {
      filtered = filtered.filter(member => 
        member.member_info.CMIT_NM?.includes(filter.committee!)
      );
    }

    // 정렬
    if (filter.sortBy) {
      filtered.sort((a, b) => {
        switch (filter.sortBy) {
          case 'name':
            return a.member_info.NAAS_NM.localeCompare(b.member_info.NAAS_NM);
          case 'total_count':
            return b.bill_stats.total_count - a.bill_stats.total_count;
          case 'total_pass_rate':
            return b.bill_stats.total_pass_rate - a.bill_stats.total_pass_rate;
          case 'lead_count':
            return b.bill_stats.lead_count - a.bill_stats.lead_count;
          case 'party':
            return (a.member_info.PLPT_NM || '').localeCompare(b.member_info.PLPT_NM || '');
          default:
            return 0;
        }
      });
    }

    return filtered;
  }, [members, filter]);
};

// 필터링된 의안 목록 훅
export const useFilteredBills = (bills: BillStatisticsResponse[], filter: FilterState) => {
  return useMemo(() => {
    let filtered = [...bills];

    // 위원회 필터링
    if (filter.committee) {
      filtered = filtered.filter(bill => 
        bill.bill_committee.includes(filter.committee!)
      );
    }

    // 정렬
    if (filter.sortBy) {
      filtered.sort((a, b) => {
        switch (filter.sortBy) {
          case 'bill_name':
            return a.bill_name.localeCompare(b.bill_name);
          case 'bill_count':
            return b.bill_count - a.bill_count;
          case 'bill_pass_rate':
            return b.bill_pass_rate - a.bill_pass_rate;
          case 'bill_committee':
            return a.bill_committee.localeCompare(b.bill_committee);
          default:
            return 0;
        }
      });
    }

    return filtered;
  }, [bills, filter]);
};

// 전체 통계 계산 훅
export const useOverallStats = (members: MemberStatisticsResponse[]): OverallStats => {
  return useMemo(() => {
    const totalMembers = members.length;
    const totalLeadBills = members.reduce((sum, member) => sum + member.bill_stats.lead_count, 0);
    const avgLeadBillCount = totalMembers === 0 ? 0 : Math.round((totalLeadBills / totalMembers) * 10) / 10;
    const avgLeadPassRate = totalMembers === 0 ? 0 : 
      Math.round((members.reduce((sum, member) => sum + member.bill_stats.lead_pass_rate, 0) / totalMembers) * 10) / 10;
    const totalBills = members.reduce((sum, member) => sum + member.bill_stats.total_count, 0);

    return {
      totalMembers,
      totalLeadBills,
      avgLeadBillCount,
      avgLeadPassRate,
      totalBills,
    };
  }, [members]);
};

// 정당별 통계 계산 훅
export const usePartyStats = (members: MemberStatisticsResponse[]): PartyStats[] => {
  return useMemo(() => {
    const partyMap = new Map<string, PartyStats>();

    members.forEach((member) => {
      const partyFull = member.member_info.PLPT_NM || '무소속';
      const party = partyFull.split('/').pop() || '무소속';

      if (!partyMap.has(party)) {
        partyMap.set(party, {
          name: party,
          count: 0,
          totalLeadBills: 0,
          avgLeadBillCount: 0,
          avgLeadPassRate: 0,
          topMembers: [],
        });
      }

      const partyData = partyMap.get(party)!;
      partyData.count += 1;
      partyData.totalLeadBills += member.bill_stats.lead_count;
      partyData.topMembers.push(member);
    });

    return Array.from(partyMap.values()).map((party) => ({
      ...party,
      avgLeadBillCount: Math.round((party.totalLeadBills / party.count) * 10) / 10,
      avgLeadPassRate: Math.round((party.topMembers.reduce((sum, member) => 
        sum + member.bill_stats.lead_pass_rate, 0) / party.count) * 10) / 10,
      topMembers: party.topMembers
        .sort((a, b) => b.bill_stats.lead_count - a.bill_stats.lead_count)
        .slice(0, 2),
    }));
  }, [members]);
};

// 많이 발의된 의안 Top 3 훅
export const useTopBills = (bills: BillStatisticsResponse[]): TopBill[] => {
  return useMemo(() => {
    return bills
      .sort((a, b) => b.bill_count - a.bill_count)
      .slice(0, 3)
      .map(bill => ({
        bill_name: bill.bill_name,
        bill_committee: bill.bill_committee,
        bill_count: bill.bill_count,
        bill_pass_rate: bill.bill_pass_rate,
      }));
  }, [bills]);
};

// 고유 옵션 추출 훅
export const useUniqueOptions = (members: MemberStatisticsResponse[]) => {
  return useMemo(() => {
    const parties = Array.from(
      new Set(
      members
        .map(member => member.member_info.PLPT_NM)
        .filter(Boolean)
        .flatMap(plpt => plpt!.split('/').map(p => p.trim()))
      )
    ).filter(Boolean).sort();

    const committees = Array.from(
      new Set(
      members
        .map(member => member.member_info.CMIT_NM)
        .filter(Boolean)
        .flatMap(cmit => cmit!.split('/').map(c => c.trim()))
      )
    ).filter(Boolean).sort();

    return {
      partyOptions: [
        { value: '', label: '전체' },
        ...parties.map(party => ({ value: party, label: party }))
      ],
      committeeOptions: [
        { value: '', label: '전체' },
        ...committees.map(committee => ({ value: committee, label: committee }))
      ]
    };
  }, [members]);
};
