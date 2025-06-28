import json
from collections import Counter
from datetime import datetime

# Member 클래스의 모든 필드
member_fields = (
    "NAAS_CD",  # MEMBER_ID
    "NAAS_NM",
    "BIRDY_DT",
    "DTY_NM",
    "PLPT_NM",
    "ELECD_NM",
    "ELECD_DIV_NM",
    "CMIT_NM",
    "BLNG_CMIT_NM",
    "NTR_DIV",
    "NAAS_HP_URL",
    "BRF_HST",
    "NAAS_PIC",
)

# MemberHistory 클래스의 모든 필드
member_history_fields = (
    "AGE",
    "MEMBER_ID",
    "NAAS_NM",
    "DTY_NM",
    "ELECD_NM",
    "ELECD_DIV_NM",
    "PLPT_NM",
)

# Committee 클래스의 모든 필드
committee_fields = (
    "COMMITTEE_TYPE_CODE",
    "COMMITTEE_TYPE",
    "COMMITTEE_ID",
    "COMMITTEE_NAME",
    "LIMIT_CNT",
    "CURR_CNT",
    "POLY99_CNT",
    "POLY_CNT",
    "ORDER_NUM",
)

# CommitteeMember 클래스의 모든 필드
committee_member_fields = ("COMMITTEE_NAME", "MEMBER_ID", "JOB_RES_NM")


# Bill 클래스의 모든 필드
bill_fields = (
    "BILL_ID",
    "BILL_NO",
    "PROPOSER_KIND",
    "AGE",
    "BILL_NAME",
    "COMMITTEE_NAME",
    "PROPOSE_DT",
    "PROC_DT",
    "STATUS",
)

# BillDetail 클래스의 모든 필드
bill_detail_fields = (
    "BILL_ID",
    "PROC_DT",
    "DETAIL_LINK",
    "LAW_SUBMIT_DT",
    "LAW_PRESENT_DT",
    "LAW_PROC_DT",
    "LAW_PROC_RESULT_CD",
    "COMMITTEE_DT",
    "CMT_PRESENT_DT",
    "CMT_PROC_DT",
    "CMT_PROC_RESULT_CD",
    "PROC_RESULT",
)

# BillProposer 클래스의 모든 필드
bill_proposer_fields = ("BILL_ID", "PROPOSER_ID", "PROPOSER_TYPE")


with open("./data/raw/law_bill_all.json", "r") as f:
    all_bills = json.load(f)

with open("./data/raw/bills.json", "r") as f:
    bills = json.load(f)

with open("./data/raw/members.json", "r") as f:
    members = json.load(f)

with open("./data/raw/committees.json", "r") as f:
    committees = json.load(f)

with open("./data/raw/committee_members.json", "r") as f:
    committee_members = json.load(f)

with open("./data/raw/cur_members.json", "r") as f:
    cur_members = json.load(f)

########################################origin################
with open("./data/new/committee_members.json", "r") as f:
    oall_committee_members = json.load(f)

with open("./data/new/committees.json", "r") as f:
    oall_committees = json.load(f)

with open("./data/new/member_history.json", "r") as f:
    omember_history_list = json.load(f)

with open("./data/new/bills.json", "r") as f:
    oall_bills = json.load(f)

with open("./data/new/bill_details.json", "r") as f:
    obill_details = json.load(f)

with open("./data/new/member_bills.json", "r") as f:
    oproposer_bills = json.load(f)


datas = {
    "all_committee_members": len(oall_committee_members),
    "all_committees": len(oall_committees),
    "member_history_list": len(omember_history_list),
    "all_bills": len(oall_bills),
    "bill_details": len(obill_details),
    "proposer_bills": len(oproposer_bills),
}

for name, data in datas.items():
    print(f"{name}: {data} -- origin")


def convert_str_to_isoformat(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    return date_obj.isoformat()


# 국회의원
member_dict = {}
member_history_list = []
for raw_member in members:
    plpt = raw_member.get("PLPT_NM").split("/")
    elecd_div = raw_member.get("ELECD_DIV_NM").split("/")

    r_cnt = len(elecd_div)
    eraco = (
        raw_member.get("GTELT_ERACO").split(", ")
        if raw_member.get("GTELT_ERACO")
        else [None for _ in range(r_cnt)]
    )
    elecd = (
        raw_member.get("ELECD_NM").split("/")
        if raw_member.get("ELECD_NM")
        else [None for _ in range(r_cnt)]
    )

    eraco_counter = Counter(eraco)
    if 2 in eraco_counter.values():
        for i, v in enumerate(eraco):
            if eraco_counter[v] == 2:
                eraco = eraco[:i] + eraco[i + 1 :]
                plpt = plpt[:i] + plpt[i + 1 :]
                elecd = elecd[:i] + elecd[i + 1 :] if len(elecd) > r_cnt else elecd
                break

    if len(eraco) > 1:
        if r_cnt > len(elecd):
            idx = [
                i
                for i, div in enumerate(elecd_div)
                if div in ["비례대표", "전국구", "통일주체국민회의"]
            ]
            for i in idx:
                elecd.insert(i, None)

        for i in range(len(eraco)):
            age = eraco[i][1:-1] if eraco[i] not in ["제헌", None] else eraco[i]
            if age == "제헌":
                plpt.append(plpt[0])
            member_history_list.append(
                {
                    "AGE": age,
                    "MEMBER_ID": raw_member["NAAS_CD"],
                    "DTY_NM": raw_member["DTY_NM"],
                    "ELECD_DIV_NM": elecd_div[i],
                    "ELECD_NM": elecd[i],
                    "PLPT_NM": plpt[i],
                }
            )
            member_dict[(raw_member["NAAS_NM"], age)] = raw_member["NAAS_CD"]
    else:
        raw_member["AGE"] = (
            raw_member["GTELT_ERACO"][1:-1]
            if raw_member["GTELT_ERACO"] not in ["제헌", None]
            else raw_member["GTELT_ERACO"]
        )
        raw_member["MEMBER_ID"] = raw_member["NAAS_CD"]
        member_history_list.append({k: raw_member[k] for k in member_history_fields})
        if member_dict.get((raw_member["NAAS_NM"], raw_member["AGE"])):
            print(member_dict.get((raw_member["NAAS_NM"], raw_member["AGE"])))
            print(
                "new", raw_member["NAAS_NM"], raw_member["NAAS_CD"], raw_member["AGE"]
            )
        member_dict[(raw_member["NAAS_NM"], raw_member["AGE"])] = raw_member["NAAS_CD"]


new_members = []
for raw_member in cur_members:
    if raw_member["REELE_GBN_NM"] == "초선":
        if (raw_member["HG_NM"], "22") not in member_dict:
            new_members.append(((raw_member["HG_NM"], "22"), raw_member))
    else:
        for age in raw_member["UNITS"].split(", "):
            if (raw_member["HG_NM"], age[1:-1]) not in member_dict:
                new_members.append((raw_member["HG_NM"], age[1:-1]), raw_member)

for key, raw_member in new_members:
    member_dict[key] = raw_member["MONA_CD"]
    member_history_list.append(
        {
            "AGE": age[1:-1],
            "MEMBER_ID": raw_member["MONA_CD"],
            "NAAS_NM": raw_member["HG_NM"],
            "DTY_NM": raw_member["JOB_RES_NM"],
            "ELECD_DIV_NM": raw_member["ELECT_GBN_NM"],
            "ELECD_NM": raw_member["ORIG_NM"],
            "PLPT_NM": raw_member["POLY_NM"],
        }
    )

# 정부/위원회 의안
origin_bills = [bill["BILL_NO"] for bill in bills]
all = [bill for bill in all_bills if bill["PROPOSER_KIND"] != "의원"]

new_bills = []

for raw_bill in all:
    if raw_bill["BILL_NO"] not in origin_bills:
        convert = {
            "CURR_COMMITTEE_ID": "COMMITTEE_ID",
            "CURR_COMMITTEE": "COMMITTEE",
            "PROC_RESULT_CD": "PROC_RESULT",
            "LINK_URL": "DETAIL_LINK",
        }
        bill = {
            convert[k] if k in convert.keys() else k: v for k, v in raw_bill.items()
        }
        bill["PUBL_PROPOSER"] = None
        bill["MEMBER_LIST"] = None
        new_bills.append(bill)


# 의안
committee_dict = {}
for bill in bills:
    if bill["COMMITTEE"] is not None and bill["COMMITTEE"] not in committee_dict:
        committee_dict[bill["COMMITTEE"]] = bill["COMMITTEE_ID"]

print(f"정부, 위원장 의안 {len(new_bills)} 개")

bills.extend(new_bills)
proposer_bills = []
all_bills = []
bill_details = []

print(f"전체 의안 {len(bills)} 개")
for raw_bill in bills:
    # 의원별 의안
    bill_id = raw_bill["BILL_ID"]
    kind = raw_bill.get("PROPOSER_KIND", "의원")
    if kind == "위원장":
        proposer_bills.append(
            {
                "BILL_ID": bill_id,
                "PROPOSER_ID": raw_bill["COMMITTEE_ID"],
                "PROPOSER_TYPE": "위원장",
            }
        )
    elif kind == "정부":
        proposer_bills.append(
            {
                "BILL_ID": bill_id,
                "PROPOSER_ID": "0000",
                "PROPOSER_TYPE": "정부",
            }
        )
    elif kind == "의원":
        raw_bill["PROPOSER_KIND"] = kind
        if raw_bill["RST_PROPOSER"]:
            for member in raw_bill["RST_PROPOSER"].split(","):
                proposer_bills.append(
                    {
                        "BILL_ID": bill_id,
                        "PROPOSER_ID": member_dict.get((member, "22")),
                        "PROPOSER_TYPE": "의원대표",
                    }
                )
        if raw_bill["PUBL_PROPOSER"]:
            for member in raw_bill["PUBL_PROPOSER"].split(","):
                proposer_bills.append(
                    {
                        "BILL_ID": bill_id,
                        "PROPOSER_ID": member_dict.get((member, "22")),
                        "PROPOSER_TYPE": "의원공동",
                    }
                )

    raw_bill["STATUS"] = None
    raw_bill["COMMITTEE_NAME"] = raw_bill["COMMITTEE"]
    bill_details.append({k: raw_bill[k] for k in bill_detail_fields})
    bill = {k: raw_bill[k] for k in bill_fields}

    committee_name = raw_bill.get("COMMITTEE")
    if not committee_name:
        bill["STATUS"] = "소관위원회지정대기"
        all_bills.append(bill)
        continue

    if raw_bill["PROC_RESULT"]:
        bill["STATUS"] = raw_bill["PROC_RESULT"]
        all_bills.append(bill)
        continue

    status_map = {
        "COMMITTEE_DT": "소관위진행중",
        "CMT_PRESENT_DT": "소관위진행중",
        "CMT_PROC_DT": None,
        "LAW_SUBMIT_DT": "법사위진행중",
        "LAW_PRESENT_DT": "법사위진행중",
        "LAW_PROC_DT": None,
    }

    today = datetime.now().isoformat()
    process_dict = {
        k: raw_bill[k] for k in status_map.keys() if raw_bill[k] is not None
    }
    cnt = len(process_dict)

    if cnt == 1:
        bill["STATUS"] = "소관위진행중"
    elif cnt == 2:
        if today < convert_str_to_isoformat(raw_bill["CMT_PRESENT_DT"]):
            bill["STATUS"] = "소관위계류"
        else:
            bill["STATUS"] = "소관위진행중"
    elif cnt == 3:
        bill["STATUS"] = "법사위진행중"
    elif cnt == 4:
        bill["STATUS"] = "법사위진행중"
    elif cnt == 5:
        if today < convert_str_to_isoformat(raw_bill["LAW_PRESENT_DT"]):
            bill["STATUS"] = "법사위진행중"
        else:
            bill["STATUS"] = "법사위계류"
    else:
        bill["STATUS"] = "기타"
    all_bills.append(bill)


# 위원회
counter = Counter([com["COMMITTEE_NAME"] for com in committees])
dup_committee = [committee for committee in counter if counter["COMMITTEE_NAME"] != 1]

all_committees = []
committee_name = []
for raw_committee in committees:
    name = raw_committee.get("COMMITTEE_NAME")
    if name in committee_name:
        continue
    committee_name.append(name)
    raw_committee["COMMITTEE_ID"] = committee_dict.get(name)
    raw_committee["COMMITTEE_TYPE"] = raw_committee["CMT_DIV_NM"]
    raw_committee["COMMITTEE_TYPE_CODE"] = raw_committee["CMT_DIV_CD"]
    all_committees.append({k: raw_committee[k] for k in committee_fields})

# 위원회 구성원
all_committee_members = []
for raw_committee_member in committee_members:
    committee_name = raw_committee_member.get("DEPT_NM")
    committee_id = committee_dict.get(committee_name) or committee_dict.get(
        committee_name[:-2]
    )
    all_committee_members.append(
        {
            "COMMITTEE_NAME": committee_name,
            "MEMBER_ID": member_dict[(raw_committee_member.get("HG_NM"), "22")],
            "MEMBER_TYPE": raw_committee_member.get("JOB_RES_NM"),
        }
    )

datas = {
    "all_committee_members": all_committee_members,
    "all_committees": all_committees,
    "member_history_list": member_history_list,
    "all_bills": all_bills,
    "bill_details": bill_details,
    "proposer_bills": proposer_bills,
    "member_dict": member_dict,
}

for name, data in datas.items():
    print(f"{name}: {len(data)}")


with open("./data/new/committee_members.json", "w", encoding="utf-8") as f:
    json.dump(all_committee_members, f, indent=2)

with open("./data/new/committees.json", "w", encoding="utf-8") as f:
    json.dump(all_committees, f, indent=2)

with open("./data/new/member_history.json", "w", encoding="utf-8") as f:
    json.dump(member_history_list, f, indent=2)

with open("./data/new/bills.json", "w", encoding="utf-8") as f:
    json.dump(all_bills, f, indent=2)

with open("./data/new/bill_details.json", "w", encoding="utf-8") as f:
    json.dump(bill_details, f, indent=2)

with open("./data/new/proposer_bills.json", "w", encoding="utf-8") as f:
    json.dump(proposer_bills, f, indent=2)

str_member_dict = {str(k): v for k, v in member_dict.items()}
with open("./data/new/member_id.json", "w", encoding="utf-8") as f:
    json.dump(str_member_dict, f, ensure_ascii=False, indent=2)
