# import json
# from collections import defaultdict

# root_dir = "/Users/aohus/Workspaces/github/politics/data/"
# with open(
#     "/Users/aohus/Workspaces/github/politics/data/assembly/raw/bills.json", "r"
# ) as f:
#     bills = json.load(f)

# bill_core = {}
# for bill in bills:
#     bill_core[bill["BILL_ID"]] = (
#         bill["BILL_NAME"],
#         bill["COMMITTEE"],
#         (True if bill["PROC_DT"] and bill["PROC_RESULT"] != "철회" else False),
#     )


# with open(
#     "/Users/aohus/Workspaces/github/politics/data/assembly/formatted/bill_proposer.json",
#     "r",
# ) as f:
#     proposer = json.load(f)


# statistics = {}  # defaultdict({"rst": list, "co": list})
# for info in proposer:
#     if info["MEMBER_ID"] not in statistics.keys():
#         statistics[info["MEMBER_ID"]] = {
#             "rst": {"count": 0, "pass": 0, "committee": {}, "name": {}},
#             "co": {"count": 0, "pass": 0, "committee": {}, "name": {}},
#         }
#     rst = "rst" if info["RST"] else "co"
#     name, committee, is_passed = bill_core[info["BILL_ID"]]

#     # statistics[info["MEMBER_ID"]][rst].append(bill_core[info["BILL_ID"]])
#     statistics[info["MEMBER_ID"]][rst]["count"] += 1
#     statistics[info["MEMBER_ID"]][rst]["pass"] += 1 if is_passed else 0
#     if committee in statistics[info["MEMBER_ID"]][rst]["committee"]:
#         statistics[info["MEMBER_ID"]][rst]["committee"][committee] += 1
#     else:
#         statistics[info["MEMBER_ID"]][rst]["committee"][committee] = 1

#     if name in statistics[info["MEMBER_ID"]][rst]["name"]:
#         statistics[info["MEMBER_ID"]][rst]["name"][name] += 1
#     else:
#         statistics[info["MEMBER_ID"]][rst]["name"][name] = 1

# with open(f"{root_dir}/assembly/formatted/stats.json", "w", encoding="utf-8") as f:
#     json.dump(statistics, f, ensure_ascii=False, indent=2)


# bill_stats = {
#     "proc_bill": {"name": defaultdict(int), "committee": defaultdict(int)},
#     "passed_bill": {"name": defaultdict(int), "committee": defaultdict(int)},
# }
# for name, committee, is_passed in bill_core.values():
#     bill_stats["proc_bill"]["name"][name] += 1
#     bill_stats["proc_bill"]["committee"][committee] += 1
#     bill_stats["passed_bill"]["name"][name] += 1 if is_passed else 0
#     bill_stats["passed_bill"]["committee"][committee] += 1 if is_passed else 0

# with open(
#     f"{root_dir}/assembly/formatted/stats_bills.json", "w", encoding="utf-8"
# ) as f:
#     json.dump(bill_stats, f, ensure_ascii=False, indent=2)
