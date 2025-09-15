from .section import (
    FinanceSection,
    FinanceSectionParser,
    FinanceSectionProcessor,
    Section,
    SectionData,
    SectionParser,
    SubTaskNestedSectionParser,
    SubTaskSection,
    SubTaskSectionData,
)


class SectionManager:
    def __init__(self):
        self.section_queue = []
        self.section_factory = SectionFactory()

    def add(self, task, section_title, section_content):
        section = self.create_section(task, section_title, section_content)
        self.section_queue.add(section)

    def create_section(self, task, section_title, section_content):
        return self.section_factory.create(task, section_title, section_content)

    def parsing(self):
        while True:
            if section := self.section_queue.pop():
                section.parse()


class SectionFactory:
    def __init__(self):
        self.configs = {
            'finance': (FinanceSectionParser(), FinanceSectionProcessor, FinanceSection),
            'subtasks': (SubTaskNestedSectionParser(), SubTaskSection, SubTaskSectionData),
            'etc': (SectionParser(), Section, SectionData)
        }

    def create(self, task, section_title, section_content):
        parser, section_cls, data_cls = self.configs.get(section_title)
        return section_cls(task, parser, data_cls, section_content)
