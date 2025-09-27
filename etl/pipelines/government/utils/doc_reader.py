import os
from pathlib import Path


class GoalDocReader:
    BASE_DIR = Path("/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/성과관리계획_및_평가/성과관리시행계획/TXT")

    async def read(self, year, ministry):
        filename = Path(f"성과계획_{ministry}_{year}.txt")
        with open(self.BASE_DIR / filename, 'r') as f:
            return f.read()

    async def read_goal_ref():
        pass
        # with open(f'/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/교육부_전략_과제_{filepath}.json', 'r') as f:
        #     yearly_tasks = json.load(f)

        # goals = {}
        # for 전략목표 in yearly_tasks:
        #     전략목표번호 = 전략목표['전략목표'][0]
        #     for 성과목표, 관리과제 in 전략목표['성과목표'].items():
        #         성과목표번호 = f'{전략목표번호}-{성과목표[0]}'
        #         성과목표전체 = f'{전략목표번호}-{성과목표}'
        #         goals[성과목표번호] = [title for title in 관리과제['관리과제']]
    
    @staticmethod
    async def result():
        pathdir = Path('/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/tasks_data/')
        for fname in os.listdir(pathdir):
            with open(f"{pathdir}/{fname}", 'r') as f:
                data = f.read()
                print(fname, len(data))

    @classmethod
    def get_filepath(cls, year, ministry):
        return cls.BASE_DIR / Path(f"성과계획_{ministry}_{year}.txt")
