import json


class TaskWriter:
    def save(self):
        basedir = '/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/부처별'
        filename = f"성과관리시행계획_{self.ministry}_{self.year}-{self.goal_num}"
        with open(f'{basedir}/{self.ministry}/tmp/{filename}.json', 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
        self.status = "Saved"